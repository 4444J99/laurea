"""Arena reruns retain their exact owner and never replace accepted records.

Git operations use isolated local repositories. GitHub API responses are explicit
fixtures, so these tests do not claim hosted execution or production publication.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess

import pytest

from laurea import publish as p
from laurea.arena import write_entry


ENTRY = "arena/entries/4.json"
LIST = "/pulls?state=open&base=main&per_page=100"


def proposal(number=9, *, head="a" * 40, base="b" * 40):
    """Return one same-repository, immutable-generation proposal fixture."""
    return {
        "number": number, "state": "open",
        "head": {"ref": f"automation/arena/{number}-1", "sha": head, "repo": {"id": 7}},
        "base": {"ref": "main", "sha": base, "repo": {"id": 7}},
    }


def inventory_api(pulls, *, files=None, after=None):
    """Serve only the three reads used by the bounded ownership inventory."""
    calls = []
    files = [{"filename": ENTRY, "status": "added"}] if files is None else files

    def api(path):
        calls.append(path)
        if path == LIST:
            return deepcopy(pulls)
        if path.endswith("/files?per_page=100"):
            return deepcopy(files)
        for pr in pulls if isinstance(pulls, list) else []:
            if isinstance(pr, dict) and path == f"/pulls/{pr.get('number')}":
                return deepcopy(pr if after is None else after)
        raise AssertionError(f"Unexpected API request: {path}")
    return api, calls


def owners(api):
    """Invoke production ownership discovery for the one source issue."""
    return p.pending_arena_proposals(
        api, repository="owner/repo", repository_id=7, default="main", entry_path=ENTRY,
    )


def test_existing_owner_is_bound_to_repo_head_base_and_exact_added_path():
    pr = proposal()
    api, calls = inventory_api([pr])
    assert owners(api) == [{
        "pr_url": "https://github.com/owner/repo/pull/9",
        "head_sha": pr["head"]["sha"], "branch": pr["head"]["ref"],
    }]
    assert calls == [LIST, "/pulls/9/files?per_page=100", "/pulls/9"]


def test_other_issue_is_independent_only_after_generation_readback():
    api, calls = inventory_api([proposal()], files=[{"filename": "arena/entries/5.json", "status": "added"}])
    assert owners(api) == []
    assert calls[-1] == "/pulls/9"


@pytest.mark.parametrize("inventory", [None, {}, [None], [proposal()] * 100])
def test_incomplete_or_malformed_inventory_fails_closed(inventory):
    api, _ = inventory_api(inventory)
    with pytest.raises(ValueError):
        owners(api)


@pytest.mark.parametrize("field,value", [
    (("number",), True), (("number",), 0), (("state",), "closed"),
    (("head", "ref"), "automation/arena/0-1"),
    (("head", "sha"), "short"), (("base", "sha"), None),
    (("head", "repo", "id"), True), (("head", "repo", "id"), 8),
    (("base", "repo", "id"), 8), (("base", "ref"), "other"),
])
def test_untrusted_proposal_identity_fails_closed(field, value):
    pr = proposal()
    target = pr
    for key in field[:-1]:
        target = target[key]
    target[field[-1]] = value
    api, _ = inventory_api([pr])
    with pytest.raises(ValueError):
        owners(api)


@pytest.mark.parametrize("files", [
    {}, [None], [{"filename": "", "status": "added"}],
    [{"filename": ENTRY, "status": "added"}] * 100,
    [{"filename": ENTRY, "status": "added"}] * 2,
    [{"filename": ENTRY, "status": "modified"}],
    [{"filename": "elsewhere.json", "previous_filename": ENTRY, "status": "renamed"}],
    [{"filename": ENTRY, "status": "added"}, {"filename": "unrelated.py", "status": "added"}],
])
def test_incomplete_replacing_or_mixed_file_inventory_fails_closed(files):
    api, _ = inventory_api([proposal()], files=files)
    with pytest.raises(ValueError):
        owners(api)


@pytest.mark.parametrize("mutation", ["head", "base", "closed"])
@pytest.mark.parametrize("filename", [ENTRY, "arena/entries/5.json"])
def test_generation_movement_rejects_even_other_issue_decisions(mutation, filename):
    pr, after = proposal(), proposal()
    if mutation == "closed":
        after["state"] = "closed"
    else:
        after[mutation]["sha"] = "c" * 40
    api, _ = inventory_api([pr], files=[{"filename": filename, "status": "added"}], after=after)
    with pytest.raises(ValueError):
        owners(api)


def test_duplicate_pr_identity_is_not_counted_as_multiple_owners():
    api, _ = inventory_api([proposal(), proposal()])
    with pytest.raises(ValueError, match="duplicate"):
        owners(api)


def test_api_failure_is_not_an_empty_ownership_inventory():
    def denied(path):
        raise RuntimeError("source unavailable")
    with pytest.raises(RuntimeError, match="unavailable"):
        owners(denied)


@pytest.fixture
def arena_checkout(tmp_path, monkeypatch):
    """Use real Git refs and explicit mocked provider reads in an isolated repo."""
    root, remote = tmp_path / "work", tmp_path / "remote.git"
    root.mkdir()

    def git(*args, cwd=root):
        return subprocess.run(
            ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, timeout=10,
        ).stdout.strip()

    git("init", "--bare", str(remote))
    git("init", "-b", "main")
    git("config", "user.name", "fixture")
    git("config", "user.email", "fixture@example.invalid")
    (root / "README.md").write_text("fixture\n")
    git("add", "README.md")
    git("commit", "-m", "fixture")
    source = git("rev-parse", "HEAD")
    git("remote", "add", "origin", str(remote))
    git("push", "origin", "HEAD:refs/heads/main")
    event = tmp_path / "event.json"
    event.write_text(json.dumps({"action": "opened", "issue": {"number": 4},
                                 "repository": {"full_name": "owner/repo", "id": 7}}))
    env = {**os.environ, "GITHUB_ACTIONS": "true", "GITHUB_WORKSPACE": str(root),
           "GITHUB_REPOSITORY": "owner/repo", "GITHUB_SHA": source,
           "GITHUB_RUN_ID": "12", "GITHUB_RUN_ATTEMPT": "2",
           "GITHUB_EVENT_NAME": "issues", "GITHUB_EVENT_PATH": str(event)}
    settings = {"default": source, "pulls": [], "created": False, "default_reads": 0}
    calls, real = [], p.command

    def command(argv, *, root, env):
        calls.append(argv)
        if argv == ["git", "remote", "get-url", "origin"]:
            return "https://github.com/owner/repo"
        if argv[0] != "gh":
            return real(argv, root=root, env=env)
        if argv[:3] == ["gh", "pr", "create"]:
            settings["created"] = True
            return "https://github.com/owner/repo/pull/99"
        assert argv[:2] == ["gh", "api"]
        path = argv[2].removeprefix("repos/owner/repo")
        if path == "":
            value = {"id": 7, "full_name": "owner/repo", "default_branch": "main"}
        elif path == "/commits/main":
            settings["default_reads"] += 1
            value = {"sha": settings.get("moved_default", settings["default"])
                     if settings["default_reads"] > 1 else settings["default"]}
        elif path.startswith("/compare/"):
            value = {"status": "identical" if settings["default"] == source else "ahead"}
        elif path == "/issues/4":
            value = {"number": 4, "state": "open"}
        elif path == LIST:
            value = settings["pulls"]
        elif path.startswith("/pulls?state=open&head="):
            value = [proposal(99, head=git("rev-parse", "HEAD"), base=settings["default"])]
            value[0]["head"]["ref"] = git("branch", "--show-current")
            if not settings["created"]:
                value = []
        else:
            for pr in settings["pulls"]:
                if path == f"/pulls/{pr['number']}/files?per_page=100":
                    value = [{"filename": settings.get("pending_path", ENTRY), "status": "added"}]
                    break
                if path == f"/pulls/{pr['number']}":
                    value = pr
                    break
            else:
                raise AssertionError(f"Unexpected API request: {path}")
        return json.dumps(value)

    monkeypatch.setattr(p, "command", command)
    write_entry(root / "arena/entries", issue=4,
                row=dict(login="alice", contributions=1, prs=1, repos=1,
                         languages=1, measured_axes=1, verified="2026-09-20"),
                observed_at="2026-09-20T00:00:00+00:00")
    return root, remote, env, settings, calls, git, source


def assert_no_publication(calls):
    """No preparation mutation, push, PR creation or issue closure was attempted."""
    assert not any(call[:2] in (["git", "add"], ["git", "switch"], ["git", "push"])
                   or call[:3] in (["gh", "pr", "create"], ["gh", "issue", "close"])
                   for call in calls)


def test_rerun_keeps_existing_pr_branch_default_and_caller_bytes(arena_checkout):
    root, remote, env, settings, calls, git, source = arena_checkout
    previous = (root / ENTRY).read_bytes()
    git("add", ENTRY)
    git("commit", "-m", "existing observation proposal")
    owner = proposal(head=git("rev-parse", "HEAD"), base=source)
    git("push", "origin", f"HEAD:refs/heads/{owner['head']['ref']}")
    git("switch", "-c", "rerun-checkout", source)
    (root / ENTRY).parent.mkdir(parents=True, exist_ok=True)
    (root / ENTRY).write_bytes(previous.replace(b"00:00:00", b"01:00:00"))
    settings["pulls"] = [owner]
    before = (root / ENTRY).read_bytes()
    result = p.publish("arena", issue=4, root=root, env=env)
    assert result["status"] == "pending_predecessor"
    assert result["pr_url"] == "https://github.com/owner/repo/pull/9"
    assert result["branch"] == owner["head"]["ref"]
    assert result["head_sha"] == owner["head"]["sha"]
    assert git("rev-parse", "refs/heads/main", cwd=remote) == source
    assert git("rev-parse", "refs/heads/" + result["branch"], cwd=remote) == owner["head"]["sha"]
    assert git("show", owner["head"]["sha"] + ":" + ENTRY).encode() + b"\n" == previous
    assert git("branch", "--show-current") == "rerun-checkout"
    assert git("diff", "--cached", "--name-only") == ""
    assert (root / ENTRY).read_bytes() == before
    assert_no_publication(calls)


def test_multiple_prior_owners_stay_in_receipt_without_new_publication(arena_checkout):
    root, remote, env, settings, calls, git, source = arena_checkout
    settings["pulls"] = [proposal(9, head=source, base=source), proposal(10, head=source, base=source)]
    receipt = {}
    with pytest.raises(ValueError, match="multiple arena proposals"):
        p.publish("arena", issue=4, root=root, env=env, receipt=receipt)
    assert receipt["status"] == "pending_predecessor"
    assert len(receipt["pending"]) == 2
    assert git("rev-parse", "refs/heads/main", cwd=remote) == source
    assert_no_publication(calls)


def test_stale_rerun_cannot_replace_record_already_on_current_default(arena_checkout):
    root, remote, env, settings, calls, git, source = arena_checkout
    original = (root / ENTRY).read_bytes()
    git("add", ENTRY)
    git("commit", "-m", "accepted immutable observation")
    accepted = git("rev-parse", "HEAD")
    git("push", "origin", "HEAD:refs/heads/main")
    git("switch", "--detach", source)
    (root / ENTRY).parent.mkdir(parents=True, exist_ok=True)
    (root / ENTRY).write_bytes(original.replace(b"00:00:00", b"01:00:00"))
    candidate = (root / ENTRY).read_bytes()
    settings["default"] = accepted
    with pytest.raises(ValueError, match="already accepted"):
        p.publish("arena", issue=4, root=root, env=env)
    assert git("rev-parse", "refs/heads/main", cwd=remote) == accepted
    assert git("show", accepted + ":" + ENTRY).encode() + b"\n" == original
    assert (root / ENTRY).read_bytes() == candidate
    assert_no_publication(calls)


def test_default_movement_during_inventory_stops_before_publication(arena_checkout):
    root, remote, env, settings, calls, git, source = arena_checkout
    settings["moved_default"] = "c" * 40
    with pytest.raises(ValueError, match="default moved"):
        p.publish("arena", issue=4, root=root, env=env)
    assert git("rev-parse", "refs/heads/main", cwd=remote) == source
    assert_no_publication(calls)


def test_other_issue_proposal_does_not_block_a_new_independent_record(arena_checkout):
    root, remote, env, settings, calls, git, source = arena_checkout
    settings["pulls"] = [proposal(head=source, base=source)]
    settings["pending_path"] = "arena/entries/5.json"
    result = p.publish("arena", issue=4, root=root, env=env)
    assert result["status"] == "pr_open"
    assert result["branch"] == "automation/arena/12-2"
    assert git("rev-parse", "refs/heads/main", cwd=remote) == source
    assert git("rev-parse", "refs/heads/" + result["branch"], cwd=remote) == result["head_sha"]
    assert git("diff", "--name-only", source, result["head_sha"]) == ENTRY
    assert sum(call[:3] == ["gh", "pr", "create"] for call in calls) == 1
    assert not any("--force" in call or call[:3] == ["gh", "issue", "close"] for call in calls)
