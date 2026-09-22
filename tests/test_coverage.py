"""Collection coverage must survive failures without leaking private rows."""
import json

import pytest

from laurea.github import CoverageError, _paginate_repos, collect


def connection(nodes, total=None, more=False, cursor=None):
    return {"nodes": nodes, "totalCount": len(nodes) if total is None else total,
            "pageInfo": {"hasNextPage": more, "endCursor": cursor}}


@pytest.mark.parametrize("conn", [connection([], 1), connection([], 0, True, None),
                                  {"nodes": None}, connection([None])])
def test_bad_connections_fail_closed(monkeypatch, conn):
    monkeypatch.setattr("laurea.github._gql", lambda *args: {"repos": conn})
    with pytest.raises(CoverageError):
        _paginate_repos("query", ["repos"], {}, "token")


def test_repeated_cursor_is_bounded(monkeypatch):
    calls = []
    def gql(*args):
        calls.append(args)
        return {"repos": connection([{}], 5, True, "same")}
    monkeypatch.setattr("laurea.github._gql", gql)
    with pytest.raises(CoverageError, match="advance"):
        _paginate_repos("query", ["repos"], {}, "token")
    assert len(calls) == 2


@pytest.mark.parametrize("visibility", ["public", "private", "unknown", "different-id", "malformed"])
def test_failed_org_and_private_exclusion_remain_counted(monkeypatch, visibility):
    user = {"login": "tester", "name": "Tester", "createdAt": "2020-01-01Z",
            "followers": {"totalCount": 0}, "contributionsCollection": {
                "contributionCalendar": {"totalContributions": 0},
                "totalCommitContributions": 0, "totalPullRequestContributions": 0,
                "totalPullRequestReviewContributions": 0,
                "totalIssueContributions": 0, "restrictedContributionsCount": 0}}
    def gql(query, variables, token):
        if "node(id:" in query:
            if visibility == "malformed":
                return None
            if visibility == "unknown":
                raise OSError("private API details")
            return {"node": {"id": "other" if visibility == "different-id" else variables["id"], "isPrivate": visibility == "private"}}
        if "contributionsCollection" in query:
            return {"user": user}
        if "organizations(first" in query:
            return {"user": {"organizations": connection([{"login": "org"}])}}
        if "org" in variables:
            raise RuntimeError("private API details must not be published")
        return {"user": {"repositories": connection([
            {"id": "public-id", "nameWithOwner": "tester/public", "isPrivate": False,
             "isFork": False, "isArchived": True, "stargazerCount": 2,
             "defaultBranchRef": {"name": "main", "target": {"oid": "abc"}}},
            {"id": "secret-id", "nameWithOwner": "tester/secret", "isPrivate": True, "isFork": False, "stargazerCount": 3}])}}
    monkeypatch.setattr("laurea.github._gql", gql)
    snapshot = collect("tester", "token")
    assert snapshot["coverage"]["status"] == "unmeasured"
    assert snapshot["coverage"]["failed_sources"] == 1
    assert snapshot["coverage"]["observed_repositories"] == 2
    assert snapshot["coverage"]["private_repositories_excluded"] == (2 if visibility == "private" else 1)
    assert snapshot["repository_aggregates"]["nonfork_repositories"] == 2
    assert snapshot["repository_aggregates"]["stars"] == 5
    if visibility == "public":
        assert snapshot["repos"][0]["defaultBranchRef"]["target"]["oid"] == "abc"
        assert snapshot["repos"][0]["health"]["verification"] == "unmeasured"
    else:
        assert snapshot["repos"] == []
        assert "tester/public" not in json.dumps(snapshot)
        assert snapshot["coverage"]["visibility_unmeasured"] == int(visibility in {"unknown", "different-id", "malformed"})
    assert "secret" not in json.dumps(snapshot)
    assert "private API details" not in json.dumps(snapshot)


def test_multiple_pages_preserve_cursor_and_total(monkeypatch):
    calls = []
    def gql(query, variables, token):
        calls.append(variables["cursor"])
        if variables["cursor"] is None:
            return {"repos": connection([{"id": "one"}], 2, True, "next")}
        return {"repos": connection([{"id": "two"}], 2)}
    monkeypatch.setattr("laurea.github._gql", gql)
    assert len(_paginate_repos("query", ["repos"], {}, "token")) == 2
    assert calls == [None, "next"]


def test_changed_denominator_is_unmeasured(monkeypatch):
    pages = iter([connection([{}], 2, True, "next"), connection([{}], 3)])
    monkeypatch.setattr("laurea.github._gql", lambda *args: {"repos": next(pages)})
    with pytest.raises(CoverageError, match="changed"):
        _paginate_repos("query", ["repos"], {}, "token")


