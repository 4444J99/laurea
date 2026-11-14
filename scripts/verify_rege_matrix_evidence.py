"""Offline validation for the dated RE:GE matrix-execution evidence record."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "2026-10-02-rege-matrix-execution.json"


def verify(data: dict) -> dict:
    if data.get("schema_version") != "laurea.rege-matrix-execution.v1":
        raise ValueError("unsupported evidence schema")
    repo = data["source_repository"]
    if repo["repository_id"] != 1140011103:
        raise ValueError("unexpected repository identity")
    if repo["head_sha"] != "a00d55f9c3bbbb4486ec0fc7e589bb35d5da905e":
        raise ValueError("unexpected observed head")
    workflow = data["workflow"]
    if workflow["blob_sha"] != "f72e46f5221f522addd2c0b8ed49ae0113fcbb4b":
        raise ValueError("unexpected workflow blob")
    expected = workflow["collection_count"]
    if expected != 1998:
        raise ValueError("unexpected collected suite size")

    by_python = {row["python"]: row for row in data["environments"]}
    p311 = by_python["3.11.16"]
    p312 = by_python["3.12.14"]
    for row in (p311, p312):
        if row["collected"] != expected:
            raise ValueError("matrix collection counts disagree")
        if row["passed"] + row["failed"] + row["skipped"] != expected:
            raise ValueError("test disposition does not reconcile")

    if (p311["passed"], p311["failed"], p311["skipped"]) != (1997, 1, 0):
        raise ValueError("Python 3.11 result mismatch")
    if p311["test_step_conclusion"] != "failure" or p311["job_conclusion"] != "failure":
        raise ValueError("Python 3.11 conclusion mismatch")
    failure = p311["failure"]
    if failure["exception"] != "TypeError" or "EnumType" not in failure["message"]:
        raise ValueError("Python 3.11 failure identity mismatch")

    if (p312["passed"], p312["failed"], p312["skipped"]) != (1998, 0, 0):
        raise ValueError("Python 3.12 result mismatch")
    if p312["test_step_conclusion"] != "success":
        raise ValueError("Python 3.12 test step was not successful")
    if p312["job_conclusion"] != "cancelled":
        raise ValueError("Python 3.12 overall job boundary changed")

    derived = data["derived"]
    if derived["cross_version_full_suite_green"] is not False:
        raise ValueError("evidence must not claim cross-version green")
    if abs(derived["python_311_pass_rate_percent"] - (1997 / 1998 * 100)) > 1e-12:
        raise ValueError("Python 3.11 pass-rate calculation mismatch")
    if derived["python_312_pass_rate_percent"] != 100.0:
        raise ValueError("Python 3.12 pass-rate calculation mismatch")

    return {
        "collected": expected,
        "python_311": {"passed": 1997, "failed": 1},
        "python_312": {"passed": 1998, "failed": 0},
        "cross_version_full_suite_green": False,
    }


def main() -> None:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    print(json.dumps(verify(data), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
