# app/services/judge0_client.py
from __future__ import annotations

import time
from typing import Any, Optional, Dict

import httpx

from app.config import get_settings

settings = get_settings()

# Judge0 status IDs:
# 1: In Queue, 2: Processing, >=3: Done (Accepted/WA/CE/etc)
_PROCESSING_STATUS_IDS = {1, 2}

DEFAULT_LANGUAGE_ID = 71  # Python (Judge0)
DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_POLL_INTERVAL_SECONDS = 0.8
DEFAULT_MAX_INTERVAL_SECONDS = 2.0


class Judge0ClientError(Exception):
    """Non-fatal client error (network, parsing, server errors)."""


def _headers() -> Dict[str, str]:
    """
    Uses RapidAPI headers if present.
    If you later move to self-hosted Judge0 CE, adjust headers here.
    """
    headers = {"Content-Type": "application/json"}

    api_key = getattr(settings, "judge0_api_key", None)
    rapid_host = getattr(settings, "judge0_rapidapi_host", None)

    if api_key:
        headers["X-RapidAPI-Key"] = api_key
    if rapid_host:
        headers["X-RapidAPI-Host"] = rapid_host

    return headers


def submit_code(source_code: str, stdin: str | None = None) -> str:
    """
    Send POST request to Judge0 /submissions and return execution token.
    """
    base_url = getattr(settings, "judge0_base_url", None)
    if not base_url:
        raise Judge0ClientError("JUDGE0_BASE_URL is not configured")

    language_id = getattr(settings, "judge0_language_id", DEFAULT_LANGUAGE_ID)

    url = f"{base_url.rstrip('/')}/submissions?base64_encoded=false&wait=false"

    payload: Dict[str, Any] = {
        "language_id": language_id,
        "source_code": source_code,
    }
    if stdin is not None:
        payload["stdin"] = stdin

    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(url, json=payload, headers=_headers())
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as e:
        raise Judge0ClientError(f"HTTP error submitting to Judge0: {e}") from e
    except ValueError as e:
        raise Judge0ClientError("Invalid JSON response from Judge0 (submit)") from e

    token = data.get("token")
    if not token or not isinstance(token, str):
        raise Judge0ClientError(f"Judge0 submit returned no token: {data}")

    return token


def poll_result(token: str) -> dict:
    """
    Poll Judge0 /submissions/{token} until completion or timeout.
    Returns structured result dict:
    {
      "stdout": "...",
      "stderr": "...",
      "status": "...",
      "time": "...",
      "memory": "..."
    }
    """
    base_url = getattr(settings, "judge0_base_url", None)
    if not base_url:
        return _failure_result("JUDGE0_BASE_URL is not configured")

    timeout_seconds = getattr(settings, "judge0_poll_timeout_seconds", DEFAULT_TIMEOUT_SECONDS)
    poll_interval = getattr(settings, "judge0_poll_interval_seconds", DEFAULT_POLL_INTERVAL_SECONDS)
    max_interval = getattr(settings, "judge0_poll_max_interval_seconds", DEFAULT_MAX_INTERVAL_SECONDS)

    url = f"{base_url.rstrip('/')}/submissions/{token}?base64_encoded=false"

    start = time.time()
    interval = float(poll_interval)

    try:
        with httpx.Client(timeout=10.0) as client:
            while True:
                # timeout check
                if (time.time() - start) > float(timeout_seconds):
                    return _failure_result("Judge0 polling timeout exceeded")

                r = client.get(url, headers=_headers())
                # Handle invalid token or server errors gracefully
                if r.status_code == 404:
                    return _failure_result("Judge0 token not found (404)")
                if r.status_code >= 500:
                    return _failure_result(f"Judge0 server error ({r.status_code})")
                if r.status_code >= 400:
                    return _failure_result(f"Judge0 HTTP error ({r.status_code})")

                data = r.json()

                status = _parse_status(data)
                if status is None:
                    return _failure_result("Unexpected Judge0 response structure (missing status)")

                status_id = status.get("id")
                if status_id in _PROCESSING_STATUS_IDS:
                    time.sleep(interval)
                    interval = min(interval * 1.25, max_interval)  # gentle backoff
                    continue

                return _structured_result(data)

    except httpx.HTTPError as e:
        return _failure_result(f"HTTP error polling Judge0: {e}")
    except ValueError:
        return _failure_result("Invalid JSON response from Judge0 (poll)")
    except Exception as e:
        # Never crash worker
        return _failure_result(f"Unexpected error polling Judge0: {e}")


def _parse_status(data: dict) -> Optional[dict]:
    status = data.get("status")
    if isinstance(status, dict) and "id" in status:
        return status
    return None


def _structured_result(data: dict) -> dict:
    status = data.get("status") or {}
    return {
        "stdout": data.get("stdout") or "",
        "stderr": data.get("stderr") or "",
        "status": status.get("description") or "Unknown",
        "time": data.get("time"),
        "memory": data.get("memory"),
    }


def _failure_result(message: str) -> dict:
    return {
        "stdout": "",
        "stderr": message,
        "status": "failed",
        "time": None,
        "memory": None,
    }
