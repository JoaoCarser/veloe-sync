from __future__ import annotations

import time
from typing import Any, Dict

from src.monday.create_items import CreationResult
from src.shared.logger import log_info
from src.sync.compare_records import ComparisonResult
from src.sync.run_cleanup import CleanupResult


def _format_elapsed(start_ts: float) -> str:
    total = int(time.time() - start_ts)
    minutes, seconds = divmod(max(total, 0), 60)
    return f"{minutes}m{seconds:02d}s"


def _print_summary(payload: Dict[str, Any]) -> None:
    w = 50
    print("|" + "-" * w + "|")
    print("|" + "SUMMARY".center(w) + "|")
    print("|" + "-" * w + "|")
    print("|" + " TEMPO ".center(w, "-") + "|")
    print(f"| Tempo total..............: {payload['elapsed']:<23}|")
    print(f"| Fallback.................: {'SIM' if payload['fallback_used'] else 'NAO':<23}|")
    print("|" + "-" * w + "|")
    print("|" + " SINCRONIA ".center(w, "-") + "|")
    print(f"| Veloe total..............: {payload['veloe_total']:<23}|")
    print(f"| Monday inicial...........: {payload['monday_initial_total']:<23}|")
    print(f"| Novos IDs................: {payload['new_ids_found']:<23}|")
    print(f"| Criados com sucesso......: {payload['monday_created_ok']:<23}|")
    print(f"| Erros ao criar...........: {payload['monday_create_errors']:<23}|")
    print("|" + "-" * w + "|")
    print("|" + " LIMPEZA ".center(w, "-") + "|")
    print(f"| Duplicados encontrados...: {payload['duplicates_found']:<23}|")
    print(f"| Duplicados removidos.....: {payload['duplicates_removed']:<23}|")
    print(f"| Orphans encontrados......: {payload['orphans_found']:<23}|")
    print(f"| Orphans removidos........: {payload['orphans_removed']:<23}|")
    print("|" + "-" * w + "|")
    print("|" + " EXPECTATIVA ".center(w, "-") + "|")
    print(f"| Monday Atualizado........: {payload['monday_final_estimated']:<23}|")
    print(f"| Esperado (Veloe).........: {payload['veloe_total']:<23}|")
    print(f"| Diferenca................: {payload['difference']:<23}|")
    print("|" + "-" * w + "|")


def build_summary(
    pipeline_start_ts: float,
    comparison: ComparisonResult,
    creation_result: CreationResult,
    cleanup_result: CleanupResult,
    fallback_used: bool = False,
) -> Dict[str, Any]:
    monday_final = (
        comparison.monday_initial_total
        + creation_result.created_ok
        - cleanup_result.duplicates_removed
        - cleanup_result.orphans_removed
    )
    difference = comparison.veloe_total - monday_final

    payload: Dict[str, Any] = {
        "elapsed": _format_elapsed(pipeline_start_ts),
        "fallback_used": fallback_used,
        "veloe_total": comparison.veloe_total,
        "monday_initial_total": comparison.monday_initial_total,
        "new_ids_found": comparison.new_ids_found,
        "monday_created_ok": creation_result.created_ok,
        "monday_create_errors": creation_result.create_errors,
        "duplicates_found": cleanup_result.duplicates_found,
        "duplicates_removed": cleanup_result.duplicates_removed,
        "orphans_found": cleanup_result.orphans_found,
        "orphans_removed": cleanup_result.orphans_removed,
        "monday_final_estimated": monday_final,
        "difference": difference,
    }

    _print_summary(payload)
    return payload
