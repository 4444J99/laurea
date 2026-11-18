"""Identity-free corpus totals and publication coverage guards."""
from __future__ import annotations

from typing import Any


def require_complete(snapshot: dict[str, Any]) -> None:
    """Reject known incomplete/new malformed coverage before any publication."""
    if "coverage" not in snapshot:
        return  # Legacy unredacted v2 snapshots retain their recorded semantics.
    coverage = snapshot["coverage"]
    if (not isinstance(coverage, dict) or coverage.get("status") != "complete"
            or coverage.get("organization_scope_complete") is not True
            or type(coverage.get("failed_sources")) is not int
            or coverage["failed_sources"] != 0):
        raise ValueError("source coverage is unmeasured; existing published assets and history are preserved")
    if coverage.get("private_repositories_excluded", 0) and "repository_aggregates" not in snapshot:
        raise ValueError("redacted corpus is missing its aggregate evidence")


def aggregate_repositories(repos: list[dict[str, Any]]) -> dict[str, Any]:
    """Count non-fork repositories and languages, and stars across all supplied repositories.

    Reject missing aggregate fields rather than inferring zero; return no repository identities.
    """
    languages: dict[str, int] = {}
    nonfork = 0
    stars = 0
    for repo in repos:
        if (type(repo.get("isFork")) is not bool or type(repo.get("stargazerCount")) is not int
                or repo["stargazerCount"] < 0):
            raise ValueError("repository aggregate fields unavailable")
        stars += repo["stargazerCount"]
        if repo["isFork"]:
            continue
        nonfork += 1
        primary = repo.get("primaryLanguage")
        if primary is not None:
            if not isinstance(primary, dict) or not isinstance(primary.get("name"), str) or not primary["name"]:
                raise ValueError("repository language unavailable")
            language = primary["name"]
            languages[language] = languages.get(language, 0) + 1
    return {"scope": "token_visible", "nonfork_repositories": nonfork,
            "stars": stars, "primary_languages": languages}


def aggregate_quality(signals: list[dict[str, Any]]) -> dict[str, Any]:
    """Count test presence, CI health, and docs density over active repositories.

    ``signals`` carries one identity-free record per active repository:
    ``test_signal`` (bool), ``ci`` (one of "green", "failing", "pending",
    "none"), ``substantive_readme`` (bool), ``docs_dir`` (bool). Counts are
    validated against the denominator rather than inferred; return no
    repository identities.
    """
    active = len(signals)
    counts = {
        "test_presence": 0,
        "ci_green": 0,
        "ci_no_ci": 0,
        "ci_pending": 0,
        "docs_substantive_readme": 0,
        "docs_dir": 0,
    }
    for signal in signals:
        if (not isinstance(signal, dict) or type(signal.get("test_signal")) is not bool
                or signal.get("ci") not in ("green", "failing", "pending", "none")
                or type(signal.get("substantive_readme")) is not bool
                or type(signal.get("docs_dir")) is not bool):
            raise ValueError("repository quality signal unavailable")
        if signal["test_signal"]:
            counts["test_presence"] += 1
        if signal["ci"] == "green":
            counts["ci_green"] += 1
        elif signal["ci"] == "none":
            counts["ci_no_ci"] += 1
        elif signal["ci"] == "pending":
            counts["ci_pending"] += 1
        if signal["substantive_readme"]:
            counts["docs_substantive_readme"] += 1
        if signal["docs_dir"]:
            counts["docs_dir"] += 1
    quality = {"active_repositories": active, **counts}
    validate_quality(quality)
    return quality


def validate_quality(quality: dict[str, Any]) -> None:
    """Reject malformed quality aggregates: counts must be integers within the denominator."""
    keys = ("active_repositories", "test_presence", "ci_green", "ci_no_ci",
            "ci_pending", "docs_substantive_readme", "docs_dir")
    if not isinstance(quality, dict) or set(quality) != set(keys):
        raise ValueError("invalid repository quality aggregate evidence")
    if any(type(quality.get(key)) is not int or quality[key] < 0 for key in keys):
        raise ValueError("invalid repository quality aggregate evidence")
    denominator = quality["active_repositories"]
    if any(quality[key] > denominator for key in keys[1:]):
        raise ValueError("repository quality counts exceed the active denominator")


def corpus_totals(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Validate complete corpus evidence and return identity-free totals.

    Reuse validated redacted aggregates when present; derive totals from legacy repository rows otherwise.
    """
    require_complete(snapshot)
    value = snapshot.get("repository_aggregates")
    if value is None:
        return aggregate_repositories(snapshot["repos"])
    if (not isinstance(value, dict) or value.get("scope") != "token_visible"
            or any(type(value.get(k)) is not int or value[k] < 0 for k in ("nonfork_repositories", "stars"))
            or not isinstance(value.get("primary_languages"), dict)
            or any(not isinstance(k, str) or not k or type(v) is not int or v < 1
                   for k, v in value["primary_languages"].items())
            or sum(value["primary_languages"].values()) > value["nonfork_repositories"]):
        raise ValueError("invalid repository aggregate evidence")
    if "quality" in value:
        validate_quality(value["quality"])
    return value
