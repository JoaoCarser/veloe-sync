from __future__ import annotations

import time

from src.config.settings import LOG_PREFIX


def log_info(message: str) -> None:
    print(f"{LOG_PREFIX} [INFO] {message}")


def log_warn(message: str) -> None:
    print(f"{LOG_PREFIX} [WARN] {message}")


def log_error(message: str) -> None:
    print(f"{LOG_PREFIX} [ERROR] {message}")


def print_stage(label: str) -> None:
    print("")
    print("=" * 60)
    log_info(label)
    print("=" * 60)
    print("")


def log_ckpt_start(step: str) -> float:
    log_info(f"CKPT START step={step}")
    return time.perf_counter()


def log_ckpt_end(step: str, start: float, rows: object = None) -> None:
    dur = time.perf_counter() - start
    if rows is None:
        log_info(f"CKPT END step={step} dur_s={dur:.2f}")
    else:
        log_info(f"CKPT END step={step} rows={rows} dur_s={dur:.2f}")
