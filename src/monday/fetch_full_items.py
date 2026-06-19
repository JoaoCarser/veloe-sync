from __future__ import annotations

from typing import Any, Dict, List

from src.config.settings import MONDAY_BOARD_ID, MONDAY_BOARD_NAME, MONDAY_PAGE_SIZE
from src.shared.logger import log_info
from src.shared.normalize_text import normalize_text
from src.monday.api_client import query_board_items_paginated


def fetch_full_items() -> List[Dict[str, str]]:
    """Busca id + name de todos os itens atuais do board (usado após criação)."""
    raw = query_board_items_paginated(
        board_id=MONDAY_BOARD_ID,
        fields="id name",
        limit=MONDAY_PAGE_SIZE,
        board_name=MONDAY_BOARD_NAME,
    )

    items = [
        {
            "id_monday": normalize_text(item.get("id")),
            "id_veloe": normalize_text(item.get("name")),
        }
        for item in raw
        if normalize_text(item.get("id"))
    ]

    log_info(f"Total de itens Monday (pos-create): {len(items)}")
    return items
