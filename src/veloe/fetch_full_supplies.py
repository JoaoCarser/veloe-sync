from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
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
from src.shared.normalize_text import normalize_compare_key, normalize_text
from src.shared.retry import sleep_with_jitter
from src.veloe.api_client import build_auth_headers, request_json
from src.veloe.date_periods import generate_date_windows
from src.veloe.map_supply_data import normalize_supply_full_row


def _build_supply_recovery_plan(
    missing_supplies: List[Dict[str, str]],
    end_date: str,
) -> List[Dict[str, Any]]:
    """Organiza os IDs novos em janelas de datas + lotes de placas para reconsulta."""
    valid = [s for s in missing_supplies if normalize_text(s.get("id")) and normalize_text(s.get("date"))]
    if not valid:
        return []

    dates = [pd.to_datetime(s["date"], errors="coerce") for s in valid]
    min_date_str = min(d for d in dates if not pd.isna(d)).strftime("%d/%m/%Y")

    date_windows = generate_date_windows(min_date_str, end_date, VELOE_SUPPLY_WINDOW_DAYS)
    plan: List[Dict[str, Any]] = []

    for win_idx, (win_start, win_end) in enumerate(date_windows, 1):
        win_start_ts = pd.to_datetime(win_start, dayfirst=True)
        win_end_ts = pd.to_datetime(win_end, dayfirst=True)

        window_items = [
            s for s in valid
            if win_start_ts <= pd.to_datetime(s["date"], errors="coerce") <= win_end_ts
        ]
        if not window_items:
            continue

        plates = sorted({normalize_text(s.get("placa", "")) for s in window_items if normalize_text(s.get("placa", ""))})
        plate_batches = chunk_list(plates, VELOE_SUPPLY_BATCH_SIZE)

        for bat_idx, plate_batch in enumerate(plate_batches, 1):
            batch_items = [s for s in window_items if normalize_text(s.get("placa", "")) in plate_batch]
            target_ids = [normalize_text(s["id"]) for s in batch_items if normalize_text(s.get("id"))]
            plan.append({
                "plan_id": f"W{win_idx:03d}_B{bat_idx:02d}",
                "window_start": win_start,
                "window_end": win_end,
                "vehiclePlates": plate_batch,
                "target_ids": target_ids,
            })

    log_info(f"Plano de reconsulta: {len(plan)} janelas preparadas")
    return plan


def fetch_full_supplies(
    session: Any,
    token: str,
    missing_supplies: List[Dict[str, str]],
    period: Dict[str, str],
) -> Dict[str, Any]:
    """Busca dados completos dos abastecimentos novos identificados na comparação."""
    end_date = period["end_date"]
    yesterday_date = period["yesterday_date"]

    if not missing_supplies:
        log_warn("Nenhum abastecimento novo para reconsultar")
        return {"items": [], "fallback_used": False}

    plan = _build_supply_recovery_plan(missing_supplies, end_date)
    if not plan:
        log_warn("Plano de reconsulta vazio")
        return {"items": [], "fallback_used": False}

    target_ids = {
        normalize_compare_key(tid)
        for row in plan
        for tid in row.get("target_ids", [])
        if normalize_compare_key(tid)
    }

    all_rows: List[Dict[str, Any]] = []
    fallback_used = False
    progress_bar = tqdm(total=len(plan), desc="Buscando supply completo", unit="janela", disable=not SHOW_PROGRESS)

    try:
        for plan_row in plan:
            plates = plan_row["vehiclePlates"]
            win_start = plan_row["window_start"]
            win_end = plan_row["window_end"]
            fallback_end = yesterday_date if win_end == end_date else None

            attempts = [(win_start, win_end)]
            if fallback_end and fallback_end != win_end:
                attempts.append((win_start, fallback_end))

            window_ok = False
            last_exc: Optional[Exception] = None

            for att_idx, (att_start, att_end) in enumerate(attempts, 1):
                page = 0
                attempt_rows: List[Dict[str, Any]] = []
                try:
                    while True:
                        payload = {
                            "vehiclePlates": plates,
                            "startDate": att_start,
                            "endDate": att_end,
                            "pageNumber": page,
                            "pageSize": 500,
                        }
                        response = request_json(
                            session=session,
                            method="POST",
                            url=VELOE_SUPPLY_HISTORY_ENDPOINT,
                            headers=build_auth_headers(token),
                            json_body=payload,
                        )

                        items = response.get("body", []) if isinstance(response, dict) else []
                        if not isinstance(items, list):
                            items = []

                        if not items:
                            log_info(f"Supply completo | {plan_row['plan_id']} pag {page}: sem registros")
                            break

                        for item in items:
                            supply_row = normalize_supply_full_row(item)
                            if not target_ids or normalize_compare_key(supply_row["id"]) in target_ids:
                                attempt_rows.append(supply_row)

                        log_info(
                            f"Supply completo | {plan_row['plan_id']} pag {page}: "
                            f"{len(items)} registros | filtrados={len(attempt_rows)}"
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
                        fallback_used = True
                        log_warn(
                            f"Supply completo fallback | {plan_row['plan_id']} "
                            f"-> usando endDate={fallback_end}"
                        )
                        continue
                    raise

            if not window_ok and last_exc:
                raise last_exc

            progress_bar.update(1)
    finally:
        progress_bar.close()

    log_info(f"Total de abastecimentos completos: {len(all_rows)}")
    return {"items": all_rows, "fallback_used": fallback_used}
