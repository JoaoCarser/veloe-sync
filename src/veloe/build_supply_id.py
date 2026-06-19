from __future__ import annotations

from src.shared.normalize_text import normalize_text, parse_supply_date


def build_supply_id(vehicle_plate: str, authorization: str, transaction_date: str) -> str:
    plate = normalize_text(vehicle_plate)
    auth = normalize_text(authorization)
    date_iso = parse_supply_date(transaction_date)
    return f"{plate} - {auth} - {date_iso}"
