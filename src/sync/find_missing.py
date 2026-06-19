from __future__ import annotations

from typing import Dict, List

from src.shared.normalize_text import normalize_compare_key


def find_missing_ids(
    veloe_supplies: List[Dict[str, str]],
    monday_item_names: List[str],
) -> List[Dict[str, str]]:
    """Retorna abastecimentos da Veloe que não existem no Monday."""
    monday_keys = {normalize_compare_key(n) for n in monday_item_names if n}
    return [
        s for s in veloe_supplies
        if normalize_compare_key(s.get("id", "")) not in monday_keys
    ]
