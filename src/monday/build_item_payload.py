from __future__ import annotations

import json
from typing import Any, Dict, List

from src.config.settings import MONDAY_BOARD_ID, MONDAY_COLUMN_MAP, MONDAY_DATE_COLUMNS, MONDAY_NUMERIC_COLUMNS
from src.shared.normalize_text import is_blank, normalize_monday_number, normalize_text, parse_supply_date
from src.veloe.map_supply_data import prepare_supply_for_monday


def _build_column_values(row: Dict[str, Any]) -> Dict[str, Any]:
    column_values: Dict[str, Any] = {}

    for source_col, monday_col_id in MONDAY_COLUMN_MAP.items():
        if source_col == "name":
            continue

        value = row.get(source_col)
        if is_blank(value):
            continue

        if source_col in MONDAY_DATE_COLUMNS:
            date_val = parse_supply_date(value)
            if date_val:
                column_values[monday_col_id] = date_val
        elif source_col in MONDAY_NUMERIC_COLUMNS:
            num_val = normalize_monday_number(value)
            if num_val is not None:
                column_values[monday_col_id] = num_val
        else:
            text_val = normalize_text(value)
            if text_val:
                column_values[monday_col_id] = text_val

    return column_values


def build_item_payloads(full_supplies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Monta a lista de payloads prontos para criação no Monday."""
    payloads: List[Dict[str, Any]] = []

    for supply in full_supplies:
        ready = prepare_supply_for_monday(supply)
        technical_id = normalize_text(ready.get("id"))
        if not technical_id:
            continue

        column_values = _build_column_values(ready)
        payloads.append({
            "board_id": MONDAY_BOARD_ID,
            "item_name": technical_id,
            "column_values_json": json.dumps(column_values, ensure_ascii=False),
            "technical_id": technical_id,
        })

    return payloads
