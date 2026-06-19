from __future__ import annotations

from typing import List

from src.config.settings import HTTP_REQUEST_PAUSE_SECONDS
from src.shared.logger import log_info, log_error
from src.shared.normalize_text import normalize_text
from src.shared.retry import sleep_with_jitter
from src.monday.api_client import execute_monday_query


def delete_item(item_id: str) -> None:
    mutation = """
    mutation ($item_id: ID!) {
      delete_item(item_id: $item_id) { id }
    }
    """
    execute_monday_query(mutation, {"item_id": item_id}, f"delete_item_{item_id}")


def delete_items(item_ids: List[str], label: str = "item") -> int:
    """Deleta itens pelo ID Monday. Retorna a quantidade removida."""
    removed = 0
    for item_id in item_ids:
        iid = normalize_text(item_id)
        if not iid:
            continue
        try:
            delete_item(iid)
            log_info(f"Apagado {label} | id_monday={iid}")
            removed += 1
            sleep_with_jitter(HTTP_REQUEST_PAUSE_SECONDS)
        except Exception as exc:
            log_error(f"Falha ao apagar {label} | id_monday={iid} | erro={exc}")
    return removed
