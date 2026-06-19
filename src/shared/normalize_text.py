from __future__ import annotations

from typing import Any, Optional

import pandas as pd


def is_blank(value: Any) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return str(value).strip() == ""


def normalize_text(value: Any) -> str:
    return "" if is_blank(value) else str(value).strip()


def normalize_upper(value: Any) -> str:
    return normalize_text(value).upper()


def normalize_lower(value: Any) -> str:
    return normalize_text(value).lower()


def normalize_compare_key(value: Any) -> str:
    return normalize_text(value).strip().lower()


def to_float_br(value: Any) -> Optional[float]:
    if is_blank(value):
        return None
    text = normalize_text(value).replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def to_int_safe(value: Any) -> Optional[int]:
    if is_blank(value):
        return None
    try:
        return int(float(normalize_text(value).replace(",", ".")))
    except ValueError:
        return None


def normalize_monday_number(value: Any) -> Optional[float]:
    if is_blank(value):
        return None
    if isinstance(value, (int, float)):
        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass
        return float(value)
    return to_float_br(value)


def parse_supply_date(value: Any) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y"):
        try:
            return pd.to_datetime(text, format=fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    parsed = pd.to_datetime(text, errors="coerce", dayfirst=True)
    if pd.isna(parsed):
        return text
    return parsed.strftime("%Y-%m-%d")
