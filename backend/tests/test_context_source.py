"""Unit tests for context_source.py."""

import subprocess
from unittest.mock import patch, MagicMock

import pytest

from src.context_source import ContextFetcher, ContextSourceError, _replace_placeholders, MAX_TIMEOUT


# ─── _replace_placeholders ───────────────────────────────────────


def test_replace_placeholders_str():
    assert _replace_placeholders("query: {input}", "hello") == "query: hello"


def test_replace_placeholders_dict():
    result = _replace_placeholders({"q": "{input}", "k": 5}, "world")
    assert result == {"q": "world", "k": 5}


def test_replace_placeholders_list():
    result = _replace_placeholders(["{input}", "static", 42], "test")
    assert result == ["test", "static", 42]


def test_replace_placeholders_nested():
    obj = {"outer": {"inner": "{input}"}, "list": ["{input}", 1]}
    result = _replace_placeholders(obj, "x")
    assert result == {"outer": {"inner": "x"}, "list": ["x", 1]}


def test_replace_placeholders_non_string_passthrough():
    assert _replace_placeholders(42, "x") == 42
    assert _replace_placeholders(3.14, "x") == 3.14
    assert _replace_placeholders(None, "x") is None
    assert _replace_placeholders(True, "x") is True


# ─── Script source ────────────────────────────────────────────────


def _make_script_fetcher(command="echo {input}", timeout=30):
    return ContextFetcher({"type": "script", "command": command, "timeout": timeout})


def test_script_fetch_success():
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = "retrieved context"

    with patch("src.context_source.subprocess.run", return_value=mock_proc) as mock_run:
        fetcher = _make_script_fetcher(command="myscript.sh {input}")
        result = fetcher.fetch("hello world")

    assert result == "retrieved context"
    mock_run.assert_called_once()
    call_args = mock_run.call_args
    # Input is shell-escaped
    assert "'hello world'" in call_args[0][0]


def test_script_input_shell_escaped():
    """Verify shell metacharacters in input are escaped."""
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = "ok"

    with patch("src.context_source.subprocess.run", return_value=mock_proc) as mock_run:
        fetcher = _make_script_fetcher(command="echo {input}")
        fetcher.fetch("hello; rm -rf /")

    call_args = mock_run.call_args[0][0]
    # The dangerous input should be quoted, not executed as separate command
    assert "rm -rf" not in call_args or "'" in call_args


def test_script_fetch_non_zero_exit():
    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.stderr = "script failed"

    with patch("src.context_source.subprocess.run", return_value=mock_proc):
        fetcher = _make_script_fetcher()
        with pytest.raises(ContextSourceError, match="exited with code 1"):
            fetcher.fetch("anything")


def test_script_fetch_timeout():
    with patch(
        "src.context_source.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="cmd", timeout=5),
    ):
        fetcher = _make_script_fetcher(timeout=5)
        with pytest.raises(ContextSourceError, match="timed out"):
            fetcher.fetch("anything")


# ─── HTTP source ──────────────────────────────────────────────────


def _make_http_fetcher(url="http://example.com/retrieve", method="POST", **kwargs):
    config = {"type": "http", "url": url, "method": method, **kwargs}
    return ContextFetcher(config)


def _mock_response(json_data=None, text="", status_code=200):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.text = text
    if json_data is not None:
        mock_resp.json.return_value = json_data
    else:
        mock_resp.json.side_effect = Exception("not json")
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


def test_http_post_success():
    resp = _mock_response(json_data={"context": "relevant info"})

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.return_value = resp

    with patch("src.context_source.httpx.Client", return_value=mock_client):
        fetcher = _make_http_fetcher(method="POST")
        result = fetcher.fetch("my question")

    mock_client.post.assert_called_once()
    assert "context" in result or result  # returns json dump of response


def test_http_get_success():
    resp = _mock_response(json_data="some context string")

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.return_value = resp

    with patch("src.context_source.httpx.Client", return_value=mock_client):
        fetcher = _make_http_fetcher(method="GET")
        result = fetcher.fetch("my query")

    mock_client.get.assert_called_once()
    assert result == "some context string"


def test_http_timeout():
    import httpx

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.side_effect = httpx.TimeoutException("timeout")

    with patch("src.context_source.httpx.Client", return_value=mock_client):
        fetcher = _make_http_fetcher()
        with pytest.raises(ContextSourceError, match="timed out"):
            fetcher.fetch("input")


def test_http_error_status():
    import httpx

    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"
    http_err = httpx.HTTPStatusError("500", request=MagicMock(), response=mock_resp)

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.side_effect = http_err

    with patch("src.context_source.httpx.Client", return_value=mock_client):
        fetcher = _make_http_fetcher()
        with pytest.raises(ContextSourceError, match="HTTP error 500"):
            fetcher.fetch("input")


def test_http_response_path_extraction():
    resp = _mock_response(json_data={"data": {"context": "deep value"}})

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.return_value = resp

    with patch("src.context_source.httpx.Client", return_value=mock_client):
        fetcher = _make_http_fetcher(response_path="data.context")
        result = fetcher.fetch("input")

    assert result == "deep value"


def test_http_response_path_missing_key():
    resp = _mock_response(json_data={"other": "stuff"})

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.return_value = resp

    with patch("src.context_source.httpx.Client", return_value=mock_client):
        fetcher = _make_http_fetcher(response_path="data.context")
        with pytest.raises(ContextSourceError, match="response_path"):
            fetcher.fetch("input")


# ─── Caching ──────────────────────────────────────────────────────


def test_caching_same_input_called_once():
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = "cached result"

    with patch("src.context_source.subprocess.run", return_value=mock_proc) as mock_run:
        fetcher = _make_script_fetcher()
        result1 = fetcher.fetch("same input")
        result2 = fetcher.fetch("same input")

    assert result1 == result2 == "cached result"
    assert mock_run.call_count == 1


def test_caching_different_inputs_called_twice():
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = "result"

    with patch("src.context_source.subprocess.run", return_value=mock_proc) as mock_run:
        fetcher = _make_script_fetcher()
        fetcher.fetch("input one")
        fetcher.fetch("input two")

    assert mock_run.call_count == 2


# ─── Unknown source type ──────────────────────────────────────────


def test_unknown_source_type_raises():
    fetcher = ContextFetcher({"type": "unknown"})
    with pytest.raises(ContextSourceError, match="Unknown source type"):
        fetcher.fetch("anything")


# ─── Security: URL scheme validation ────────────────────────────


def test_http_rejects_file_scheme():
    fetcher = _make_http_fetcher(url="file:///etc/passwd")
    with pytest.raises(ContextSourceError, match="not allowed"):
        fetcher.fetch("input")


def test_http_rejects_empty_scheme():
    fetcher = _make_http_fetcher(url="//internal-host/path")
    with pytest.raises(ContextSourceError, match="not allowed"):
        fetcher.fetch("input")


# ─── Security: timeout clamping ──────────────────────────────────


def test_timeout_clamped_to_max():
    fetcher = ContextFetcher({"type": "script", "command": "echo hi", "timeout": 9999})
    assert fetcher.timeout == MAX_TIMEOUT


def test_timeout_default_used_when_not_in_config():
    fetcher = ContextFetcher({"type": "script", "command": "echo hi"})
    assert fetcher.timeout == 30
