from __future__ import annotations

from typing import Any, Dict, List, Optional

from tqdm import tqdm

from src.config.settings import (
    HTTP_REQUEST_PAUSE_SECONDS,
    SHOW_PROGRESS,
    VELOE_SUPPLY_BATCH_SIZE,
    VELOE_SUPPLY_HISTORY_ENDPOINT,
    VELOE_SUPPLY_WINDOW_DAYS,
)
from src.shared.chunks import chunk_list
from src.shared.logger import log_info, log_warn
from src.shared.normalize_text import normalize_text
from src.shared.retry import sleep_with_jitter
from src.veloe.api_client import build_auth_headers, request_json
from src.veloe.date_periods import generate_date_windows
from src.veloe.map_supply_data import normalize_supply_id_row


def _extract_items(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(response, dict):
        return []
    body = response.get("body", [])
    return body if isinstance(body, list) else []


def _extract_records_count(response: Dict[str, Any]) -> int:
    if not isinstance(response, dict):
        return 0
    val = response.get("recordsCount", 0)
    if isinstance(val, int):
        return val
    if isinstance(val, str) and val.isdigit():
        return int(val)
    return 0


def _build_payload(
    plates: List[str], start: str, end: str, page: int, size: int
) -> Dict[str, Any]:
    return {
        "vehiclePlates": plates,
        "startDate": start,
        "endDate": end,
        "pageNumber": page,
        "pageSize": size,
    }


def fetch_supplies(
    session: Any,
    token: str,
    vehicles: List[Dict[str, str]],
    period: Dict[str, str],
) -> List[Dict[str, str]]:
    """Busca IDs técnicos de todos os abastecimentos do semestre."""
    start_date = period["start_date"]
    end_date = period["end_date"]
    yesterday_date = period["yesterday_date"]

    plates = [normalize_text(v.get("plate", "")) for v in vehicles]
    plates = [p for p in plates if p]
    if not plates:
        log_warn("Nenhuma placa encontrada para busca de supply")
        return []

    plate_batches = chunk_list(plates, VELOE_SUPPLY_BATCH_SIZE)
    date_windows = generate_date_windows(start_date, end_date, VELOE_SUPPLY_WINDOW_DAYS)
    all_rows: List[Dict[str, str]] = []

    progress_bar = tqdm(
        total=len(plate_batches) * len(date_windows),
        desc="Buscando supply IDs",
        unit="req",
        disable=not SHOW_PROGRESS,
    )

    try:
        for batch_idx, plate_batch in enumerate(plate_batches, 1):
            for win_idx, (win_start, win_end) in enumerate(date_windows, 1):
                fallback_end = yesterday_date if win_end == end_date else None
                attempts = [(win_start, win_end)]
                if fallback_end and fallback_end != win_end:
                    attempts.append((win_start, fallback_end))

                window_ok = False
                last_exc: Optional[Exception] = None

                for att_idx, (att_start, att_end) in enumerate(attempts, 1):
                    page = 0
                    attempt_rows: List[Dict[str, str]] = []
                    try:
                        while True:
                            response = request_json(
                                session=session,
                                method="POST",
                                url=VELOE_SUPPLY_HISTORY_ENDPOINT,
                                headers=build_auth_headers(token),
                                json_body=_build_payload(plate_batch, att_start, att_end, page, 500),
                            )

                            items = _extract_items(response)
                            records_count = _extract_records_count(response)

                            if not items:
                                log_info(
                                    f"Supply IDs | lote {batch_idx}/{len(plate_batches)} "
                                    f"janela {win_idx}/{len(date_windows)} pag {page}: sem registros"
                                )
                                break

                            for item in items:
                                attempt_rows.append(normalize_supply_id_row(item))

                            log_info(
                                f"Supply IDs | lote {batch_idx}/{len(plate_batches)} "
                                f"janela {win_idx}/{len(date_windows)} pag {page}: "
                                f"{len(items)} registros | rc={records_count}"
                            )
                            sleep_with_jitter(HTTP_REQUEST_PAUSE_SECONDS)

                            if len(items) < 500:
                                break
                            page += 1

                        all_rows.extend(attempt_rows)
                        window_ok = True
                        break

                    except Exception as exc:
                        last_exc = exc
                        if att_idx == 1 and fallback_end and (
                            "400" in str(exc) or "Bad Request" in str(exc)
                        ):
                            log_warn(
                                f"Supply IDs fallback | lote {batch_idx} janela {win_idx} "
                                f"-> usando endDate={fallback_end}"
                            )
                            continue
                        raise

                if not window_ok and last_exc:
                    raise last_exc

                progress_bar.update(1)
    finally:
        progress_bar.close()

    log_info(f"Total de IDs Veloe carregados: {len(all_rows)}")
    return all_rows
