"""Live snapshot collection from the GitHub GraphQL API.

Zero dependencies: urllib only. The token comes from LAUREA_TOKEN,
GH_TOKEN, or GITHUB_TOKEN (first found). Public data is enough for
every axis; a user-scoped token additionally counts private
(restricted) contributions.
"""

from __future__ import annotations

from .corpus import aggregate_quality, aggregate_repositories

import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

GRAPHQL_URL = "https://api.github.com/graphql"
REST_API_URL = "https://api.github.com"

# A README counts as substantive only at or above this byte floor, cited in
# the detector evidence. The floor is a stated size, not a judgement of content.
QUALITY_README_MIN_BYTES = 1024

# Test-command spellings recognised inside a workflow file. A workflow that
# only lints, builds, or deploys does not establish a test signal.
QUALITY_TEST_COMMANDS = (
    "pytest", "npm test", "npm run test", "go test", "cargo test",
    "make test", "ctest", "jest", "vitest", "rspec", "phpunit",
)

# Transient GitHub GraphQL gateway failures are retried a bounded number
# of times. Auth failures and GraphQL payload errors are not retried.
GQL_RETRY_ATTEMPTS = 3
GQL_RETRY_BACKOFF_SECONDS = (2, 4)
GQL_RETRY_STATUS_CODES = frozenset({502, 503, 504})

_USER_QUERY = """
query($login: String!) {
  user(login: $login) {
    login
    name
    createdAt
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, first: 100) { totalCount }
    contributionsCollection {
      contributionCalendar { totalContributions }
      totalCommitContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      totalIssueContributions
      restrictedContributionsCount
    }
  }
}
"""

_ORG_REPOS_QUERY = """
query($org: String!, $cursor: String) {
  organization(login: $org) {
    repositories(first: 100, after: $cursor, ownerAffiliations: OWNER) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        nameWithOwner
        isPrivate
        defaultBranchRef { name target { oid } }
        name
        isFork
        isArchived
        stargazerCount
        pushedAt
        primaryLanguage { name }
      }
    }
  }
}
"""

_USER_REPOS_QUERY = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    repositories(first: 100, after: $cursor, ownerAffiliations: OWNER) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        nameWithOwner
        isPrivate
        defaultBranchRef { name target { oid } }
        name
        isFork
        isArchived
        stargazerCount
        pushedAt
        primaryLanguage { name }
      }
    }
  }
}
"""


def resolve_token() -> str:
    """Read the configured token variables in priority order, then try the authenticated GitHub CLI.

    Return the existing credential without provisioning one; raise RuntimeError when none is available.
    """
    for var in ("LAUREA_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        token = os.environ.get(var)
        if token:
            return token
    try:
        out = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=10
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    raise RuntimeError(
        "No GitHub token found: set LAUREA_TOKEN, GH_TOKEN, or GITHUB_TOKEN."
    )


def _transient_http_error(exc: BaseException) -> bool:
    """Return True when the failure is a retryable GraphQL gateway status."""
    return isinstance(exc, urllib.error.HTTPError) and exc.code in GQL_RETRY_STATUS_CODES


def _gql(query: str, variables: dict[str, Any], token: str) -> dict[str, Any]:
    """Send one authenticated GraphQL request with a 30-second timeout and reject API error payloads.

    Retry 502, 503, and 504 responses up to GQL_RETRY_ATTEMPTS total tries,
    sleeping GQL_RETRY_BACKOFF_SECONDS between attempts.
    """
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "laurea",
        },
    )
    for attempt in range(GQL_RETRY_ATTEMPTS):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read())
            if payload.get("errors"):
                raise RuntimeError(f"GraphQL errors: {payload['errors']}")
            return payload["data"]
        except urllib.error.HTTPError as exc:
            if not _transient_http_error(exc) or attempt == GQL_RETRY_ATTEMPTS - 1:
                raise
            time.sleep(GQL_RETRY_BACKOFF_SECONDS[attempt])
    raise RuntimeError("GraphQL retry loop exited without a result")


class CoverageError(RuntimeError):
    """A connection could not establish a complete, stable denominator."""


def _rest_get(path: str, token: str) -> Any:
    """Send one authenticated REST GET with a 30-second timeout.

    Raise CoverageError on any transport or payload failure; a failed probe
    is a failed source, never a silent omission.
    """
    req = urllib.request.Request(
        REST_API_URL + path,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "laurea",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except (urllib.error.HTTPError, urllib.error.URLError, OSError, ValueError) as exc:
        raise CoverageError(f"REST request failed: {path}") from exc


def _tree_quality_signals(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Scan one recursive git tree for test, README, and docs signals.

    The signal definition is the one the quality detectors cite: a ``tests/``
    or ``test/`` directory, a ``*_test.py`` or ``*.test.*`` file, a root
    README of at least QUALITY_README_MIN_BYTES, a ``docs/`` directory.
    Workflow paths and a root pyproject are returned for a content read;
    their presence alone is not a test signal.
    """
    signals = {
        "test_signal": False,
        "substantive_readme": False,
        "docs_dir": False,
        "has_pyproject": False,
        "workflow_paths": [],
    }
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise CoverageError("malformed git tree entry")
        path = entry["path"]
        parts = path.split("/")
        if "tests" in parts or "test" in parts:
            signals["test_signal"] = True
        name = parts[-1]
        if name.endswith("_test.py") or ".test." in name:
            signals["test_signal"] = True
        if len(parts) == 1 and name.lower().startswith("readme"):
            size = entry.get("size")
            if entry.get("type") == "blob" and type(size) is int and size >= QUALITY_README_MIN_BYTES:
                signals["substantive_readme"] = True
        if parts[0] == "docs":
            signals["docs_dir"] = True
        if path == "pyproject.toml":
            signals["has_pyproject"] = True
        if (len(parts) == 3 and parts[0] == ".github" and parts[1] == "workflows"
                and (name.endswith(".yml") or name.endswith(".yaml"))):
            signals["workflow_paths"].append(path)
    return signals


