from __future__ import annotations

from typing import Dict, List, Set

from src.shared.logger import log_info
from src.shared.normalize_text import normalize_compare_key


def find_orphans(
    monday_items: List[Dict[str, str]],
    veloe_ids: Set[str],
) -> List[Dict[str, str]]:
    """
    Identifica itens que existem no Monday mas cujo id_veloe
    não está presente na Veloe dentro do período consultado.
    """
    orphans = [
        item for item in monday_items
        if normalize_compare_key(item.get("id_veloe", "")) not in veloe_ids
        and normalize_compare_key(item.get("id_veloe", "")) != ""
    ]
    log_info(f"Orphans encontrados: {len(orphans)}")
    return orphans
