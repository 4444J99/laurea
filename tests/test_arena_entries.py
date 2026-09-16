import json
from concurrent.futures import ThreadPoolExecutor
import pytest
from laurea.arena import write_entry

STAMP = "2026-09-16T07:00:00+00:00"
def row(login):
    return dict(login=login, contributions=1, prs=2, repos=3, languages=1, measured_axes=4, verified="2026-09-16")

def test_concurrent_entrants_preserve_both_observations(tmp_path):
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(write_entry, tmp_path, issue=i, row=row(login), observed_at=STAMP)
                   for i, login in [(1, "alice"), (2, "bob")]]
        paths = [f.result() for f in futures]
    assert {json.loads(p.read_text())["row"]["login"] for p in paths} == {"alice", "bob"}
    assert sorted(p.name for p in tmp_path.iterdir()) == ["1.json", "2.json"]

def test_replay_is_idempotent_but_changed_evidence_cannot_overwrite(tmp_path):
    path = write_entry(tmp_path, issue=1, row=row("alice"), observed_at=STAMP)
    original = path.read_bytes()
    assert write_entry(tmp_path, issue=1, row=row("alice"), observed_at=STAMP) == path
    with pytest.raises(ValueError):
        write_entry(tmp_path, issue=1, row=row("bob"), observed_at=STAMP)
    assert path.read_bytes() == original

@pytest.mark.parametrize("issue,login", [(0,"alice"),(True,"alice"),(1,"../outside"),(1,"")])
def test_invalid_identity_cannot_create_entry(tmp_path, issue, login):
    with pytest.raises(ValueError):
        write_entry(tmp_path, issue=issue, row=row(login), observed_at=STAMP)
    assert not list(tmp_path.iterdir())

def test_symlink_destination_is_rejected(tmp_path):
    outside = tmp_path / "outside"
    outside.write_text("preserve")
    (tmp_path / "1.json").symlink_to(outside)
    with pytest.raises(ValueError):
        write_entry(tmp_path, issue=1, row=row("alice"), observed_at=STAMP)
    assert outside.read_text() == "preserve"