def _read_text_file(owner: str, repo: str, path: str, branch: str, token: str, rest_get) -> str:
    """Read one small text file from a branch; raise CoverageError when unreadable."""
    payload = rest_get(
        f"/repos/{owner}/{repo}/contents/{urllib.parse.quote(path, safe='')}"
        f"?ref={urllib.parse.quote(branch, safe='')}",
        token,
    )
    if not isinstance(payload, dict) or payload.get("encoding") != "base64" or not isinstance(payload.get("content"), str):
        raise CoverageError(f"unreadable file content: {path}")
    import base64

    try:
        return base64.b64decode(payload["content"]).decode("utf-8", "replace")
    except (ValueError, TypeError) as exc:
        raise CoverageError(f"unreadable file content: {path}") from exc


def _probe_ci(owner: str, repo: str, head_sha: str, token: str, rest_get) -> str:
    """Read the latest completed default-branch verdict: green, failing, pending, or none.

    "green" needs at least one success and no failure-ish conclusion among
    completed check runs. A repository with no check runs and no commit
    statuses has no CI at all ("none"). Runs that exist but have no completed
    verdict are "pending", not green and not a failure.
    """
    runs = rest_get(f"/repos/{owner}/{repo}/commits/{head_sha}/check-runs?per_page=100", token)
    if not isinstance(runs, dict) or not isinstance(runs.get("check_runs"), list):
        raise CoverageError("unreadable check runs")
    check_runs = runs["check_runs"]
    if not check_runs:
        status = rest_get(f"/repos/{owner}/{repo}/commits/{head_sha}/status", token)
        if not isinstance(status, dict) or not isinstance(status.get("statuses"), list):
            raise CoverageError("unreadable commit status")
        if not status["statuses"]:
            return "none"
        state = status.get("state")
        if state == "success":
            return "green"
        if state in ("failure", "error"):
            return "failing"
        if state == "pending":
            return "pending"
        raise CoverageError("unreadable commit status state")
    completed = [run for run in check_runs if isinstance(run, dict) and run.get("status") == "completed"]
    if not completed:
        return "pending"
    conclusions = [run.get("conclusion") for run in completed]
    if any(conclusion not in ("success", "skipped", "neutral", "cancelled", "timed_out",
                              "action_required", "stale", "failure") for conclusion in conclusions):
        raise CoverageError("unreadable check-run conclusion")
    if any(conclusion in ("failure", "cancelled", "timed_out", "action_required", "stale")
           for conclusion in conclusions):
        return "failing"
    if any(conclusion == "success" for conclusion in conclusions):
        return "green"
    return "pending"


