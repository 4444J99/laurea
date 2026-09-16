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


def test_cli_issue_mode_preserves_existing_table(tmp_path, monkeypatch):
    from laurea import cli
    monkeypatch.setattr(cli, "resolve_token", lambda: "fixture")
    monkeypatch.setattr(cli, "collect", lambda *a: {})
    monkeypatch.setattr(cli, "run_all", lambda *a: [])
    monkeypatch.setattr(cli, "build_row", lambda report: row(report.login))
    table = tmp_path / "LEADERBOARD.md"
    table.write_text("existing table")
    entries = tmp_path / "entries"
    assert cli.main(["arena", "--login", "alice", "--issue", "12", "--entries", str(entries), "--leaderboard", str(table)]) == 0
    assert table.read_text() == "existing table"
    assert json.loads((entries / "12.json").read_text())["row"]["login"] == "alice"


def test_cli_rejects_invalid_issue_before_collection(monkeypatch):
    from laurea import cli
    monkeypatch.setattr(cli, "collect", lambda *a: pytest.fail("must not collect"))
    with pytest.raises(SystemExit):
        cli.main(["arena", "--login", "alice", "--issue", "0"])


def test_materialization_preserves_entrants_and_selects_latest_observation(tmp_path):
    from laurea.arena import materialize_entries
    entries = tmp_path / "entries"
    write_entry(entries, issue=2, row=row("bob"), observed_at=STAMP)
    write_entry(entries, issue=1, row=row("alice"), observed_at=STAMP)
    newer = row("alice"); newer["contributions"] = 9
    write_entry(entries, issue=3, row=newer, observed_at="2026-09-17T00:00:00Z")
    table = tmp_path / "table.md"
    text = materialize_entries(entries, table)
    assert text.count("@alice") == text.count("@bob") == 1
    assert "`@alice` | 9" in text
    assert materialize_entries(entries, table) == text


def test_malformed_record_preserves_previous_table(tmp_path):
    from laurea.arena import materialize_entries
    entries = tmp_path / "entries"
    write_entry(entries, issue=1, row=row("alice"), observed_at=STAMP)
    (entries / "2.json").write_text("{}")
    table = tmp_path / "table.md"; table.write_text("preserve")
    with pytest.raises(ValueError):
        materialize_entries(entries, table)
    assert table.read_text() == "preserve"
