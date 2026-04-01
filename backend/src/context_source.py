"""
Context source: fetch dynamic context for test cases from external sources.

Supports two source types:
- script: run a shell command with {input} substitution, capture stdout
- http: call an HTTP endpoint with {input} substitution in request body/params

Security note: script mode executes shell commands configured by the tool operator.
This is intentional for a self-hosted developer tool. The {input} placeholder is
shell-escaped to prevent test case inputs from becoming an injection vector.
"""

import hashlib
import shlex
import subprocess
import json
from urllib.parse import urlparse

import httpx


MAX_TIMEOUT = 120

ALLOWED_URL_SCHEMES = {"http", "https"}


class ContextSourceError(Exception):
    """Raised when context fetching fails."""
    pass


def _replace_placeholders(obj, input_text: str):
    """Recursively replace {input} placeholder in str/dict/list."""
    if isinstance(obj, str):
        return obj.replace("{input}", input_text)
    if isinstance(obj, dict):
        return {k: _replace_placeholders(v, input_text) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_replace_placeholders(item, input_text) for item in obj]
    return obj


class ContextFetcher:
    def __init__(self, config: dict, timeout: int = 30):
        self.source_type = config.get("type")  # "script" or "http"
        self.config = config
        self.timeout = min(config.get("timeout", timeout), MAX_TIMEOUT)
        self._cache: dict[str, str] = {}

    def fetch(self, input_text: str) -> str:
        cache_key = hashlib.sha256(input_text.encode()).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]

        if self.source_type == "script":
            result = self._fetch_script(input_text)
        elif self.source_type == "http":
            result = self._fetch_http(input_text)
        else:
            raise ContextSourceError(f"Unknown source type: {self.source_type!r}")

        self._cache[cache_key] = result
        return result

    def _fetch_script(self, input_text: str) -> str:
        command = self.config.get("command", "")
        # Shell-escape the input to prevent injection via test case content
        safe_input = shlex.quote(input_text)
        command = command.replace("{input}", safe_input)

        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired as e:
            raise ContextSourceError(f"Script timed out after {self.timeout}s") from e

        if proc.returncode != 0:
            raise ContextSourceError(
                f"Script exited with code {proc.returncode}: {proc.stderr.strip()}"
            )

        return proc.stdout

    def _fetch_http(self, input_text: str) -> str:
        url = self.config.get("url", "")
        parsed = urlparse(url)
        if parsed.scheme not in ALLOWED_URL_SCHEMES:
            raise ContextSourceError(
                f"URL scheme {parsed.scheme!r} not allowed. Use http or https."
            )
        method = self.config.get("method", "POST").upper()
        headers = self.config.get("headers", {})
        body_template = self.config.get("body_template")
        response_path = self.config.get("response_path")

        headers = _replace_placeholders(headers, input_text)

        try:
            with httpx.Client(timeout=self.timeout) as client:
                if method == "GET":
                    params = _replace_placeholders(
                        self.config.get("params", {"input": "{input}"}),
                        input_text,
                    )
                    response = client.get(url, headers=headers, params=params)
                else:
                    if body_template is not None:
                        body = _replace_placeholders(body_template, input_text)
                    else:
                        body = {"input": input_text}
                    response = client.post(url, headers=headers, json=body)

                response.raise_for_status()

        except httpx.TimeoutException as e:
            raise ContextSourceError(f"HTTP request timed out after {self.timeout}s") from e
        except httpx.HTTPStatusError as e:
            raise ContextSourceError(
                f"HTTP error {e.response.status_code}: {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            raise ContextSourceError(f"HTTP request failed: {e}") from e

        try:
            data = response.json()
        except Exception:
            return response.text

        if response_path:
            try:
                for key in response_path.split("."):
                    data = data[key]
                return str(data)
            except (KeyError, TypeError, IndexError) as e:
                raise ContextSourceError(
                    f"Could not extract response_path {response_path!r}: {e}"
                ) from e

        if isinstance(data, str):
            return data
        return json.dumps(data)
