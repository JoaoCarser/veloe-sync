from __future__ import annotations

from typing import Any, Dict, List

from tqdm import tqdm

from src.config.settings import (
    HTTP_REQUEST_PAUSE_SECONDS,
    SHOW_PROGRESS,
    VELOE_VEHICLES_ENDPOINT,
    VELOE_VEHICLES_PAGE_SIZE,
)
from src.shared.logger import log_info, log_warn
from src.shared.normalize_text import normalize_text
from src.shared.retry import sleep_with_jitter
from src.veloe.api_client import build_auth_headers, request_json
from src.veloe.login import login_veloe


def _extract_vehicle_items(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(response, dict):
        return []
    for key in ("items", "data", "vehicles", "body"):
        value = response.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            for nested in ("items", "data", "vehicles"):
                nested_val = value.get(nested)
                if isinstance(nested_val, list):
                    return nested_val
    return []


def fetch_all_vehicles(session: Any, token: str) -> List[Dict[str, str]]:
    all_rows: List[Dict[str, str]] = []
    page = 0
    progress_bar = tqdm(desc="Buscando veiculos", unit="pagina", disable=not SHOW_PROGRESS)

    try:
        while True:
            response = request_json(
                session=session,
                method="GET",
                url=VELOE_VEHICLES_ENDPOINT,
                headers=build_auth_headers(token),
                params={"pageSize": VELOE_VEHICLES_PAGE_SIZE, "pageNumber": page},
            )

            items = _extract_vehicle_items(response)
            if not items:
                log_info(f"Pagina {page}: sem registros, finalizando busca de veiculos")
                break

            for item in items:
                all_rows.append({
                    "plate": normalize_text(item.get("plate")),
                    "baseName": normalize_text(item.get("baseName")),
                    "model": normalize_text(item.get("model")),
                    "status": normalize_text(item.get("status")),
                })

            log_info(f"Veiculos pagina {page}: {len(items)} registros")
            progress_bar.update(1)

            if len(items) < VELOE_VEHICLES_PAGE_SIZE:
                break

            page += 1
            sleep_with_jitter(HTTP_REQUEST_PAUSE_SECONDS)
    finally:
        progress_bar.close()

    log_info(f"Total de veiculos: {len(all_rows)}")
    return all_rows
