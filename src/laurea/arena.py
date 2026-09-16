"""The arena — comparable snapshots under one bounded field definition."""

from __future__ import annotations

import re
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from .baselines import STATUS_MEASURED
from .models import Report
from .corpus import require_complete

_MARK_START = "<!-- arena:rows:start -->"
_MARK_END = "<!-- arena:rows:end -->"

HEADER = """# THE ARENA — GitHub activity snapshots

Every row below was computed from the GitHub API at the recorded time.
Rows are comparable only under the same field definitions and token visibility.
They are not rankings of engineering quality, authorship, or impact.

"""

TABLE_HEAD = (
    "| # | login | contribution events | PRs opened | visible repos | languages | measured axes | verified |\n"
    "|---|-------|--------------------:|-----------:|--------------:|----------:|--------------:|----------|\n"
)


def build_row(report: Report) -> dict:
    """Build one leaderboard row from a report without adding rank claims."""

    require_complete(report.snapshot)

    def value(axis: str) -> int:
        finding = report.by_axis(axis)
        return int(finding.value) if finding else 0

    try:
        verified = datetime.fromisoformat(report.generated_at)
        verified_date = verified.astimezone(UTC).date().isoformat()
    except ValueError:
        verified_date = report.generated_at.split()[0]

    return {
        "login": report.login,
        "contributions": value("contributions_year"),
        "prs": value("pull_requests_year"),
        "repos": value("repos_visible"),
        "languages": value("language_breadth"),
        "measured_axes": sum(
            finding.status == STATUS_MEASURED for finding in report.findings
        ),
        "verified": verified_date,
    }


def _parse_rows(text: str) -> list[dict]:
    # Version 0.1 stored an unsupported percentile label in column seven and
    # used different repository semantics. Those rows cannot be relabeled as
    # v0.2 measurements; the next arena run safely starts a new table.
    if "| best floor |" in text:
        return []
    rows = []
    match = re.search(f"{_MARK_START}\n(.*?){_MARK_END}", text, re.DOTALL)
    if not match:
        return rows
    for line in match.group(1).splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 8 and cells[0].isdigit() and cells[6].isdigit():
            rows.append(
                {
                    "login": cells[1].strip("`@"),
                    "contributions": int(cells[2].replace(",", "")),
                    "prs": int(cells[3].replace(",", "")),
                    "repos": int(cells[4].replace(",", "")),
                    "languages": int(cells[5].replace(",", "")),
                    "measured_axes": int(cells[6]),
                    "verified": cells[7],
                }
            )
    return rows


def update_leaderboard(path: Path, row: dict) -> str:
    """Replace one login's row, order by activity count, and write the table."""
    rows = _parse_rows(path.read_text()) if path.exists() else []
    rows = [
        candidate
        for candidate in rows
        if candidate["login"].lower() != row["login"].lower()
    ]
    rows.append(row)
    text = _render_rows(rows)
    path.write_text(text)
    return text


def _render_rows(rows: list[dict]) -> str:
    rows.sort(key=lambda candidate: -candidate["contributions"])
    body = "".join(
        f"| {index + 1} | `@{candidate['login']}` | {candidate['contributions']:,} "
        f"| {candidate['prs']:,} | {candidate['repos']:,} | {candidate['languages']:,} "
        f"| {candidate['measured_axes']} | {candidate['verified']} |\n"
        for index, candidate in enumerate(rows)
    )
    text = f"{HEADER}{_MARK_START}\n{TABLE_HEAD}{body}{_MARK_END}\n"
    return text


