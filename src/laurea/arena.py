"""The arena — laurels you can challenge.

Anyone opens an issue titled ``arena: <login>``; CI recomputes that
login's laurels against the live public API (no self-reporting, no
trust) and writes a verified row into LEADERBOARD.md. Same rules for
every entrant: public estate only, same floors, same citations.
"""

from __future__ import annotations

import re
from pathlib import Path

from .models import Report

_MARK_START = "<!-- arena:rows:start -->"
_MARK_END = "<!-- arena:rows:end -->"

HEADER = """# THE ARENA — verified laurels

Every row below was computed by CI from the live GitHub API at the
moment of entry — nobody reports their own numbers. Enter by opening an
issue titled `arena: your-login`. Same floors, same citations, same
public-estate rules for everyone (see [METHODOLOGY.md](METHODOLOGY.md)).

"""

TABLE_HEAD = (
    "| # | login | contributions/yr | PRs/yr | repos | languages | best floor | verified |\n"
    "|---|-------|-----------------:|-------:|------:|----------:|------------|----------|\n"
)


def build_row(report: Report) -> dict:
    def val(axis: str) -> int:
        f = report.by_axis(axis)
        return int(f.value) if f else 0

    best = min(
        (f.tier for f in report.findings if f.tier.startswith("top")),
        key=lambda t: float(t.split()[1].rstrip("%")),
        default="notable",
    )
    return {
        "login": report.login,
        "contributions": val("contributions_year"),
        "prs": val("pull_requests_year"),
        "repos": val("repos_owned"),
        "languages": val("language_breadth"),
        "best": best,
        "verified": report.generated_at.split()[0],
    }


def _parse_rows(text: str) -> list[dict]:
    rows = []
    m = re.search(f"{_MARK_START}\n(.*?){_MARK_END}", text, re.S)
    if not m:
        return rows
    for line in m.group(1).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 8 and cells[0].isdigit():
            rows.append({
                "login": cells[1].strip("`@"),
                "contributions": int(cells[2].replace(",", "")),
                "prs": int(cells[3].replace(",", "")),
                "repos": int(cells[4].replace(",", "")),
                "languages": int(cells[5].replace(",", "")),
                "best": cells[6],
                "verified": cells[7],
            })
    return rows


def update_leaderboard(path: Path, row: dict) -> str:
    rows = _parse_rows(path.read_text()) if path.exists() else []
    rows = [r for r in rows if r["login"].lower() != row["login"].lower()] + [row]
    rows.sort(key=lambda r: -r["contributions"])
    body = "".join(
        f"| {i + 1} | `@{r['login']}` | {r['contributions']:,} | {r['prs']:,} "
        f"| {r['repos']:,} | {r['languages']:,} | {r['best']} | {r['verified']} |\n"
        for i, r in enumerate(rows)
    )
    text = f"{HEADER}{_MARK_START}\n{TABLE_HEAD}{body}{_MARK_END}\n"
    path.write_text(text)
    return text
