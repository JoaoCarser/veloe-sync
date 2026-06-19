from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from src.config.settings import (
    PIPELINE_DELETE_DUPLICATE_DRY_RUN,
    PIPELINE_DELETE_ORPHAN_DRY_RUN,
)
from src.shared.logger import log_info, log_warn
from src.shared.normalize_text import normalize_compare_key
from src.monday.delete_items import delete_items
from src.monday.fetch_full_items import fetch_full_items
from src.sync.find_duplicates import find_duplicates
from src.sync.find_orphans import find_orphans


@dataclass
class CleanupResult:
    duplicates_found: int
    duplicates_removed: int
    orphans_found: int
    orphans_removed: int


def run_cleanup(veloe_supplies: List[Dict[str, str]]) -> CleanupResult:
    """
    1. Recarrega o Monday uma única vez (pós-criação).
    2. Detecta e remove duplicados, atualizando a lista em memória.
    3. Detecta e remove órfãos usando a lista já atualizada.
    Respeita as flags de dry-run individualmente.
    """
    # 1. Reload Monday — única chamada à API nesta etapa
    log_info("Recarregando Monday para limpeza...")
    monday_items = fetch_full_items()

    # 2. Duplicados
    duplicates = find_duplicates(monday_items)
    dup_found = len(duplicates)

    if PIPELINE_DELETE_DUPLICATE_DRY_RUN:
        log_warn(f"[DRY-RUN] Duplicados: {dup_found} encontrados, nenhum apagado")
        dup_removed = 0
    else:
        ids_to_delete = [d["id_monday"] for d in duplicates if d.get("id_monday")]
        dup_removed = delete_items(ids_to_delete, label="duplicado")
        log_info(f"Duplicados removidos: {dup_removed}/{dup_found}")
        # Remove os apagados da lista em memória para a detecção de órfãos
        deleted_set = set(ids_to_delete)
        monday_items = [item for item in monday_items if item.get("id_monday") not in deleted_set]

    # 3. Orphans — usa a lista já atualizada, sem nova chamada à API
    veloe_ids = {normalize_compare_key(s.get("id", "")) for s in veloe_supplies}
    orphans = find_orphans(monday_items, veloe_ids)
    orp_found = len(orphans)

    if PIPELINE_DELETE_ORPHAN_DRY_RUN:
        log_warn(f"[DRY-RUN] Orphans: {orp_found} encontrados, nenhum apagado")
        orp_removed = 0
    else:
        ids_to_delete = [o["id_monday"] for o in orphans if o.get("id_monday")]
        orp_removed = delete_items(ids_to_delete, label="orphan")
        log_info(f"Orphans removidos: {orp_removed}/{orp_found}")

    return CleanupResult(
        duplicates_found=dup_found,
        duplicates_removed=dup_removed,
        orphans_found=orp_found,
        orphans_removed=orp_removed,
    )
