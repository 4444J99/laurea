"""Tests for the quality-signal detector class (laurea #1).

The three detectors report exact fractions over the active corpus
(non-fork, non-archived repositories) from identity-free quality
aggregates collected alongside the snapshot. They never emit a
percentile, grade, or rank, and reliability/judgment stays NOT_MEASURED.
"""

from __future__ import annotations

import base64
import json

import pytest

from laurea.baselines import STATUS_MEASURED
from laurea.corpus import aggregate_quality, validate_quality
from laurea.detectors import run_all
from laurea.github import _probe_repo_quality, _tree_quality_signals, collect
from laurea.models import Report
from laurea.render import NOT_MEASURED, render_all


def _quality(active, **counts):
    quality = {"active_repositories": active, "test_presence": 0, "ci_green": 0,
               "ci_no_ci": 0, "ci_pending": 0, "docs_substantive_readme": 0,
               "docs_dir": 0}
    quality.update(counts)
    return quality


def _snapshot(**overrides):
    base = {
        "login": "tester",
        "name": "Tester",
        "created_at": "2016-12-27T17:24:06Z",
        "followers": 38,
        "orgs": [],
        "repos": [],
        "contributions": {
            "total": 100, "commits": 50, "pull_requests": 5,
            "reviews": 1, "issues": 2, "restricted": 0,
        },
        "coverage": {"status": "complete", "organization_scope_complete": True,
                     "failed_sources": 0, "private_repositories_excluded": 0},
        "repository_aggregates": {
            "scope": "token_visible", "nonfork_repositories": 4, "stars": 0,
            "primary_languages": {},
            "quality": _quality(4, test_presence=3, ci_green=2, ci_no_ci=1,
                                ci_pending=1, docs_substantive_readme=3, docs_dir=2),
        },
    }
    base.update(overrides)
    return base


def _quality_findings(snapshot=None):
    findings = run_all(snapshot or _snapshot())
    return {finding.axis: finding for finding in findings
            if finding.axis in ("test_presence", "ci_health", "docs_density")}


def test_quality_detectors_report_exact_fractions():
    findings = _quality_findings()
    assert set(findings) == {"test_presence", "ci_health", "docs_density"}
    assert findings["test_presence"].value == pytest.approx(3 / 4)
    assert findings["ci_health"].value == pytest.approx(2 / 4)
    assert findings["docs_density"].value == pytest.approx(3 / 4)
    for finding in findings.values():
        assert finding.status == STATUS_MEASURED
        assert finding.unit == "fraction"
    assert "3 of 4" in findings["test_presence"].evidence
    assert "2 of 4" in findings["ci_health"].evidence
    assert "1 have no CI at all" in findings["ci_health"].evidence
    assert "1 have runs but no completed verdict yet" in findings["ci_health"].evidence
    assert "3 of 4" in findings["docs_density"].evidence
    assert "1024 bytes" in findings["docs_density"].evidence
    assert "2 have a docs/ directory" in findings["docs_density"].evidence


def test_quality_detectors_state_what_the_signal_does_not_prove():
    findings = _quality_findings()
    assert "not evidence tests pass" in findings["test_presence"].analysis
    assert "not evidence of correctness" in findings["ci_health"].analysis
    assert "not evidence the docs are accurate" in findings["docs_density"].analysis


def test_quality_findings_emit_no_percentile_grade_or_rank():
    findings = _quality_findings()
    assert len(findings) == 3
    for finding in findings.values():
        assert finding.status in (STATUS_MEASURED, "derived")
        text = " ".join((finding.title, finding.evidence, finding.source, finding.analysis)).lower()
        assert "percentile" not in text
        assert "top" not in text
        assert "grade" not in text
        assert "rank" not in text


def test_quality_counts_exceeding_the_denominator_fail_closed():
    snapshot = _snapshot()
    snapshot["repository_aggregates"]["quality"] = _quality(
        4, test_presence=5, ci_green=2, ci_no_ci=1, docs_substantive_readme=3)
    with pytest.raises(ValueError, match="exceed"):
        run_all(snapshot)


