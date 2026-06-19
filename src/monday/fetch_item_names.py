from __future__ import annotations

from typing import List

from src.config.settings import MONDAY_BOARD_ID, MONDAY_BOARD_NAME, MONDAY_PAGE_SIZE
from src.shared.logger import log_info
from src.shared.normalize_text import normalize_text
from src.monday.api_client import query_board_items_paginated


def fetch_existing_item_names() -> List[str]:
    """Busca apenas os names dos itens do board para comparação rápida com Veloe."""
    raw = query_board_items_paginated(
        board_id=MONDAY_BOARD_ID,
        fields="id name",
        limit=MONDAY_PAGE_SIZE,
        board_name=MONDAY_BOARD_NAME,
    )

    names = [normalize_text(item.get("name")) for item in raw]
    names = [n for n in names if n]
    log_info(f"Total de nomes Monday carregados: {len(names)}")
    return names
