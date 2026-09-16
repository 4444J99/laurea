"""Bounded, read-only repository health observations at one default generation.

Executed Actions evidence is distinct from the repository acceptance predicate.
Permission failures and truncated pages stay unmeasured; alert details stay private.
"""
from __future__ import annotations

import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import quote


class Unmeasured(RuntimeError):
    """A bounded observation could not establish the requested fact."""


class Reader:
    def __init__(self, token: str, *, seconds: float = 60, requests: int = 40):  # allow-secret: runtime parameter or synthetic rejection fixture; no credential literal
        self.token = token  # allow-secret: runtime parameter or synthetic rejection fixture; no credential literal
        self.deadline = time.monotonic() + seconds
        self.remaining = requests

    def __call__(self, path: str) -> Any:
        remaining = self.deadline - time.monotonic()
        if remaining <= 0 or self.remaining <= 0:
            raise Unmeasured("read budget exhausted")
        self.remaining -= 1
        request = urllib.request.Request(
            "https://api.github.com" + path,
            headers={"Authorization": "bearer " + self.token,
                     "Accept": "application/vnd.github+json", "User-Agent": "laurea",
                     "X-GitHub-Api-Version": "2026-03-10"},
        )
        with urllib.request.urlopen(request, timeout=min(10, remaining)) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise Unmeasured("response limit exceeded")
        return json.loads(raw)


def _connection(value: Any, key: str) -> list[dict[str, Any]]:
    if not isinstance(value, dict):
        raise Unmeasured("malformed connection")
    nodes = value.get(key)
    count = value.get("total_count")
    if (not isinstance(nodes, list) or type(count) is not int
            or count != len(nodes) or any(not isinstance(n, dict) for n in nodes)):
        raise Unmeasured("incomplete connection")
    return nodes


def _unknown() -> dict[str, Any]:
    return {"status": "unmeasured"}


def _verification(read: Callable, prefix: str, sha: str) -> dict[str, Any]:
    runs = _connection(read(prefix + "/actions/runs?head_sha=" + sha + "&per_page=100"), "workflow_runs")
    observations = []
    # A bounded subset remains explicit; successful children never cover omitted runs.
    for run in runs[:10]:
        if run.get("head_sha") != sha or type(run.get("id")) is not int:
            raise Unmeasured("run generation mismatch")
        row = {"run_id": run["id"], "head_sha": sha,
               "conclusion": run.get("conclusion"), "execution": "unmeasured"}
        try:
            jobs = _connection(read(prefix + f"/actions/runs/{run['id']}/jobs?filter=latest&per_page=100"), "jobs")
            executed = 0
            for job in jobs:
                if job.get("head_sha") != sha or not isinstance(job.get("steps"), list):
                    raise Unmeasured("job generation or steps unavailable")
                executed += sum(isinstance(step, dict)
                                and step.get("status") == "completed"
                                and step.get("conclusion") in {"success", "failure", "cancelled", "timed_out"}
                                for step in job["steps"])
            row["executed_steps"] = executed
            row["jobs_observed"] = len(jobs)
            row["execution"] = "executed" if executed else "no_executed_steps"
        except (OSError, ValueError, KeyError, TypeError, Unmeasured):
            pass
        observations.append(row)
    return {"status": "measured" if len(runs) <= 10 else "unmeasured",
            "runs_total": len(runs), "runs_observed": observations,
            "runs_unmeasured": max(0, len(runs) - 10),
            "acceptance": "unmeasured",
            "boundary": "Executed steps do not establish the owning verification predicate or required workflow coverage."}


def _security(read: Callable, prefix: str) -> dict[str, Any]:
    result = {}
    for name, endpoint in (("dependabot", "dependabot/alerts"),
                           ("code_scanning", "code-scanning/alerts"),
                           ("secret_scanning", "secret-scanning/alerts")):
        try:
            rows = read(prefix + "/" + endpoint + "?state=open&per_page=100")
            if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                raise Unmeasured("malformed alerts")
            result[name] = {"status": "measured" if len(rows) < 100 else "unmeasured",
                            "open_alerts_observed": len(rows), "complete": len(rows) < 100}
        except (OSError, ValueError, KeyError, TypeError, Unmeasured):
            result[name] = _unknown()
    return result


def _pulls(read: Callable, prefix: str) -> dict[str, Any]:
    rows = read(prefix + "/pulls?state=open&per_page=100")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise Unmeasured("malformed pull requests")
    return {"status": "measured" if len(rows) < 100 else "unmeasured",
            "open_observed": len(rows),
            "readiness": "unmeasured",
            "boundary": "Open count does not establish review, required checks, mergeability or exact-head acceptance."}


def collect_health(repository: str, token: str, *, read: Callable | None = None) -> dict[str, Any]:  # allow-secret: runtime parameter or synthetic rejection fixture; no credential literal
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("repository must be OWNER/NAME")
    read = read or Reader(token)
    result = {"schema_version": "laurea.health.v1", "status": "unmeasured", "observed_at": datetime.now(timezone.utc).isoformat(),
              "generation": "unmeasured", "verification": _unknown(),
              "security": _unknown(), "pr_readiness": _unknown()}
    prefix = "/repos/" + repository
    try:
        repo = read(prefix)
        if not isinstance(repo, dict) or repo.get("private") is not False:
            result["excluded_private_or_unknown"] = True
            return result
        branch = repo["default_branch"]
        if (type(repo.get("id")) is not int or not isinstance(branch, str)
                or not isinstance(repo.get("full_name"), str)):
            raise Unmeasured("repository identity unavailable")
        ref = read(prefix + "/commits/" + quote(branch, safe=""))
        sha = ref["sha"]
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise Unmeasured("default SHA unavailable")
        result.update(repository=repo["full_name"], repository_id=repo["id"], default_sha=sha)
        for key, probe in (("verification", lambda: _verification(read, prefix, sha)),
                           ("security", lambda: _security(read, prefix)),
                           ("pr_readiness", lambda: _pulls(read, prefix))):
            try:
                result[key] = probe()
            except (OSError, ValueError, KeyError, TypeError, Unmeasured):
                result[key] = _unknown()
        after = read(prefix)
        current = read(prefix + "/commits/" + quote(branch, safe=""))
        result["generation"] = "current" if (after.get("id") == repo["id"]
            and after.get("default_branch") == branch and after.get("private") is False
            and current.get("sha") == sha) else "not_current"
    except (OSError, ValueError, KeyError, TypeError, AttributeError, Unmeasured):
        pass
    return result
