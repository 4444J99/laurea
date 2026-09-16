"""Health observations preserve generation and missing-evidence boundaries."""
import json
import pytest
from laurea.health import collect_health, Reader, Unmeasured

SHA = "a" * 40


def reader(*, steps=None, private=False, moved=False, denied=False):
    calls = []
    def read(path):
        calls.append(path)
        if path == "/repos/owner/repo":
            return {"id": 7, "full_name": "owner/repo", "private": private, "default_branch": "main"}
        if "/commits/" in path:
            return {"sha": "b" * 40 if moved and calls.count(path) > 1 else SHA}
        if "/actions/runs?" in path:
            return {"total_count": 1, "workflow_runs": [{"id": 1, "head_sha": SHA, "conclusion": "failure"}]}
        if "/jobs?" in path:
            return {"total_count": 1, "jobs": [{"head_sha": SHA, "steps": steps or []}]}
        if "/alerts?" in path:
            if denied:
                raise OSError("secret provider details")
            return []
        if "/pulls?" in path:
            return []
        raise AssertionError(path)
    return read, calls


def test_zero_step_failure_is_not_executed_code_failure():
    read, _ = reader()
    result = collect_health("owner/repo", "token", read=read)
    assert result["generation"] == "current"
    row = result["verification"]["runs_observed"][0]
    assert row["conclusion"] == "failure"
    assert row["execution"] == "no_executed_steps"
    assert result["verification"]["acceptance"] == "unmeasured"


def test_executed_steps_preserve_separate_acceptance():
    read, _ = reader(steps=[{"status": "completed", "conclusion": "failure"}])
    result = collect_health("owner/repo", "token", read=read)
    assert result["verification"]["runs_observed"][0]["execution"] == "executed"
    assert result["pr_readiness"]["readiness"] == "unmeasured"


def test_head_movement_invalidates_generation():
    read, _ = reader(moved=True)
    assert collect_health("owner/repo", "token", read=read)["generation"] == "not_current"


def test_denied_security_does_not_report_zero_alerts():
    read, _ = reader(denied=True)
    result = collect_health("owner/repo", "token", read=read)
    assert all(value == {"status": "unmeasured"} for value in result["security"].values())
    assert "secret provider" not in json.dumps(result)


def test_private_identity_is_excluded_before_other_reads():
    read, calls = reader(private=True)
    result = collect_health("owner/repo", "token", read=read)
    assert "owner/repo" not in json.dumps(result)
    assert len(calls) == 1


def test_truncated_runs_remain_unmeasured():
    base, _ = reader()
    def read(path):
        if "/actions/runs?" in path:
            return {"total_count": 101, "workflow_runs": []}
        return base(path)
    assert collect_health("owner/repo", "token", read=read)["verification"] == {"status": "unmeasured"}


def test_wrong_run_generation_cannot_be_used():
    base, _ = reader()
    def read(path):
        if "/actions/runs?" in path:
            return {"total_count": 1, "workflow_runs": [{"id": 1, "head_sha": "b" * 40}]}
        return base(path)
    assert collect_health("owner/repo", "token", read=read)["verification"] == {"status": "unmeasured"}


def test_budget_exhaustion_does_not_issue_network_request():
    with pytest.raises(Unmeasured):
        Reader("token", requests=0)("/repos/owner/repo")


@pytest.mark.parametrize("repo", ["../x/y", "owner/repo?token=secret", "owner"])  # allow-secret: runtime parameter or synthetic rejection fixture; no credential literal
def test_coordinate_rejected_before_network(repo):
    with pytest.raises(ValueError):
        collect_health(repo, "token")


def test_cli_unknown_health_returns_77_even_with_current_generation(monkeypatch, capsys):
    from laurea.cli import main
    monkeypatch.setattr("laurea.cli.resolve_token", lambda: "token")
    monkeypatch.setattr("laurea.cli.collect_health", lambda *args: {
        "status": "unmeasured", "generation": "current"})
    assert main(["health", "--repo", "owner/repo"]) == 77
    assert json.loads(capsys.readouterr().out)["generation"] == "current"


def test_failed_job_observation_keeps_verification_unmeasured():
    base, _ = reader()
    def read(path):
        if "/jobs?" in path:
            raise OSError("unavailable")
        return base(path)
    result = collect_health("owner/repo", "fixture", read=read)
    assert result["verification"]["status"] == "unmeasured"
    assert result["verification"]["runs_observed"][0]["execution"] == "unmeasured"


def test_malformed_steps_do_not_become_measured_zero_execution():
    read, _ = reader(steps=["malformed"])
    result = collect_health("owner/repo", "fixture", read=read)
    assert result["verification"]["status"] == "unmeasured"
    assert result["verification"]["runs_observed"][0]["execution"] == "unmeasured"