def test_membership_and_repository_failures_have_both_attempts(monkeypatch):
    user = {"login": "tester", "name": "Tester", "createdAt": "2020-01-01Z",
            "followers": {"totalCount": 0}, "contributionsCollection": {
                "contributionCalendar": {"totalContributions": 0},
                "totalCommitContributions": 0, "totalPullRequestContributions": 0,
                "totalPullRequestReviewContributions": 0,
                "totalIssueContributions": 0, "restrictedContributionsCount": 0}}
    def gql(query, *args):
        if "contributionsCollection" in query:
            return {"user": user}
        raise OSError("unavailable")
    monkeypatch.setattr("laurea.github._gql", gql)
    coverage = collect("tester", "fixture")["coverage"]
    assert coverage["failed_sources"] == coverage["sources_attempted"] == 2


@pytest.mark.parametrize("pages", [
    [connection([], 0, True, "next"), connection([], 0)],
    [connection([], 1, True, "next"), connection([{"id": "one"}], 1)],
    [connection([{"id": "one"}], 1, True, "next"), connection([], 1)],
    [connection([{"id": "one"}, {"id": "two"}], 1, True, "next"), connection([], 1)],
    [connection([{"id": "one"}], 2, True, "first"),
     connection([], 2, True, "second"), connection([{"id": "two"}], 2)],
    [connection([{"id": "one"}], 2, True, "first"),
     connection([{"id": "two"}], 2, True, "second"), connection([], 2)],
])
def test_impossible_nonterminal_page_stops_before_next_request(monkeypatch, pages):
    """Reject inconsistent page evidence without requesting a later page."""
    calls = []
    expected_calls = 2 if len(pages) == 3 else 1

    def gql(query, variables, token):
        calls.append(variables["cursor"])
        return {"repos": pages[len(calls) - 1]}

    monkeypatch.setattr("laurea.github._gql", gql)
    with pytest.raises(CoverageError, match="inconsistent pagination state"):
        _paginate_repos("query", ["repos"], {}, "fixture")
    assert len(calls) == expected_calls


@pytest.mark.parametrize("failed_source", ["memberships", "personal", "organization"])
def test_impossible_pagination_cannot_claim_complete_collection(monkeypatch, failed_source):
    """Keep each source failure unmeasured and outside publication admission."""
    from laurea.corpus import require_complete

    user = {"login": "tester", "name": "Tester", "createdAt": "2020-01-01Z",
            "followers": {"totalCount": 0}, "contributionsCollection": {
                "contributionCalendar": {"totalContributions": 0},
                "totalCommitContributions": 0, "totalPullRequestContributions": 0,
                "totalPullRequestReviewContributions": 0,
                "totalIssueContributions": 0, "restrictedContributionsCount": 0}}
    calls = []

    def gql(query, variables, token):
        if "contributionsCollection" in query:
            return {"user": user}
        if "organizations(first" in query:
            source, parent, key = "memberships", "user", "organizations"
            nodes = [{"login": "org"}] if failed_source == "organization" else []
        elif "org" in variables:
            source, parent, key, nodes = "organization", "organization", "repositories", []
        else:
            source, parent, key, nodes = "personal", "user", "repositories", []
        calls.append((source, variables["cursor"]))
        if source == failed_source and variables["cursor"] is None:
            return {parent: {key: connection([], 0, True, "impossible-next")}}
        return {parent: {key: connection(nodes)}}

    monkeypatch.setattr("laurea.github._gql", gql)
    snapshot = collect("tester", "fixture")
    assert snapshot["coverage"]["status"] == "unmeasured"
    assert snapshot["coverage"]["failed_sources"] == 1
    assert snapshot["coverage"]["sources_attempted"] == (3 if failed_source == "organization" else 2)
    assert snapshot["coverage"]["organization_scope_complete"] is (failed_source != "memberships")
    assert all(cursor is None for _, cursor in calls)
    with pytest.raises(ValueError, match="coverage is unmeasured"):
        require_complete(snapshot)


def test_empty_terminal_connection_remains_valid(monkeypatch):
    """Allow a genuine complete empty source instead of conflating it with failure."""
    calls = []

    def gql(query, variables, token):
        calls.append(variables["cursor"])
        return {"repos": connection([], 0)}

    monkeypatch.setattr("laurea.github._gql", gql)
    assert _paginate_repos("query", ["repos"], {}, "fixture") == []
    assert calls == [None]
