from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List

from tqdm import tqdm

from src.config.settings import HTTP_REQUEST_PAUSE_SECONDS, MONDAY_BOARD_ID, PIPELINE_CREATE_DRY_RUN, SHOW_PROGRESS
from src.shared.logger import log_error, log_info, log_warn
from src.shared.normalize_text import normalize_text
from src.shared.retry import sleep_with_jitter
from src.monday.api_client import execute_monday_query


@dataclass
class CreationResult:
    created_ok: int
    create_errors: int


def _get_default_group_id(board_id: str) -> str:
    query = """
    query ($board_id: [ID!]) {
      boards(ids: $board_id) {
        groups { id title }
      }
    }
    """
    data = execute_monday_query(query, {"board_id": [board_id]}, "get_default_group")
    boards = data.get("boards", [])
    if not boards:
        raise RuntimeError("Nenhum board retornado ao buscar grupos")
    groups = boards[0].get("groups", [])
    if not groups:
        raise RuntimeError("Nenhum grupo encontrado no board Monday")
    group_id = normalize_text(groups[0].get("id"))
    if not group_id:
        raise RuntimeError("Grupo padrao sem id valido")
    return group_id


def _create_single_item(board_id: str, group_id: str, item_name: str, column_values: Dict[str, Any]) -> str:
    mutation = """
    mutation ($board_id: ID!, $group_id: String!, $item_name: String!, $column_values: JSON!) {
      create_item(
        board_id: $board_id,
        group_id: $group_id,
        item_name: $item_name,
        column_values: $column_values
      ) { id }
    }
    """
    data = execute_monday_query(
        mutation,
        {
            "board_id": board_id,
            "group_id": group_id,
            "item_name": item_name,
            "column_values": json.dumps(column_values, ensure_ascii=False),
        },
        f"create_item_{item_name[:40]}",
    )
    item_id = normalize_text((data.get("create_item") or {}).get("id"))
    if not item_id:
        raise RuntimeError(f"Monday nao retornou id para o item criado: {item_name}")
    return item_id


def create_items(payloads: List[Dict[str, Any]]) -> CreationResult:
    if not payloads:
        log_warn("Nenhum payload para criar no Monday")
        return CreationResult(created_ok=0, create_errors=0)

    if PIPELINE_CREATE_DRY_RUN:
        log_warn(f"[DRY-RUN] create_items simulado | total={len(payloads)}")
        return CreationResult(created_ok=0, create_errors=0)

    group_id = _get_default_group_id(MONDAY_BOARD_ID)
    log_info(f"Grupo padrao Monday: {group_id}")

    created_ok = 0
    create_errors = 0
    progress_bar = tqdm(total=len(payloads), desc="Criando itens Monday", unit="item", disable=not SHOW_PROGRESS)

    try:
        for payload in payloads:
            technical_id = normalize_text(payload.get("technical_id"))
            item_name = normalize_text(payload.get("item_name"))
            column_values_raw = payload.get("column_values_json", "{}")
            column_values = json.loads(column_values_raw) if isinstance(column_values_raw, str) else {}

            try:
                monday_id = _create_single_item(MONDAY_BOARD_ID, group_id, item_name, column_values)
                created_ok += 1
                log_info(f"Criado | technical_id={technical_id} | monday_id={monday_id}")
            except Exception as exc:
                create_errors += 1
                log_error(f"Falha ao criar | technical_id={technical_id} | erro={exc}")
            finally:
                progress_bar.update(1)
                sleep_with_jitter(HTTP_REQUEST_PAUSE_SECONDS)
    finally:
        progress_bar.close()

    log_info(f"Criacao concluida | ok={created_ok} | erros={create_errors}")
    return CreationResult(created_ok=created_ok, create_errors=create_errors)
