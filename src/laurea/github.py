"""Live snapshot collection from the GitHub GraphQL API.

Zero dependencies: urllib only. The token comes from LAUREA_TOKEN,
GH_TOKEN, or GITHUB_TOKEN (first found). Public data is enough for
every axis; a user-scoped token additionally counts private
(restricted) contributions.
"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from typing import Any

GRAPHQL_URL = "https://api.github.com/graphql"

_USER_QUERY = """
query($login: String!) {
  user(login: $login) {
    login
    name
    createdAt
    followers { totalCount }
    organizations(first: 20) { nodes { login } }
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


def _candidate_tokens() -> list[str]:
    tokens: list[str] = []
    for var in ("LAUREA_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        token = os.environ.get(var)
        if token and token not in tokens:
            tokens.append(token)
    try:
        out = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=10
        )
        if out.returncode == 0 and out.stdout.strip():
            tok = out.stdout.strip()
            if tok not in tokens:
                tokens.append(tok)
    except (OSError, subprocess.TimeoutExpired):
        pass
    if not tokens:
        raise RuntimeError(
            "No GitHub token found: set LAUREA_TOKEN, GH_TOKEN, or GITHUB_TOKEN."
        )
    return tokens


def resolve_token() -> str:
    return _candidate_tokens()[0]


def _gql(query: str, variables: dict[str, Any], token: str) -> dict[str, Any]:
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
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read())
    if payload.get("errors"):
        raise RuntimeError(f"GraphQL errors: {payload['errors']}")
    return payload["data"]


def _gql_with_fallback(
    query: str, variables: dict[str, Any], tokens: list[str]
) -> tuple[dict[str, Any], str]:
    last_err: Exception | None = None
    for token in tokens:
        try:
            return _gql(query, variables, token), token
        except urllib.error.HTTPError as err:
            last_err = err
            if err.code != 401:
                raise
            # Unauthorized: try the next token (e.g. expired LAUREA_TOKEN).
            continue
    if last_err:
        raise last_err
    raise RuntimeError("no usable token")


def _paginate_repos(
    query: str, key_path: list[str], variables: dict[str, Any], token: str
) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        data = _gql(query, {**variables, "cursor": cursor}, token)
        conn = data
        for key in key_path:
            conn = conn[key]
        nodes.extend(conn["nodes"])
        page = conn["pageInfo"]
        if not page["hasNextPage"]:
            return nodes
        cursor = page["endCursor"]


def collect(login: str, token: str | None = None) -> dict[str, Any]:
    """Collect the full identity snapshot: user, orgs, every owned repo."""
    tokens = [token] if token else _candidate_tokens()
    data, working_token = _gql_with_fallback(_USER_QUERY, {"login": login}, tokens)
    user = data["user"]
    if not isinstance(user, dict):
        raise ValueError(
            f"GitHub login @{login} is not a user; set LAUREA_LOGIN to a user account"
        )

    repos = _paginate_repos(
        _USER_REPOS_QUERY, ["user", "repositories"], {"login": login}, working_token
    )
    org_logins = [n["login"] for n in user["organizations"]["nodes"]]
    for org in org_logins:
        try:
            repos.extend(
                _paginate_repos(
                    _ORG_REPOS_QUERY, ["organization", "repositories"], {"org": org}, working_token
                )
            )
        except RuntimeError:
            # Repositories the token cannot read do not enter the visible corpus.
            continue

    contrib = user["contributionsCollection"]
    return {
        "login": user["login"],
        "name": user["name"],
        "created_at": user["createdAt"],
        "followers": user["followers"]["totalCount"],
        "orgs": org_logins,
        "repos": repos,
        "contributions": {
            "total": contrib["contributionCalendar"]["totalContributions"],
            "commits": contrib["totalCommitContributions"],
            "pull_requests": contrib["totalPullRequestContributions"],
            "reviews": contrib["totalPullRequestReviewContributions"],
            "issues": contrib["totalIssueContributions"],
            "restricted": contrib["restrictedContributionsCount"],
        },
    }
