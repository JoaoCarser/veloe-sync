from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from src.shared.logger import log_info
from src.shared.normalize_text import normalize_compare_key


@dataclass
class ComparisonResult:
    missing_supplies: List[Dict[str, str]]
    veloe_total: int
    monday_initial_total: int
    new_ids_found: int


def compare_veloe_with_monday(
    veloe_supplies: List[Dict[str, str]],
    monday_item_names: List[str],
) -> ComparisonResult:
    """Compara IDs técnicos da Veloe com names dos itens no Monday."""
    monday_keys = {normalize_compare_key(name) for name in monday_item_names if name}

    missing: List[Dict[str, str]] = []
    for supply in veloe_supplies:
        veloe_key = normalize_compare_key(supply.get("id", ""))
        if veloe_key and veloe_key not in monday_keys:
            missing.append(supply)

    log_info(f"Veloe total: {len(veloe_supplies)}")
    log_info(f"Monday inicial: {len(monday_item_names)}")
    log_info(f"Novos IDs para criar: {len(missing)}")

    return ComparisonResult(
        missing_supplies=missing,
        veloe_total=len(veloe_supplies),
        monday_initial_total=len(monday_item_names),
        new_ids_found=len(missing),
    )
