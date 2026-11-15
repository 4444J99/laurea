"""Reject mismatched observation clocks and competing source-issue proposals."""
from copy import deepcopy
from datetime import datetime, timezone
import json

import pytest

from laurea.arena import materialize_entries, write_entry
from laurea import publish as p
from test_publish import sandbox


def row():
    """Build a synthetic Arena row with explicit activity counts and a verified date."""
    return dict(login="alice", contributions=1, prs=1, repos=1, languages=1,
                measured_axes=1, verified="2026-09-16")


@pytest.mark.parametrize("stamp", ["2027-09-16T00:00:00Z", "2026-09-15T23:59:59Z",
                                  "2026-09-17T00:00:00Z"])
def test_inconsistent_observation_date_cannot_create_an_entry(tmp_path, stamp):
    """Verify that inconsistent observation date cannot create an entry."""
    with pytest.raises(ValueError, match="UTC date"):
        write_entry(tmp_path / "entries", issue=4, row=row(), observed_at=stamp)
    assert not (tmp_path / "entries").exists()


@pytest.mark.parametrize("stamp", ["2026-09-17T01:00:00+02:00", "2026-09-15T23:00:00-02:00"])
def test_calendar_agreement_uses_utc_not_local_date(tmp_path, stamp):
    """Observation agreement is evaluated by UTC day rather than the timestamp's local calendar."""
    path = write_entry(tmp_path / "entries", issue=4, row=row(), observed_at=stamp)
    assert json.loads(path.read_text())["observed_at"] == stamp
    assert datetime.fromisoformat(stamp).astimezone(timezone.utc).date().isoformat() == row()["verified"]


def test_existing_bad_timestamp_cannot_poison_table(tmp_path):
    """Verify that existing bad timestamp cannot poison table."""
    entries = tmp_path / "entries"
    path = write_entry(entries, issue=4, row=row(), observed_at="2026-09-16T01:00:00Z")
    table = tmp_path / "table.md"
    materialize_entries(entries, table)
    before = table.read_bytes()
    payload = json.loads(path.read_text())
    payload["observed_at"] = "2099-09-16T01:00:00Z"
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="UTC date"):
        materialize_entries(entries, table)
    assert table.read_bytes() == before


def prepare(sandbox):
    """Write the test entrant observation into the isolated publication checkout."""
    root, _, env, _, _, _, _, _ = sandbox
    env["GITHUB_EVENT_NAME"] = "issues"
    write_entry(root / "arena/entries", issue=4, row=row(), observed_at="2026-09-16T01:00:00Z")


def existing_pr(sha, number=8):
    """Build a same-repository Arena proposal fixture at the supplied exact head."""
    return {"number": number, "state": "open",
            "head": {"ref": f"automation/arena/{number}-1", "sha": "a" * 40, "repo": {"id": 7}},
            "base": {"ref": "main", "sha": sha, "repo": {"id": 7}}}


def install_responses(sandbox, monkeypatch, *, target=4, failure=None):
    """Stub repository API responses while retaining the fixture's real local Git operations."""
    _, _, _, _, _, settings, _, sha = sandbox
    pr = existing_pr(sha)
    settings["pending"] = [pr]
    files = [{"filename": f"arena/entries/{target}.json", "status": "added"}]
    after = deepcopy(pr)
    if failure == "head_moved":
        after["head"]["sha"] = "b" * 40
    elif failure == "closed":
        after["state"] = "closed"
    elif failure == "foreign_repository":
        pr["head"]["repo"]["id"] = 9
    elif failure == "truncated_files":
        files *= 100
    elif failure == "malformed_files":
        files = [{}]
    elif failure == "foreign_change":
        files += [{"filename": "README.md", "status": "modified"}]
    elif failure == "replacement":
        files[0]["status"] = "modified"
    elif failure == "truncated_pulls":
        settings["pending"] = [pr] * 100
    real = p.command

    def command(argv, *, root, env):
        """Intercept provider calls and delegate the fixture's permitted local Git commands."""
        if argv[:2] == ["gh", "api"]:
            if argv[2] == "repos/owner/repo/pulls/8/files?per_page=100":
                return json.dumps(files)
            if argv[2] == "repos/owner/repo/pulls/8":
                return json.dumps(after)
        return real(argv, root=root, env=env)

    monkeypatch.setattr(p, "command", command)
    return pr


def test_rerun_retains_existing_source_issue_pr_without_push(sandbox, monkeypatch):
    """Verify that rerun retains existing source issue PR without push."""
    prepare(sandbox)
    root, remote, env, calls, _, _, git, sha = sandbox
    pr = install_responses(sandbox, monkeypatch)
    current = (root / "arena/entries/4.json").read_bytes()
    result = p.publish("arena", issue=4, root=root, env=env)
    assert result["status"] == "pending_predecessor"
    assert result["pr_url"] == "https://github.com/owner/repo/pull/8"
    assert result["head_sha"] == pr["head"]["sha"]
    assert result["branch"] == pr["head"]["ref"]
    assert (root / "arena/entries/4.json").read_bytes() == current
    assert git("rev-parse", "HEAD") == sha
    assert git("diff", "--cached", "--name-only") == ""
    assert git("rev-parse", "main", cwd=remote) == sha
    assert not any(call[:2] == ["git", "push"] or call[:3] == ["gh", "pr", "create"] for call in calls)


def test_other_issue_proposal_does_not_block_independent_entrant(sandbox, monkeypatch):
    """Verify that other issue proposal does not block independent entrant."""
    prepare(sandbox)
    root, _, env, _, _, _, _, _ = sandbox
    install_responses(sandbox, monkeypatch, target=5)
    assert p.publish("arena", issue=4, root=root, env=env)["status"] == "pr_open"


@pytest.mark.parametrize("failure", ["head_moved", "closed", "foreign_repository", "truncated_files",
                                     "malformed_files", "foreign_change", "replacement", "truncated_pulls"])
def test_unknown_or_foreign_owner_prevents_publication(sandbox, monkeypatch, failure):
    """Verify that unknown or foreign owner prevents publication."""
    prepare(sandbox)
    root, _, env, calls, _, _, git, sha = sandbox
    install_responses(sandbox, monkeypatch, failure=failure)
    with pytest.raises(ValueError):
        p.publish("arena", issue=4, root=root, env=env)
    assert git("rev-parse", "HEAD") == sha
    assert git("diff", "--cached", "--name-only") == ""
    assert not any(call[:2] == ["git", "push"] or call[:3] == ["gh", "pr", "create"] for call in calls)


def test_current_default_observation_cannot_be_replaced(sandbox):
    """Verify that current default observation cannot be replaced."""
    prepare(sandbox)
    root, remote, env, calls, _, settings, git, _ = sandbox
    git("add", "arena/entries/4.json")
    git("commit", "-m", "accepted immutable observation")
    accepted = git("rev-parse", "HEAD")
    git("push", "origin", "main")
    env["GITHUB_SHA"] = accepted
    settings["default_sha"] = accepted
    path = root / "arena/entries/4.json"
    payload = json.loads(path.read_text())
    payload["row"]["contributions"] = 99
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="already accepted"):
        p.publish("arena", issue=4, root=root, env=env)
    assert git("rev-parse", "main", cwd=remote) == accepted
    assert not any(call[:2] == ["git", "push"] or call[:3] == ["gh", "pr", "create"] for call in calls)
