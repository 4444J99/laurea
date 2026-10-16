"""Independently recompute the dated accepted-patch and CI-provenance evidence."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "2026-10-16-accepted-patch-and-ci.json"
CATEGORIES = {
    "runtime_correctness": 3,
    "runtime_documentation": 1,
    "authentication_ui_copy": 1,
    "security_workflow_and_repository_policy": 1,
}


def verify(data: dict) -> dict:
    if data.get("schema_version") != "laurea.accepted-patch-and-ci.v1":
        raise ValueError("evidence schema changed")
    ci = data["rege_ci_recheck"]
    if (ci["repository_id"], ci["pull_request"], ci["head_sha"], ci["workflow_blob_sha"]) != (
        1140011103, 35, "18287492a065e3942c68424352f66dd575ba562f", "fb68c38867a6c45f6eb6f57e4cf97d6c7deb43ce"
    ):
        raise ValueError("RE:GE source identity drift")
    if ci["run_id"] != 37061751413 or ci["test_root"] != "rege/tests":
        raise ValueError("RE:GE run or package test root drift")
    if "rege/tests" in ci["workflow_test_roots"]:
        raise ValueError("current workflow cannot be relabeled as package-aware")
    jobs = ci["jobs"]
    if {j["python"] for j in jobs} != {"3.11", "3.12"} or len(jobs) != 2:
        raise ValueError("matrix environment set drift")
    if {j["job_id"] for j in jobs} != {111019797405, 111019797600}:
        raise ValueError("matrix job identity drift")
    if not all(j["job_conclusion"] == "success" and j["executed_package_test_cases"] == 0
               and j["test_step_notice"] == "No tests directory found, skipping tests" for j in jobs):
        raise ValueError("green CI cannot be equated to an executed test suite")

    c = data["accepted_patch_census"]
    records = c["records"]
    if len(records) != 6 or len({(r["repo_id"], r["pr"]) for r in records}) != 6:
        raise ValueError("accepted PR identities duplicated or missing")
    if not all(r["author"] == "4444J99" and r["merged"] and len(r["merge_sha"]) == 40 for r in records):
        raise ValueError("author or merge identity not evidenced")
    categories = Counter(r["category"] for r in records)
    if categories != CATEGORIES:
        raise ValueError("patch categories do not reconcile")
    changed_files = sum(len(r["files"]) for r in records)
    test_counts = [sum(p.startswith("tests/") or "/tests/" in p for p in r["files"]) for r in records]
    actual = {
        "accepted_prs": len(records), "changed_file_entries": changed_files,
        "runtime_correctness_prs": categories["runtime_correctness"],
        "prs_with_changed_test_files": sum(bool(n) for n in test_counts),
        "changed_test_files": sum(test_counts),
        "runtime_documentation_prs": categories["runtime_documentation"],
        "authentication_ui_copy_prs": categories["authentication_ui_copy"],
        "security_workflow_and_repository_policy_prs": categories["security_workflow_and_repository_policy"],
    }
    if c["reported_counts"] != actual:
        raise ValueError("accepted-patch arithmetic mismatch")
    ns = data["namespace_followup"]
    old = ns["previous"]
    new = ns["derived"]
    extra = ns["new_public_search_entry"]
    if ns["rechecked_previous_entries"] != 32 or ns["previous_entries_with_state_change"] != 0:
        raise ValueError("previous snapshot recheck scope drift")
    if old != {"prs": 32, "distinct_repositories": 30, "merged": 7, "open": 13, "closed_unmerged": 12}:
        raise ValueError("previous namespace snapshot drift")
    if (extra["repository_id"], extra["pr"], extra["author"], extra["state"], extra["merged"]) != (
        73011784, 15, "4444J99", "open", False
    ):
        raise ValueError("new namespace entry provenance drift")
    if new != {"prs": old["prs"] + 1, "distinct_repositories": old["distinct_repositories"],
               "merged": old["merged"], "open": old["open"] + 1, "closed_unmerged": old["closed_unmerged"]}:
        raise ValueError("namespace delta does not reconcile")
    return {"green_jobs_with_zero_package_tests": 2, "accepted_patch_counts": actual,
            "namespace_delta": new, "cross_version_green_on_repaired_head": False}


if __name__ == "__main__":
    print(json.dumps(verify(json.loads(EVIDENCE.read_text())), indent=2, sort_keys=True))