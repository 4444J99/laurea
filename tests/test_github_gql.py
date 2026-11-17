"""GraphQL fetches retry transient gateway timeouts and not application errors."""

from io import BytesIO
from unittest.mock import Mock
import json
import urllib.error

import pytest

from laurea import github


def _http_error(code: int, msg: str) -> urllib.error.HTTPError:
    """Build a urllib HTTPError for the GraphQL endpoint."""
    return urllib.error.HTTPError(github.GRAPHQL_URL, code, msg, hdrs=None, fp=BytesIO(b""))


def _response(payload: dict) -> Mock:
    """Build a context-managed urlopen response that returns a JSON payload."""
    resp = Mock()
    resp.read.return_value = json.dumps(payload).encode()
    resp.__enter__ = Mock(return_value=resp)
    resp.__exit__ = Mock(return_value=False)
    return resp


def test_gql_retries_504_then_succeeds(monkeypatch):
    """Verify that a single 504 is retried and the next payload is returned."""
    calls = {"urlopen": 0, "sleep": []}
    payloads = [
        _http_error(504, "Gateway Timeout"),
        _response({"data": {"user": {"login": "4444J99"}}}),
    ]

    def urlopen(_req, timeout=None):
        calls["urlopen"] += 1
        item = payloads.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr(github.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(github.time, "sleep", lambda seconds: calls["sleep"].append(seconds))

    data = github._gql("query($login: String!) { user(login: $login) { login } }",
                       {"login": "4444J99"}, "token")
    assert data == {"user": {"login": "4444J99"}}
    assert calls["urlopen"] == 2
    assert calls["sleep"] == [github.GQL_RETRY_BACKOFF_SECONDS[0]]


@pytest.mark.parametrize("code,msg", [(502, "Bad Gateway"), (503, "Service Unavailable"),
                                      (504, "Gateway Timeout")])
def test_gql_exhausted_gateway_errors_raise(monkeypatch, code, msg):
    """Verify that repeated 502, 503, and 504 responses raise after the bounded retries."""
    calls = {"urlopen": 0, "sleep": []}

    def urlopen(_req, timeout=None):
        calls["urlopen"] += 1
        raise _http_error(code, msg)

    monkeypatch.setattr(github.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(github.time, "sleep", lambda seconds: calls["sleep"].append(seconds))

    with pytest.raises(urllib.error.HTTPError) as excinfo:
        github._gql("query { viewer { login } }", {}, "token")
    assert excinfo.value.code == code
    assert calls["urlopen"] == github.GQL_RETRY_ATTEMPTS
    assert calls["sleep"] == list(github.GQL_RETRY_BACKOFF_SECONDS)


def test_gql_does_not_retry_client_errors(monkeypatch):
    """Verify that a 401 is raised immediately and is not retried."""
    calls = {"urlopen": 0}

    def urlopen(_req, timeout=None):
        calls["urlopen"] += 1
        raise _http_error(401, "Unauthorized")

    monkeypatch.setattr(github.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(github.time, "sleep", lambda _seconds: pytest.fail("slept"))

    with pytest.raises(urllib.error.HTTPError) as excinfo:
        github._gql("query { viewer { login } }", {}, "token")
    assert excinfo.value.code == 401
    assert calls["urlopen"] == 1


def test_gql_does_not_retry_graphql_payload_errors(monkeypatch):
    """Verify that a GraphQL error payload is raised without a retry."""
    calls = {"urlopen": 0}

    def urlopen(_req, timeout=None):
        calls["urlopen"] += 1
        return _response({"errors": [{"message": "Something went wrong"}]})

    monkeypatch.setattr(github.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(github.time, "sleep", lambda _seconds: pytest.fail("slept"))

    with pytest.raises(RuntimeError, match="GraphQL errors"):
        github._gql("query { viewer { login } }", {}, "token")
    assert calls["urlopen"] == 1
