from __future__ import annotations

from typing import Any, Dict

from src.config.settings import MONDAY_DATE_COLUMNS, MONDAY_NUMERIC_COLUMNS
from src.shared.normalize_text import (
    normalize_monday_number,
    normalize_text,
    parse_supply_date,
)
from src.veloe.build_supply_id import build_supply_id


def normalize_supply_id_row(item: Dict[str, Any]) -> Dict[str, str]:
    """Extrai apenas os campos necessários para comparação Veloe x Monday."""
    transaction_date = parse_supply_date(item.get("transactionDate", ""))
    return {
        "id": build_supply_id(
            vehicle_plate=normalize_text(item.get("vehiclePlate")),
            authorization=normalize_text(item.get("authorization")),
            transaction_date=transaction_date,
        ),
        "placa": normalize_text(item.get("vehiclePlate")),
        "authorization": normalize_text(item.get("authorization")),
        "date": transaction_date,
    }


def normalize_supply_full_row(item: Dict[str, Any]) -> Dict[str, Any]:
    """Extrai e normaliza todos os campos do abastecimento."""
    transaction_date_raw = normalize_text(item.get("transactionDate", ""))
    transaction_date_iso = parse_supply_date(transaction_date_raw)

    return {
        "id": build_supply_id(
            vehicle_plate=normalize_text(item.get("vehiclePlate")),
            authorization=normalize_text(item.get("authorization")),
            transaction_date=transaction_date_raw,
        ),
        "corporateName": normalize_text(item.get("corporateName")),
        "vehiclePlate": normalize_text(item.get("vehiclePlate")),
        "vehicleModel": normalize_text(item.get("vehicleModel")),
        "costCenter": normalize_text(item.get("costCenter")),
        "driverName": normalize_text(item.get("driverName")),
        "registry": normalize_text(item.get("registry")),
        "card": normalize_text(item.get("card")),
        "fuelType": normalize_text(item.get("fuelType")),
        "amountLiters": normalize_text(item.get("amountLiters")),
        "unitValue": normalize_text(item.get("unitValue")),
        "stockedValue": normalize_text(item.get("stockedValue")),
        "cardBalance": normalize_text(item.get("cardBalance")),
        "transactionDate": transaction_date_raw,
        "authorization": normalize_text(item.get("authorization")),
        "transactionStatus": normalize_text(item.get("transactionStatus")),
        "transactionType": normalize_text(item.get("transactionType")),
        "supplyLocation": normalize_text(item.get("supplyLocation")),
        "ecContractee": normalize_text(item.get("ecContractee")),
        "gasStationAddress": normalize_text(item.get("gasStationAddress")),
        "network": normalize_text(item.get("network")),
        "previousOdometer": normalize_text(item.get("previousOdometer")),
        "odometer": normalize_text(item.get("odometer")),
        "previousOrimeter": normalize_text(item.get("previousOrimeter")),
        "orimeter": normalize_text(item.get("orimeter")),
        "kmTraveled": normalize_text(item.get("kmTraveled")),
        "standardAverage": normalize_text(item.get("standardAverage")),
        "valueCostKmTraveled": normalize_text(item.get("valueCostKmTraveled")),
        "ipa": normalize_text(item.get("ipa")),
        "anpIndex": normalize_text(item.get("anpIndex")),
        "registration": normalize_text(item.get("registration")),
        "branchContractee": normalize_text(item.get("branchContractee")),
        "branchName": normalize_text(item.get("branchName")),
        "baseName": normalize_text(item.get("baseName")),
        "baseCode": normalize_text(item.get("baseCode")),
        "merchantState": normalize_text(item.get("merchantState")),
        "pumpCode": normalize_text(item.get("pumpCode")),
        "date": transaction_date_iso,
    }


def prepare_supply_for_monday(supply: Dict[str, Any]) -> Dict[str, Any]:
    """Aplica normalização final antes de montar o payload Monday."""
    result = dict(supply)
    for col in MONDAY_NUMERIC_COLUMNS:
        if col in result:
            result[col] = normalize_monday_number(result[col])
    for col in MONDAY_DATE_COLUMNS:
        if col in result:
            result[col] = parse_supply_date(result[col])
    return result