def _probe_repo_quality(owner: str, repo: str, branch: str, head_sha: str, token: str,
                        rest_get=_rest_get) -> dict[str, Any]:
    """Probe one active repository for quality signals; raise on any uncertain read.

    A truncated tree cannot establish absence, so it fails the probe instead
    of reporting a negative. Presence found in the returned portion is
    certain; absence is only reported from a complete tree.
    """
    tree = rest_get(
        f"/repos/{owner}/{repo}/git/trees/{urllib.parse.quote(branch, safe='')}?recursive=1",
        token,
    )
    if not isinstance(tree, dict) or not isinstance(tree.get("tree"), list):
        raise CoverageError("unreadable git tree")
    if tree.get("truncated") is True:
        raise CoverageError("truncated git tree cannot establish absence")
    signals = _tree_quality_signals(tree["tree"])
    if signals["has_pyproject"]:
        text = _read_text_file(owner, repo, "pyproject.toml", branch, token, rest_get)
        if "[tool.pytest]" in text:
            signals["test_signal"] = True
    for workflow in signals["workflow_paths"]:
        text = _read_text_file(owner, repo, workflow, branch, token, rest_get)
        if any(command in text for command in QUALITY_TEST_COMMANDS):
            signals["test_signal"] = True
            break
    return {
        "test_signal": signals["test_signal"],
        "ci": _probe_ci(owner, repo, head_sha, token, rest_get),
        "substantive_readme": signals["substantive_readme"],
        "docs_dir": signals["docs_dir"],
    }


def _collect_quality(repos: list[dict[str, Any]], token: str) -> tuple[dict[str, Any] | None, int, int]:
    """Probe the active repositories for quality signals.

    Returns (quality aggregates or None, failed probe count, repositories
    probed). The first failed probe aborts the pass: no partial quality is
    attached, and the caller records the failure so the run refuses to publish.
    A repository with no default branch is empty; its signals are all absent,
    which is a measurement, not a probe failure.
    """
    active = [repo for repo in repos
              if repo.get("isFork") is False and repo.get("isArchived") is not True]
    signals: list[dict[str, Any]] = []
    for repo in active:
        name_with_owner = repo.get("nameWithOwner")
        if not isinstance(name_with_owner, str) or "/" not in name_with_owner:
            return None, 1, len(signals)
        owner, name = name_with_owner.split("/", 1)
        ref = repo.get("defaultBranchRef") or {}
        branch = ref.get("name")
        head_sha = (ref.get("target") or {}).get("oid")
        if not branch or not head_sha:
            signals.append({"test_signal": False, "ci": "none",
                            "substantive_readme": False, "docs_dir": False})
            continue
        try:
            signals.append(_probe_repo_quality(owner, name, branch, head_sha, token, rest_get=_rest_get))
        except (RuntimeError, ValueError, KeyError, OSError):
            return None, 1, len(signals)
    return aggregate_quality(signals), 0, len(signals)


def _paginate_repos(
    query: str, key_path: list[str], variables: dict[str, Any], token: str
) -> list[dict[str, Any]]:
    """Read a stable connection, rejecting impossible nonterminal page evidence."""
    nodes: list[dict[str, Any]] = []
    cursor: str | None = None
    seen: set[str] = set()
    total: int | None = None
    for _ in range(100):
        conn = _gql(query, {**variables, "cursor": cursor}, token)
        try:
            for key in key_path:
                conn = conn[key]
            count, batch, page = conn["totalCount"], conn["nodes"], conn["pageInfo"]
            if type(count) is not int or count < 0 or not isinstance(batch, list):
                raise CoverageError("malformed connection")
            if total is not None and total != count:
                raise CoverageError("connection changed during collection")
            total = count
            if any(not isinstance(node, dict) for node in batch):
                raise CoverageError("malformed node")
            nodes.extend(batch)
            if type(page["hasNextPage"]) is not bool:
                raise CoverageError("malformed page state")
            if not page["hasNextPage"]:
                if len(nodes) != total:
                    raise CoverageError("connection count mismatch")
                return nodes
            if not batch or len(nodes) >= total:
                raise CoverageError("inconsistent pagination state")
            cursor = page["endCursor"]
            if not isinstance(cursor, str) or not cursor or cursor in seen:
                raise CoverageError("pagination did not advance")
            seen.add(cursor)
        except (KeyError, TypeError) as exc:
            raise CoverageError("unreadable connection") from exc
    raise CoverageError("pagination limit reached")


