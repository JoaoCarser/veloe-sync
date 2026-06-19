from __future__ import annotations

from typing import Any, Dict, Optional

import requests
from requests import Response, Session

from src.config.settings import (
    HTTP_MAX_RETRIES,
    HTTP_REQUEST_TIMEOUT,
    VELOE_AUTHORIZATION_PREFIX,
    VELOE_CLIENT_ID,
    VELOE_CLIENT_SECRET,
    VELOE_CONTRACT,
)
from src.shared.retry import (
    build_backoff_delay,
    should_retry_exception,
    should_retry_http_status,
    sleep_with_jitter,
)

_LOGIN_HEADERS: Dict[str, str] = {
    "x-ibm-client-id": VELOE_CLIENT_ID,
    "x-ibm-client-secret": VELOE_CLIENT_SECRET,
    "ClientId": VELOE_CLIENT_ID,
    "Content-Type": "application/json",
}

_BASE_AUTH_HEADERS: Dict[str, str] = {
    "x-ibm-client-id": VELOE_CLIENT_ID,
    "x-ibm-client-secret": VELOE_CLIENT_SECRET,
    "ClientId": VELOE_CLIENT_ID,
    "contract": VELOE_CONTRACT,
    "Accept": "*/*",
    "Content-Type": "application/json",
}


def get_login_headers() -> Dict[str, str]:
    return dict(_LOGIN_HEADERS)


def build_auth_headers(access_token: str) -> Dict[str, str]:
    headers = dict(_BASE_AUTH_HEADERS)
    if access_token:
        prefix = VELOE_AUTHORIZATION_PREFIX
        headers["Authorization"] = f"{prefix} {access_token}" if prefix else access_token
    return headers


def create_veloe_session() -> Session:
    session = requests.Session()
    session.headers.update(_BASE_AUTH_HEADERS)
    return session


def request_json(
    session: Session,
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    last_error: Optional[Exception] = None

    for attempt in range(HTTP_MAX_RETRIES):
        try:
            response: Response = session.request(
                method=method,
                url=url,
                headers=headers,
                json=json_body,
                params=params,
                timeout=HTTP_REQUEST_TIMEOUT,
            )

            if should_retry_http_status(response.status_code):
                last_error = RuntimeError(f"HTTP {response.status_code}")
                sleep_with_jitter(build_backoff_delay(attempt))
                continue

            response.raise_for_status()
            return response.json()

        except Exception as exc:
            last_error = exc
            if attempt == HTTP_MAX_RETRIES - 1 or not should_retry_exception(exc):
                raise
            sleep_with_jitter(build_backoff_delay(attempt))

    if last_error:
        raise last_error
    raise RuntimeError("request_json falhou sem excecao explicita")
