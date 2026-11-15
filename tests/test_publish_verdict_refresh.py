"""A refreshed metrics proposal must stage a card derived from its full history."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from laurea.publish import merge_pending_metrics_history, refresh_pending_branch
from laurea.verdict import deltas, load_history, verdict_card


HISTORY = "assets/verdict.jsonl"
CARD = "assets/cards/verdict.svg"


def git(root: Path, *args: str) -> str:
    """Run a checked Git command against an isolated local fixture repository and return its stdout."""
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True,
        timeout=10,
    ).stdout.rstrip("\n")


def initialize(root: Path) -> None:
    """Initialize and configure an isolated Git repository for metrics-history tests."""
    root.mkdir()
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "Regression fixture")
    git(root, "config", "user.email", "fixture@example.invalid")


def write_metrics(root: Path, rows: list[dict]) -> None:
    """Write deterministic metrics, dated history, and a matching verdict-card fixture."""
    history, card = root / HISTORY, root / CARD
    card.parent.mkdir(parents=True, exist_ok=True)
    history.write_text("".join(json.dumps(row) + "\n" for row in rows))
    card.write_text(verdict_card(rows))


def fixture(tmp_path: Path, previous: list[dict], current: list[dict]):
    """Create a local repository with predecessor and current metrics histories for refresh tests."""
    root = tmp_path / "repo"
    initialize(root)
    write_metrics(root, previous)
    git(root, "add", "assets")
    git(root, "commit", "-m", "previous observation")
    predecessor = git(root, "rev-parse", "HEAD")
    write_metrics(root, current)

    def run(*args):
        """Execute real local Git operations for the isolated metrics-history fixture."""
        assert args[0] == "git"
        return git(root, *args[1:])

    return root, predecessor, run


@pytest.mark.parametrize(
    "previous,current,key,expected_delta",
    [
        ([{"date": "2026-09-17", "followers": 4}],
         [{"date": "2026-09-18", "followers": 7}], "followers", (7, 3)),
        ([{"date": "2026-09-18", "unique_visitors_14d": 12}],
         [{"date": "2026-09-17", "unique_visitors_14d": 2},
          {"date": "2026-09-19", "followers": 7}],
         "unique_visitors_14d", (12, 10)),
        ([{"date": "2026-09-17", "followers": 1},
          {"date": "2026-09-18", "followers": 999}],
         [{"date": "2026-09-18", "followers": 7}], "followers", (7, 6)),
    ],
)
def test_merged_history_and_card_agree(tmp_path, previous, current, key, expected_delta):
    """Verify that merged history and card agree."""
    root, predecessor, run = fixture(tmp_path, previous, current)
    before = (root / CARD).read_text()
    merge_pending_metrics_history(run, root=root, predecessor=predecessor)
    history = load_history(root / HISTORY)
    rendered = (root / CARD).read_text()
    assert rendered != before
    assert rendered == verdict_card(history)
    assert deltas(history, key) == expected_delta
    assert f"tracking since {history[0]['date']}" in rendered
    assert ET.fromstring(rendered).tag.endswith("svg")
    first_bytes = ((root / HISTORY).read_bytes(), (root / CARD).read_bytes())
    merge_pending_metrics_history(run, root=root, predecessor=predecessor)
    assert first_bytes == ((root / HISTORY).read_bytes(), (root / CARD).read_bytes())


def test_no_predecessor_history_leaves_current_outputs_untouched(tmp_path):
    """Without a predecessor history blob, refreshing must leave current outputs byte-identical."""
    root = tmp_path / "repo"
    initialize(root)
    git(root, "commit", "--allow-empty", "-m", "no earlier history")
    predecessor = git(root, "rev-parse", "HEAD")
    write_metrics(root, [{"date": "2026-09-18", "followers": 7}])
    before = ((root / HISTORY).read_bytes(), (root / CARD).read_bytes())
    merge_pending_metrics_history(
        lambda *args: git(root, *args[1:]), root=root, predecessor=predecessor,
    )
    assert before == ((root / HISTORY).read_bytes(), (root / CARD).read_bytes())


def test_unrenderable_predecessor_does_not_replace_current_outputs(tmp_path):
    """Verify that unrenderable predecessor does not replace current outputs."""
    root, predecessor, run = fixture(
        tmp_path, [{"date": "2026-09-17", "followers": 4}],
        [{"date": "2026-09-18", "followers": 7}],
    )
    before = ((root / HISTORY).read_bytes(), (root / CARD).read_bytes())

    def malformed(*args):
        """Return malformed predecessor evidence for the history-refresh negative control."""
        if args[:2] == ("git", "show"):
            return json.dumps({"date": "2026-09-17", "followers": "invalid"})
        return run(*args)

    with pytest.raises((TypeError, ValueError)):
        merge_pending_metrics_history(malformed, root=root, predecessor=predecessor)
    assert before == ((root / HISTORY).read_bytes(), (root / CARD).read_bytes())


@pytest.mark.parametrize("relative", ["assets", "assets/cards", HISTORY, CARD])
def test_symlinked_output_is_rejected_without_writing_through_it(tmp_path, relative):
    """Verify that symlinked output is rejected without writing through it."""
    root, predecessor, run = fixture(
        tmp_path, [{"date": "2026-09-17", "followers": 4}],
        [{"date": "2026-09-18", "followers": 7}],
    )
    path = root / relative
    target = tmp_path / "external"
    path.rename(target)
    path.symlink_to(target, target_is_directory=target.is_dir())
    before = {str(p): p.read_bytes() for p in tmp_path.rglob("*")
              if p.is_file() and ".git" not in p.parts}
    with pytest.raises(ValueError, match="symlink"):
        merge_pending_metrics_history(run, root=root, predecessor=predecessor)
    assert before == {str(p): p.read_bytes() for p in tmp_path.rglob("*")
                      if p.is_file() and ".git" not in p.parts}


def test_refresh_stages_matching_card_and_preserves_both_parents(tmp_path):
    """Verify that refresh stages matching card and preserves both parents."""
    root = tmp_path / "repo"
    initialize(root)
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "--bare", str(remote))
    git(root, "remote", "add", "origin", str(remote))
    (root / "README.md").write_text("accepted source\n")
    git(root, "add", "README.md")
    git(root, "commit", "-m", "accepted source")
    base = git(root, "rev-parse", "HEAD")
    git(root, "push", "origin", "main")
    branch = "automation/metrics/1-1"
    git(root, "switch", "-c", branch)
    previous = [{"date": "2026-09-17", "followers": 4}]
    write_metrics(root, previous)
    git(root, "add", "assets")
    git(root, "commit", "-m", "pending observation")
    predecessor = git(root, "rev-parse", "HEAD")
    git(root, "push", "origin", branch)
    git(root, "switch", "main")
    current = [{"date": "2026-09-18", "followers": 7}]
    write_metrics(root, current)
    receipt = {}
    head = refresh_pending_branch(
        lambda *args: git(root, *args[1:]),
        {"branch": branch, "head_sha": predecessor}, base, receipt,
        kind="metrics", root=root,
    )
    assert git(root, "rev-parse", "HEAD") == base
    assert git(root, "ls-remote", "origin", "refs/heads/main").split()[0] == base
    assert git(root, "show", "-s", "--format=%P", head).split() == [predecessor, base]
    assert git(root, "ls-remote", "origin", "refs/heads/" + branch).split()[0] == head
    history = [json.loads(line) for line in git(root, "show", head + ":" + HISTORY).splitlines()]
    assert history == previous + current
    assert git(root, "show", head + ":" + CARD) + "\n" == verdict_card(history)
    assert set(git(root, "diff", "--name-only", base, head).splitlines()) == {HISTORY, CARD}
    assert receipt["predecessor_sha"] == predecessor
