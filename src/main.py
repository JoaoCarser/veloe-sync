from __future__ import annotations

import sys
import time

from src.config.settings import check_required_envs
from src.monday.build_item_payload import build_item_payloads
from src.monday.create_items import create_items
from src.monday.fetch_item_names import fetch_existing_item_names
from src.shared.logger import log_ckpt_end, log_ckpt_start, log_error, log_info, print_stage
from src.summary.build_summary import build_summary
from src.sync.compare_records import compare_veloe_with_monday
from src.sync.run_cleanup import run_cleanup
from src.veloe.api_client import create_veloe_session
from src.veloe.date_periods import get_current_semester_period 
from src.veloe.fetch_full_supplies import fetch_full_supplies
from src.veloe.fetch_supplies import fetch_supplies
from src.veloe.fetch_vehicles import fetch_all_vehicles
from src.veloe.login import login_veloe
from src.webhook.send_to_n8n import send_summary_to_n8n


def main() -> int:
    pipeline_start_ts = time.time()

    try:
        # ------------------------------------------------------------------
        print_stage("ETAPA 01 - VALIDAR AMBIENTE")
        step_ts = log_ckpt_start("check_env")
        check_required_envs()
        log_ckpt_end("check_env", step_ts)

        # ------------------------------------------------------------------
        print_stage("ETAPA 02 - AUTENTICAR NA VELOE")
        step_ts = log_ckpt_start("login_veloe")
        session = create_veloe_session()
        token = login_veloe(session)
        log_ckpt_end("login_veloe", step_ts)

        # ------------------------------------------------------------------
        print_stage("ETAPA 03 - BUSCAR VEICULOS")
        step_ts = log_ckpt_start("fetch_vehicles")
        vehicles = fetch_all_vehicles(session, token)
        log_ckpt_end("fetch_vehicles", step_ts, len(vehicles))

        # ------------------------------------------------------------------
        print_stage("ETAPA 04 - CALCULAR PERIODO DO SEMESTRE")
        step_ts = log_ckpt_start("get_period")
        period = get_current_semester_period()
        log_info(
            f"Periodo: semestre={period['semester']} "
            f"start={period['start_date']} end={period['end_date']}"
        )
        log_ckpt_end("get_period", step_ts)

        # ------------------------------------------------------------------
        print_stage("ETAPA 05 - BUSCAR IDs DE ABASTECIMENTO NA VELOE")
        step_ts = log_ckpt_start("fetch_supplies")
        veloe_supplies = fetch_supplies(session, token, vehicles, period)
        log_ckpt_end("fetch_supplies", step_ts, len(veloe_supplies))

        # ------------------------------------------------------------------
        print_stage("ETAPA 06 - BUSCAR REGISTROS ATUAIS NO MONDAY")
        step_ts = log_ckpt_start("fetch_monday_names")
        monday_item_names = fetch_existing_item_names()
        log_ckpt_end("fetch_monday_names", step_ts, len(monday_item_names))

        # ------------------------------------------------------------------
        print_stage("ETAPA 07 - COMPARAR VELOE x MONDAY")
        step_ts = log_ckpt_start("compare_records")
        comparison = compare_veloe_with_monday(veloe_supplies, monday_item_names)
        log_ckpt_end("compare_records", step_ts, comparison.new_ids_found)

        # ------------------------------------------------------------------
        print_stage("ETAPA 08 - BUSCAR DADOS COMPLETOS DOS NOVOS ABASTECIMENTOS")
        step_ts = log_ckpt_start("fetch_full_supplies")
        full_result = fetch_full_supplies(session, token, comparison.missing_supplies, period)
        full_supplies = full_result["items"]
        fallback_used = full_result["fallback_used"]
        log_ckpt_end("fetch_full_supplies", step_ts, len(full_supplies))

        # ------------------------------------------------------------------
        print_stage("ETAPA 09 - MONTAR PAYLOADS PARA O MONDAY")
        step_ts = log_ckpt_start("build_payloads")
        payloads = build_item_payloads(full_supplies)
        log_ckpt_end("build_payloads", step_ts, len(payloads))

        # ------------------------------------------------------------------
        print_stage("ETAPA 10 - CRIAR NOVOS ITENS NO MONDAY")
        step_ts = log_ckpt_start("create_items")
        creation_result = create_items(payloads)
        log_ckpt_end("create_items", step_ts, creation_result.created_ok)

        # ------------------------------------------------------------------
        print_stage("ETAPA 11 - LIMPEZA: DUPLICADOS E ORPHANS")
        step_ts = log_ckpt_start("run_cleanup")
        cleanup_result = run_cleanup(veloe_supplies=veloe_supplies)
        log_ckpt_end("run_cleanup", step_ts)

        # ------------------------------------------------------------------
        print_stage("ETAPA 12 - RESUMO FINAL")
        step_ts = log_ckpt_start("build_summary")
        summary = build_summary(
            pipeline_start_ts=pipeline_start_ts,
            comparison=comparison,
            creation_result=creation_result,
            cleanup_result=cleanup_result,
            fallback_used=fallback_used,
        )
        log_ckpt_end("build_summary", step_ts)

        # ------------------------------------------------------------------
        print_stage("ETAPA 13 - ENVIAR RESUMO AO WEBHOOK N8N")
        step_ts = log_ckpt_start("send_webhook")
        send_summary_to_n8n(summary)
        log_ckpt_end("send_webhook", step_ts)

        # ------------------------------------------------------------------
        print_stage("Pipeline Veloe/Alelo concluido com sucesso")
        return 0

    except Exception as exc:
        log_error(f"Falha na execucao do pipeline: {exc}")
        raise


if __name__ == "__main__":
    sys.exit(main())