def test_negative_quality_counts_fail_closed():
    snapshot = _snapshot()
    snapshot["repository_aggregates"]["quality"] = _quality(
        4, test_presence=-1, ci_green=2, ci_no_ci=1, docs_substantive_readme=3)
    with pytest.raises(ValueError, match="quality aggregate"):
        run_all(snapshot)


def test_missing_quality_aggregates_fail_closed():
    snapshot = _snapshot()
    del snapshot["repository_aggregates"]["quality"]
    with pytest.raises(ValueError, match="missing quality aggregates"):
        run_all(snapshot)


def test_malformed_quality_shape_fails_closed():
    with pytest.raises(ValueError, match="quality aggregate"):
        validate_quality({"active_repositories": 2, "test_presence": 1})
    with pytest.raises(ValueError, match="quality aggregate"):
        validate_quality(_quality(2, test_presence=1, ci_green="1"))


def test_empty_active_corpus_reports_no_quality_finding():
    snapshot = _snapshot()
    snapshot["repository_aggregates"]["quality"] = _quality(0)
    findings = run_all(snapshot)
    assert not [f for f in findings if f.axis in ("test_presence", "ci_health", "docs_density")]
    assert len(findings) == 7


def test_legacy_snapshot_without_coverage_keeps_seven_findings():
    snapshot = _snapshot()
    del snapshot["coverage"]
    del snapshot["repository_aggregates"]
    findings = run_all(snapshot)
    assert len(findings) == 7
    assert not [f for f in findings if f.axis in ("test_presence", "ci_health", "docs_density")]


def test_aggregate_quality_counts_signals_without_identities():
    signals = [
        {"test_signal": True, "ci": "green", "substantive_readme": True, "docs_dir": True},
        {"test_signal": True, "ci": "none", "substantive_readme": False, "docs_dir": False},
        {"test_signal": False, "ci": "pending", "substantive_readme": True, "docs_dir": False},
        {"test_signal": False, "ci": "failing", "substantive_readme": False, "docs_dir": True},
    ]
    quality = aggregate_quality(signals)
    assert quality == {"active_repositories": 4, "test_presence": 2, "ci_green": 1,
                       "ci_no_ci": 1, "ci_pending": 1, "docs_substantive_readme": 2,
                       "docs_dir": 2}
    assert "tester" not in json.dumps(quality)
    with pytest.raises(ValueError, match="quality signal"):
        aggregate_quality([{"test_signal": "yes", "ci": "green",
                            "substantive_readme": True, "docs_dir": False}])


def test_tree_signals_read_the_stated_definition():
    entries = [
        {"path": "README.md", "type": "blob", "size": 1023},
        {"path": "src/main.py", "type": "blob", "size": 10},
        {"path": "src/util_test.py", "type": "blob", "size": 10},
        {"path": "docs/guide.md", "type": "blob", "size": 10},
        {"path": ".github/workflows/ci.yml", "type": "blob", "size": 10},
    ]
    signals = _tree_quality_signals(entries)
    assert signals["test_signal"] is True  # *_test.py
    assert signals["substantive_readme"] is False  # 1023 bytes is below the floor
    assert signals["docs_dir"] is True
    assert signals["workflow_paths"] == [".github/workflows/ci.yml"]

    entries[0]["size"] = 1024
    signals = _tree_quality_signals(entries)
    assert signals["substantive_readme"] is True

    entries = [{"path": "pyproject.toml", "type": "blob", "size": 50}]
    signals = _tree_quality_signals(entries)
    assert signals["has_pyproject"] is True
    assert signals["test_signal"] is False


