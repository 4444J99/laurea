"""Arena: verified rows, idempotent entries, contribution-ranked."""

from __future__ import annotations

from laurea.arena import build_row, update_leaderboard
from laurea.detectors import run_all
from laurea.models import Report


def _report(login="tester", contributions=26_000):
    snapshot = {
        "login": login, "name": login, "created_at": "2016-12-27T17:24:06Z",
        "followers": 1, "orgs": [],
        "repos": [{"name": "r", "isFork": False, "isArchived": False,
                   "stargazerCount": 0, "pushedAt": None,
                   "primaryLanguage": {"name": "Python"}}],
        "contributions": {"total": contributions, "commits": 1, "pull_requests": 1,
                          "reviews": 0, "issues": 0, "restricted": 0},
    }
    return Report(login=login, generated_at="2026-07-05 00:00 UTC",
                  snapshot=snapshot, findings=run_all(snapshot))


def test_row_carries_best_floor_and_date():
    row = build_row(_report())
    assert row["best"] == "top 0.1%" and row["verified"] == "2026-07-05"
    assert row["contributions"] == 26_000


def test_leaderboard_ranks_and_deduplicates(tmp_path):
    lb = tmp_path / "LEADERBOARD.md"
    update_leaderboard(lb, build_row(_report("alice", 100)))
    update_leaderboard(lb, build_row(_report("bob", 9_000)))
    text = update_leaderboard(lb, build_row(_report("alice", 200)))
    assert text.index("bob") < text.index("alice")
    assert text.count("@alice") == 1
    assert "| 1 | `@bob` |" in text