def _validate_row(row: dict) -> None:
    if not isinstance(row, dict):
        raise ValueError("invalid activity row")
    login = row.get("login")
    if not isinstance(login, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", login):
        raise ValueError("invalid entrant identity")
    fields = {"login", "contributions", "prs", "repos", "languages", "measured_axes", "verified"}
    if set(row) != fields or any(type(row[k]) is not int or row[k] < 0 for k in fields - {"login", "verified"}):
        raise ValueError("invalid activity row")
    datetime.strptime(row["verified"], "%Y-%m-%d")


def write_entry(directory: Path, *, issue: int, row: dict, observed_at: str) -> Path:
    """Preserve one issue observation without rewriting another entrant's file."""
    if type(issue) is not int or issue <= 0:
        raise ValueError("positive issue identity required")
    _validate_row(row)
    stamp = datetime.fromisoformat(observed_at)
    if stamp.tzinfo is None:
        raise ValueError("observation requires a timezone")
    record = {"schema_version": 1, "issue": issue, "observed_at": observed_at, "row": row}
    payload = json.dumps(record, sort_keys=True, indent=2) + "\n"
    directory.mkdir(parents=True, exist_ok=True)
    if directory.is_symlink():
        raise ValueError("entry directory must not be a symlink")
    target = directory / f"{issue}.json"
    if target.is_symlink():
        raise ValueError("entry must not be a symlink")
    fd, temporary = tempfile.mkstemp(prefix=".entry-", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError:
            if target.is_symlink() or target.read_text(encoding="utf-8") != payload:
                raise ValueError("issue observation already exists with different evidence") from None
    finally:
        Path(temporary).unlink(missing_ok=True)
    return target


def materialize_entries(directory: Path, leaderboard: Path, *, baseline: Path | None = None) -> str:
    """Render accepted records deterministically; validate all before writing."""
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("entry directory unavailable")
    paths = sorted(directory.iterdir())
    if (not paths and baseline is None) or len(paths) > 10000:
        raise ValueError("entry inventory empty or exceeds bound")
    inherited = {}
    if baseline is not None:
        if baseline.is_symlink() or not baseline.is_file() or baseline.stat().st_size > 1000000:
            raise ValueError("invalid baseline file")
        data = json.loads(baseline.read_text())
        if (not isinstance(data, dict) or set(data) != {"schema_version", "source", "rows"}
                or type(data["schema_version"]) is not int or data["schema_version"] != 1
                or not isinstance(data["rows"], list) or len(data["rows"]) > 1000):
            raise ValueError("invalid baseline schema")
        source = data["source"]
        if (not isinstance(source, dict) or set(source) != {"repository", "commit", "path", "sha256", "precision"}
                or source["repository"] != "organvm/laurea" or source["path"] != "LEADERBOARD.md"
                or source["precision"] != "date-only"
                or not isinstance(source["commit"], str) or not re.fullmatch(r"[0-9a-f]{40}", source["commit"])
                or not isinstance(source["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", source["sha256"])):
            raise ValueError("invalid baseline provenance")
        for row in data["rows"]:
            _validate_row(row)
            login = row["login"].lower()
            if login in inherited:
                raise ValueError("duplicate baseline login")
            inherited[login] = row
    records = []
    with tempfile.TemporaryDirectory() as scratch:
        validation = Path(scratch) / "validate"
        for path in paths:
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 10000:
                raise ValueError("invalid entry file")
            record = json.loads(path.read_text())
            if (not isinstance(record, dict) or set(record) != {"schema_version", "issue", "observed_at", "row"}
                    or type(record["schema_version"]) is not int or record["schema_version"] != 1
                    or path.name != str(record["issue"]) + ".json"):
                raise ValueError("invalid entry schema or filename")
            write_entry(validation, issue=record["issue"], row=record["row"], observed_at=record["observed_at"])
            records.append(record)
        # Newest observation wins for one login; issue ID resolves timestamp ties.
        records.sort(key=lambda r: (datetime.fromisoformat(r["observed_at"]), r["issue"]))
        latest = dict(inherited)
        for record in records:
            row = record["row"]
            login = row["login"].lower()
            # Baseline has only a date. Never invent a timestamp or let an older
            # observation replace it; same-day precise observations supersede it.
            if login not in latest or row["verified"] >= latest[login]["verified"]:
                latest[login] = row
        text = _render_rows([latest[login] for login in sorted(latest)])
    if leaderboard.is_symlink():
        raise ValueError("leaderboard must not be a symlink")
    leaderboard.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".leaderboard-", dir=leaderboard.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, leaderboard)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return text


def check_materialized_entries(directory: Path, leaderboard: Path, *, baseline: Path | None = None) -> None:
    """Reject a stale table without modifying any caller-owned output."""
    if leaderboard.is_symlink() or not leaderboard.is_file() or leaderboard.stat().st_size > 10000000:
        raise ValueError("bounded regular leaderboard required")
    with tempfile.TemporaryDirectory() as scratch:
        expected = materialize_entries(directory, Path(scratch) / "expected.md", baseline=baseline)
    if leaderboard.read_bytes() != expected.encode("utf-8"):
        raise ValueError("leaderboard is stale relative to accepted records")