def test_truncated_tree_fails_the_probe_not_the_fraction(monkeypatch):
    def rest_get(path, token):
        return {"tree": [], "truncated": True}

    with pytest.raises(RuntimeError, match="truncated"):
        _probe_repo_quality("tester", "demo", "main", "abc", "token", rest_get=rest_get)


def _rest_stub(entries, check_runs, files=None):
    files = files or {}

    def rest_get(path, token):
        if "git/trees" in path:
            return {"tree": entries, "truncated": False}
        if "check-runs" in path:
            return {"check_runs": check_runs}
        if "commits" in path and path.endswith("/status"):
            return {"state": "success", "statuses": [{"state": "success"}]}
        if "/contents/" in path:
            name = path.split("/contents/")[1].split("?")[0]
            text = files.get(name, "")
            return {"encoding": "base64",
                    "content": base64.b64encode(text.encode()).decode()}
        raise AssertionError(f"unexpected REST path {path}")

    return rest_get


def test_probe_reads_tree_ci_and_content_signals():
    entries = [
        {"path": "README.md", "type": "blob", "size": 2048},
        {"path": "tests/test_demo.py", "type": "blob", "size": 10},
        {"path": "docs/guide.md", "type": "blob", "size": 10},
        {"path": ".github/workflows/ci.yml", "type": "blob", "size": 10},
    ]
    rest_get = _rest_stub(
        entries,
        [{"status": "completed", "conclusion": "success"}],
        {".github/workflows/ci.yml": "jobs:\n  test:\n    steps:\n      - run: pytest -q\n"},
    )
    signal = _probe_repo_quality("tester", "demo", "main", "abc", "token", rest_get=rest_get)
    assert signal == {"test_signal": True, "ci": "green",
                      "substantive_readme": True, "docs_dir": True}


def test_probe_pyproject_pytest_and_workflow_test_step_are_signals():
    entries = [{"path": "pyproject.toml", "type": "blob", "size": 50}]
    rest_get = _rest_stub(
        entries, [],
        {"pyproject.toml": "[tool.pytest]\ntestpaths = ['tests']\n"},
    )
    signal = _probe_repo_quality("tester", "demo", "main", "abc", "token", rest_get=rest_get)
    assert signal["test_signal"] is True
    assert signal["ci"] == "green"  # no check runs, commit status success


def test_probe_ci_verdicts():
    entries = []

    def probe(check_runs, statuses=None):
        rest_get = _rest_stub(entries, check_runs)
        if statuses is not None:
            def with_status(path, token, _orig=rest_get):
                if path.endswith("/status"):
                    return {"state": statuses[0], "statuses": [{"state": statuses[0]}] * statuses[1]}
                return _orig(path, token)
            rest_get = with_status
        return _probe_repo_quality("tester", "demo", "main", "abc", "token", rest_get=rest_get)["ci"]

    assert probe([{"status": "completed", "conclusion": "failure"}]) == "failing"
    assert probe([{"status": "completed", "conclusion": "success"},
                  {"status": "completed", "conclusion": "skipped"}]) == "green"
    assert probe([{"status": "completed", "conclusion": "skipped"}]) == "pending"
    assert probe([{"status": "in_progress", "conclusion": None}]) == "pending"
    assert probe([], ("success", 1)) == "green"
    assert probe([], ("failure", 1)) == "failing"
    assert probe([], ("success", 0)) == "none"


def _gql_stub(monkeypatch, repos):
    user = {"login": "tester", "name": "Tester", "createdAt": "2020-01-01T00:00:00Z",
            "followers": {"totalCount": 0}, "contributionsCollection": {
                "contributionCalendar": {"totalContributions": 0},
                "totalCommitContributions": 0, "totalPullRequestContributions": 0,
                "totalPullRequestReviewContributions": 0,
                "totalIssueContributions": 0, "restrictedContributionsCount": 0}}

    def connection(nodes, total=None):
        return {"nodes": nodes, "totalCount": len(nodes) if total is None else total,
                "pageInfo": {"hasNextPage": False, "endCursor": None}}

    def gql(query, variables, token):
        if "node(id:" in query:
            return {"node": {"id": variables["id"], "isPrivate": False}}
        if "contributionsCollection" in query:
            return {"user": user}
        if "organizations(first" in query:
            return {"user": {"organizations": connection([])}}
        return {"user": {"repositories": connection(repos)}}

    monkeypatch.setattr("laurea.github._gql", gql)


