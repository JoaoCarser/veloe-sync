from __future__ import annotations

from src.shared.normalize_text import normalize_compare_key, normalize_text


def parse_item_name(name: object) -> str:
    """Normaliza o name de um item Monday para comparação com o ID técnico Veloe."""
    return normalize_compare_key(normalize_text(name))
