from __future__ import annotations

from typing import Any, Dict

import requests

from src.config.settings import HTTP_REQUEST_TIMEOUT, N8N_SUMMARY_WEBHOOK_URL
from src.shared.logger import log_info, log_warn


def send_summary_to_n8n(summary: Dict[str, Any]) -> None:
    if not N8N_SUMMARY_WEBHOOK_URL:
        log_warn("N8N_SUMMARY_WEBHOOK_URL nao configurada, pulando envio do webhook")
        return

    response = requests.post(
        N8N_SUMMARY_WEBHOOK_URL,
        json=summary,
        timeout=HTTP_REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    log_info(f"Webhook summary enviado | status={response.status_code}")