def _public_repo(**overrides):
    repo = {"id": "demo-id", "nameWithOwner": "tester/demo", "isPrivate": False,
            "isFork": False, "isArchived": False, "stargazerCount": 0,
            "defaultBranchRef": {"name": "main", "target": {"oid": "abc"}},
            "name": "demo", "primaryLanguage": None, "pushedAt": None}
    repo.update(overrides)
    return repo


def test_collect_attaches_quality_and_refuses_on_probe_failure(monkeypatch):
    _gql_stub(monkeypatch, [_public_repo()])
    monkeypatch.setattr("laurea.github._rest_get",
                        lambda path, token: (_ for _ in ()).throw(OSError("rest down")))
    snapshot = collect("tester", "token")
    assert snapshot["coverage"]["failed_sources"] == 1
    assert snapshot["coverage"]["status"] == "unmeasured"
    assert "quality" not in snapshot["repository_aggregates"]
    with pytest.raises(ValueError, match="coverage"):
        run_all(snapshot)


def test_collect_measures_quality_from_live_probes(monkeypatch):
    _gql_stub(monkeypatch, [_public_repo()])
    entries = [
        {"path": "README.md", "type": "blob", "size": 2048},
        {"path": "tests/test_demo.py", "type": "blob", "size": 10},
    ]
    monkeypatch.setattr("laurea.github._rest_get",
                        _rest_stub(entries, [{"status": "completed", "conclusion": "success"}]))
    snapshot = collect("tester", "token")
    assert snapshot["coverage"]["status"] == "complete"
    assert snapshot["coverage"]["failed_sources"] == 0
    quality = snapshot["repository_aggregates"]["quality"]
    assert quality == {"active_repositories": 1, "test_presence": 1, "ci_green": 1,
                       "ci_no_ci": 0, "ci_pending": 0, "docs_substantive_readme": 1,
                       "docs_dir": 0}
    findings = run_all(snapshot)
    assert next(f for f in findings if f.axis == "test_presence").value == 1.0
    assert next(f for f in findings if f.axis == "ci_health").value == 1.0
    assert next(f for f in findings if f.axis == "docs_density").value == 1.0


def test_collect_skips_empty_repositories_without_failing(monkeypatch):
    _gql_stub(monkeypatch, [_public_repo(defaultBranchRef=None)])
    snapshot = collect("tester", "token")
    assert snapshot["coverage"]["status"] == "complete"
    assert snapshot["repository_aggregates"]["quality"]["active_repositories"] == 1
    assert snapshot["repository_aggregates"]["quality"]["ci_no_ci"] == 1


def test_rendered_profile_names_reliability_as_not_measured():
    snapshot = _snapshot()
    report = Report(login="tester", generated_at="2026-08-20T12:00:00Z",
                    snapshot=snapshot, findings=run_all(snapshot),
                    source_repository="tester/laurea", source_sha="abc1234")
    profile = render_all(report)["PROFILE.md"]
    assert "reliability or engineering judgment" in profile
    line = next(item for item in profile.splitlines() if "reliability or engineering judgment" in item)
    assert not any(char.isdigit() for char in line)
    assert "test_presence" in json.dumps(report.to_dict())
    cards = render_all(report)
    assert "cards/test_presence.svg" in cards
    assert "cards/ci_health.svg" in cards
    assert "cards/docs_density.svg" in cards


def test_not_measured_tuple_keeps_the_judgment_entry():
    assert any("reliability or engineering judgment" in item for item in NOT_MEASURED)
