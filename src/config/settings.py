from __future__ import annotations

import os
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()


def _get_str(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def _get_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def _get_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def _get_bool(key: str, default: bool) -> bool:
    raw = os.getenv(key, str(default)).strip().lower()
    return raw in ("1", "true", "yes")


def _mask_token(token: str) -> str:
    if not token:
        return "(vazio)"
    if len(token) <= 8:
        return "****"
    return token[:4] + "****" + token[-4:]


def _mask_id(value: str) -> str:
    if not value:
        return "(vazio)"
    if len(value) <= 4:
        return "****"
    return value[:2] + "****" + value[-2:]


# ---------------------------------------------------------------------------
# Veloe / Alelo API
# ---------------------------------------------------------------------------

VELOE_API_BASE_URL: str = _get_str("VELOE_API_BASE_URL")
VELOE_LOGIN_ENDPOINT: str = f"{VELOE_API_BASE_URL}/vehicle/login"
VELOE_VEHICLES_ENDPOINT: str = f"{VELOE_API_BASE_URL}/vehicle/vehicles"
VELOE_CONTRACT: str = _get_str("VELOE_CONTRACT")
VELOE_SUPPLY_HISTORY_ENDPOINT: str = (
    f"{VELOE_API_BASE_URL}/fuel-supply-data/v1/supply-history-anp/contract/{VELOE_CONTRACT}"
)
VELOE_CLIENT_ID: str = _get_str("VELOE_CLIENT_ID")
VELOE_CLIENT_SECRET: str = _get_str("VELOE_CLIENT_SECRET")
VELOE_AUTHORIZATION_PREFIX: str = _get_str("VELOE_AUTHORIZATION_PREFIX", "Bearer")
VELOE_TOKEN_TTL_MINUTES: int = _get_int("VELOE_TOKEN_TTL_MINUTES", 120)

# ---------------------------------------------------------------------------
# Monday
# ---------------------------------------------------------------------------

MONDAY_API_TOKEN: str = _get_str("MONDAY_API_TOKEN")
MONDAY_API_URL: str = _get_str("MONDAY_API_URL")
MONDAY_BOARD_ID: str = _get_str("MONDAY_BOARD_ID")
MONDAY_BOARD_NAME: str = _get_str("MONDAY_BOARD_NAME")
MONDAY_PAGE_SIZE: int = _get_int("MONDAY_PAGE_SIZE", 500)

MONDAY_HEADERS: Dict[str, str] = {
    "Authorization": MONDAY_API_TOKEN,
    "Content-Type": "application/json",
}

# ---------------------------------------------------------------------------
# n8n
# ---------------------------------------------------------------------------

N8N_SUMMARY_WEBHOOK_URL: str = _get_str("N8N_SUMMARY_WEBHOOK_URL")

# ---------------------------------------------------------------------------
# Retry / backoff / timeout
# ---------------------------------------------------------------------------

HTTP_MAX_RETRIES: int = _get_int("HTTP_MAX_RETRIES", 5)
HTTP_BACKOFF_BASE: float = _get_float("HTTP_BACKOFF_BASE", 1.0)
HTTP_BACKOFF_FACTOR: float = _get_float("HTTP_BACKOFF_FACTOR", 2.0)
HTTP_BACKOFF_CAP: float = _get_float("HTTP_BACKOFF_CAP", 30.0)
HTTP_JITTER_MIN: float = _get_float("HTTP_JITTER_MIN", 0.0)
HTTP_JITTER_MAX: float = _get_float("HTTP_JITTER_MAX", 0.5)
HTTP_REQUEST_TIMEOUT: int = _get_int("HTTP_REQUEST_TIMEOUT", 60)
HTTP_REQUEST_PAUSE_SECONDS: float = _get_float("HTTP_REQUEST_PAUSE_SECONDS", 0.2)

# ---------------------------------------------------------------------------
# Paginação / lotes
# ---------------------------------------------------------------------------

VELOE_VEHICLES_PAGE_SIZE: int = _get_int("VELOE_VEHICLES_PAGE_SIZE", 500)
VELOE_SUPPLY_BATCH_SIZE: int = _get_int("VELOE_SUPPLY_BATCH_SIZE", 100)
VELOE_SUPPLY_BATCH_SIZE_ON_ERROR: int = _get_int("VELOE_SUPPLY_BATCH_SIZE_ON_ERROR", 50)
VELOE_SUPPLY_WINDOW_DAYS: int = _get_int("VELOE_SUPPLY_WINDOW_DAYS", 7)

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

LOG_PREFIX: str = _get_str("PIPELINE_LOG_PREFIX", "[VELOE]")
SHOW_PROGRESS: bool = _get_bool("PIPELINE_SHOW_PROGRESS", True)

# Dry-runs: False = executa de verdade; True = só simula e registra
PIPELINE_CREATE_DRY_RUN: bool = _get_bool("PIPELINE_CREATE_DRY_RUN", False)
PIPELINE_DELETE_DUPLICATE_DRY_RUN: bool = _get_bool("PIPELINE_DELETE_DUPLICATE_DRY_RUN", False)
PIPELINE_DELETE_ORPHAN_DRY_RUN: bool = _get_bool("PIPELINE_DELETE_ORPHAN_DRY_RUN", False)

# ---------------------------------------------------------------------------
# Mapeamento de colunas Veloe → Monday
# ---------------------------------------------------------------------------

MONDAY_COLUMN_MAP: Dict[str, str] = {
    "name": "name",
    "corporateName": "text_mm4183vf",
    "vehiclePlate": "text_mm41v3r1",
    "vehicleModel": "text_mm41ynj8",
    "costCenter": "text_mm41g3dc",
    "driverName": "text_mm412t0p",
    "registry": "text_mm4165xt",
    "card": "text_mm41jysw",
    "fuelType": "dropdown_mm41g3k3",
    "amountLiters": "numeric_mm41xx58",
    "unitValue": "numeric_mm41pxat",
    "stockedValue": "numeric_mm41awka",
    "cardBalance": "numeric_mm413srq",
    "transactionDate": "date_mm41sm35",
    "authorization": "text_mm4138m",
    "transactionStatus": "color_mm41v2p0",
    "transactionType": "dropdown_mm416n4e",
    "supplyLocation": "text_mm41d2yf",
    "ecContractee": "text_mm41wfcg",
    "gasStationAddress": "text_mm41rkp3",
    "network": "dropdown_mm41jsdn",
    "previousOdometer": "numeric_mm41ph4t",
    "odometer": "numeric_mm41gj22",
    "previousOrimeter": "numeric_mm419y3e",
    "orimeter": "numeric_mm41g86j",
    "kmTraveled": "numeric_mm41hqjd",
    "standardAverage": "numeric_mm41xxzf",
    "valueCostKmTraveled": "numeric_mm41vpgd",
    "ipa": "numeric_mm41gjc",
    "anpIndex": "numeric_mm418k9w",
    "registration": "text_mm41d9tb",
    "branchContractee": "text_mm412pgh",
    "branchName": "dropdown_mm41ak2m",
    "baseName": "dropdown_mm41p473",
    "baseCode": "text_mm419tg3",
    "merchantState": "dropdown_mm41c0ve",
    "pumpCode": "text_mm41kb8n",
}

MONDAY_NUMERIC_COLUMNS: List[str] = [
    "amountLiters",
    "unitValue",
    "stockedValue",
    "cardBalance",
    "previousOdometer",
    "odometer",
    "previousOrimeter",
    "orimeter",
    "kmTraveled",
    "standardAverage",
    "valueCostKmTraveled",
    "ipa",
    "anpIndex",
]

MONDAY_DATE_COLUMNS: List[str] = [
    "transactionDate",
    "date",
]

# ---------------------------------------------------------------------------
# Colunas de supply completo
# ---------------------------------------------------------------------------

SUPPLY_FULL_COLUMNS: List[str] = [
    "id",
    "corporateName",
    "vehiclePlate",
    "vehicleModel",
    "costCenter",
    "driverName",
    "registry",
    "card",
    "fuelType",
    "amountLiters",
    "unitValue",
    "stockedValue",
    "cardBalance",
    "transactionDate",
    "authorization",
    "transactionStatus",
    "transactionType",
    "supplyLocation",
    "ecContractee",
    "gasStationAddress",
    "network",
    "previousOdometer",
    "odometer",
    "previousOrimeter",
    "orimeter",
    "kmTraveled",
    "standardAverage",
    "valueCostKmTraveled",
    "ipa",
    "anpIndex",
    "registration",
    "branchContractee",
    "branchName",
    "baseName",
    "baseCode",
    "merchantState",
    "pumpCode",
    "date",
]


def check_required_envs() -> None:
    missing: List[str] = []
    if not VELOE_API_BASE_URL:
        missing.append("VELOE_API_BASE_URL")
    if not VELOE_CLIENT_ID:
        missing.append("VELOE_CLIENT_ID")
    if not VELOE_CLIENT_SECRET:
        missing.append("VELOE_CLIENT_SECRET")
    if not VELOE_CONTRACT:
        missing.append("VELOE_CONTRACT")
    if not MONDAY_API_TOKEN:
        missing.append("MONDAY_API_TOKEN")
    if not MONDAY_API_URL:
        missing.append("MONDAY_API_URL")
    if not MONDAY_BOARD_ID:
        missing.append("MONDAY_BOARD_ID")
    if not MONDAY_BOARD_NAME:
        missing.append("MONDAY_BOARD_NAME")
    if not N8N_SUMMARY_WEBHOOK_URL:
        missing.append("N8N_SUMMARY_WEBHOOK_URL")
    if missing:
        raise EnvironmentError(f"Variaveis obrigatorias nao configuradas: {missing}")

    print(f"{LOG_PREFIX} [INFO] === Configuracao do pipeline ===")
    print(f"{LOG_PREFIX} [INFO] MONDAY_API_TOKEN  : {_mask_token(MONDAY_API_TOKEN)}")
    print(f"{LOG_PREFIX} [INFO] MONDAY_BOARD_ID   : {_mask_id(MONDAY_BOARD_ID)}")
    print(f"{LOG_PREFIX} [INFO] VELOE_CONTRACT     : {_mask_id(VELOE_CONTRACT)}")
    print(f"{LOG_PREFIX} [INFO] HTTP_MAX_RETRIES   : {HTTP_MAX_RETRIES}")
    print(f"{LOG_PREFIX} [INFO] HTTP_REQUEST_TIMEOUT: {HTTP_REQUEST_TIMEOUT}s")
    print(f"{LOG_PREFIX} [INFO] MONDAY_PAGE_SIZE   : {MONDAY_PAGE_SIZE}")
    print(f"{LOG_PREFIX} [INFO] SHOW_PROGRESS      : {SHOW_PROGRESS}")
    print(f"{LOG_PREFIX} [INFO] --- dry-runs ---")
    print(f"{LOG_PREFIX} [INFO] CREATE             : {PIPELINE_CREATE_DRY_RUN}")
    print(f"{LOG_PREFIX} [INFO] DELETE_DUPLICATE   : {PIPELINE_DELETE_DUPLICATE_DRY_RUN}")
    print(f"{LOG_PREFIX} [INFO] DELETE_ORPHAN      : {PIPELINE_DELETE_ORPHAN_DRY_RUN}")
    print(f"{LOG_PREFIX} [INFO] ===================================")
