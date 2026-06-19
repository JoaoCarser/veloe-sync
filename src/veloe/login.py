from __future__ import annotations

from typing import Optional

import pandas as pd
from requests import Session

from src.config.settings import VELOE_CLIENT_ID, VELOE_CLIENT_SECRET, VELOE_LOGIN_ENDPOINT, VELOE_TOKEN_TTL_MINUTES
from src.shared.logger import log_info, log_error
from src.shared.normalize_text import normalize_text
from src.veloe.api_client import get_login_headers, request_json

_access_token: str = ""
_token_expires_at: Optional[pd.Timestamp] = None


def _set_access_token(token: str) -> None:
    global _access_token, _token_expires_at
    _access_token = normalize_text(token)
    _token_expires_at = pd.Timestamp.utcnow() + pd.Timedelta(minutes=VELOE_TOKEN_TTL_MINUTES)


def get_access_token() -> str:
    return _access_token


def _token_is_valid() -> bool:
    if not _access_token:
        return False
    if _token_expires_at is None:
        return False
    return pd.Timestamp.utcnow() < _token_expires_at


def _do_login(session: Session) -> str:
    if not VELOE_CLIENT_ID or not VELOE_CLIENT_SECRET:
        raise ValueError("VELOE_CLIENT_ID e VELOE_CLIENT_SECRET devem estar configurados no .env")

    response = request_json(
        session=session,
        method="POST",
        url=VELOE_LOGIN_ENDPOINT,
        headers=get_login_headers(),
        json_body={"clientId": VELOE_CLIENT_ID, "clientSecret": VELOE_CLIENT_SECRET},
    )

    body = response.get("body", {}) if isinstance(response, dict) else {}
    access_token = normalize_text(body.get("accessToken"))
    if not access_token:
        raise RuntimeError("Login nao retornou accessToken")

    return access_token


def login_veloe(session: Session) -> str:
    if _token_is_valid():
        log_info("Token ja valido, reutilizando")
        return _access_token

    log_info("Autenticando na API Veloe/Alelo...")
    try:
        token = _do_login(session)
        _set_access_token(token)
        log_info(f"Login OK | token={token[:4]}...{token[-6:]}")
        return _access_token
    except Exception as exc:
        log_error(f"Falha no login Veloe: {exc}")
        raise
