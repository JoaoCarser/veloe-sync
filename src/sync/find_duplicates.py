from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List

from src.shared.logger import log_info
from src.shared.normalize_text import normalize_compare_key, normalize_text


def find_duplicates(monday_items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Identifica itens duplicados no Monday (mesmo id_veloe).
    Regra: manter o menor id_monday numérico; marcar os demais para deleção.
    Retorna lista dos itens a serem apagados (com keep_flag=False).
    """
    groups: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for item in monday_items:
        key = normalize_compare_key(item.get("id_veloe", ""))
        if key:
            groups[key].append(item)

    to_delete: List[Dict[str, str]] = []
    for key, group in groups.items():
        if len(group) <= 1:
            continue

        def _sort_key(it: Dict[str, str]) -> Any:
            mid = normalize_text(it.get("id_monday", ""))
            try:
                return int(mid)
            except ValueError:
                return float("inf")

        sorted_group = sorted(group, key=_sort_key)
        # manter o primeiro (menor id_monday), apagar os demais
        for dup in sorted_group[1:]:
            to_delete.append(dup)

    log_info(f"Duplicados encontrados para apagar: {len(to_delete)}")
    return to_delete