_ORGS_QUERY = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    organizations(first: 100, after: $cursor) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes { login }
    }
  }
}
"""


def collect(login: str, token: str | None = None) -> dict[str, Any]:
    """Collect visible sources with explicit incomplete and excluded coverage."""
    token = token or resolve_token()
    user = _gql(_USER_QUERY, {"login": login}, token)["user"]
    if not isinstance(user, dict):
        raise ValueError(
            f"GitHub login @{login} is not a user; set LAUREA_LOGIN to a user account"
        )

    failures = 0
    try:
        org_nodes = _paginate_repos(
            _ORGS_QUERY, ["user", "organizations"], {"login": login}, token
        )
        org_logins = [node["login"] for node in org_nodes]
        if any(not isinstance(org, str) or not org for org in org_logins):
            raise CoverageError("malformed organization")
        if len(set(org_logins)) != len(org_logins):
            raise CoverageError("duplicate organization")
        org_scope_complete = True
    except (RuntimeError, ValueError, KeyError, OSError):
        org_logins = []
        org_scope_complete = False
        failures += 1

    repos = []
    visible_repos = []
    private_count = 0
    visibility_unmeasured = 0
    observed_ids: set[str] = set()
    sources = [(_USER_REPOS_QUERY, ["user", "repositories"], {"login": login})]
    sources += [(_ORG_REPOS_QUERY, ["organization", "repositories"], {"org": org})
                for org in org_logins]
    for query, path, variables in sources:
        try:
            batch = _paginate_repos(query, path, variables, token)
            aggregate_repositories(batch)  # Validate before consuming any partial source.
            ids = [repo.get("id") for repo in batch]
            if (any(not isinstance(identity, str) or not identity for identity in ids)
                    or len(set(ids)) != len(ids)
                    or any(type(repo.get("isPrivate")) is not bool for repo in batch)):
                raise CoverageError("malformed repository identity or visibility")
        except (RuntimeError, ValueError, KeyError, OSError):
            failures += 1
            continue
        for repo in batch:
            if repo["id"] in observed_ids:
                continue
            observed_ids.add(repo["id"])
            visible_repos.append(repo)
            if repo["isPrivate"]:
                private_count += 1
                continue
            try:
                current = _gql(
                    "query($id: ID!) { node(id: $id) { ... on Repository { id isPrivate } } }",
                    {"id": repo["id"]}, token,
                ).get("node")
            except (RuntimeError, ValueError, KeyError, OSError, AttributeError, TypeError):
                current = None
            if not isinstance(current, dict) or current.get("id") != repo["id"] or type(current.get("isPrivate")) is not bool:
                visibility_unmeasured += 1
                continue
            if current["isPrivate"]:
                private_count += 1
                continue
            # Reconfirm visibility at the immutable ID before retaining identity.
            repo["health"] = {
                "verification": "unmeasured",
                "security": "unmeasured",
                "pr_readiness": "unmeasured",
            }
            repos.append(repo)

    contrib = user["contributionsCollection"]
    quality, quality_failures, quality_probed = _collect_quality(repos, token)
    failures += quality_failures
    aggregates = aggregate_repositories(visible_repos)
    if quality is not None:
        aggregates["quality"] = quality
    return {
        "login": user["login"],
        "name": user["name"],
        "created_at": user["createdAt"],
        "followers": user["followers"]["totalCount"],
        "orgs": org_logins,
        "repos": repos,
        "repository_aggregates": aggregates,
        "coverage": {
            "status": "complete" if failures == 0 and visibility_unmeasured == 0 else "unmeasured",
            "scope": "token-visible personal repositories and organization memberships; not an administered-estate census",
            "organization_scope_complete": org_scope_complete,
            "sources_attempted": len(sources) + 1,
            "source_count_scope": "membership discovery and repository connections",
            "failed_sources": failures,
            "observed_repositories": len(observed_ids),
            "public_repositories": len(repos),
            "private_repositories_excluded": private_count,
            "visibility_unmeasured": visibility_unmeasured,
            "archived_public_repositories": sum(repo.get("isArchived") is True for repo in repos),
            "health_status": "unmeasured",
            "quality_repositories_probed": quality_probed,
        },
        "contributions": {
            "total": contrib["contributionCalendar"]["totalContributions"],
            "commits": contrib["totalCommitContributions"],
            "pull_requests": contrib["totalPullRequestContributions"],
            "reviews": contrib["totalPullRequestReviewContributions"],
            "issues": contrib["totalIssueContributions"],
            "restricted": contrib["restrictedContributionsCount"],
        },
    }
