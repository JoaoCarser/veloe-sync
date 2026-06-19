from __future__ import annotations

import random
import time

import requests

from src.config.settings import (
    HTTP_BACKOFF_BASE,
    HTTP_BACKOFF_CAP,
    HTTP_BACKOFF_FACTOR,
    HTTP_JITTER_MAX,
    HTTP_JITTER_MIN,
)


def build_backoff_delay(attempt: int) -> float:
    return min(HTTP_BACKOFF_BASE * (HTTP_BACKOFF_FACTOR ** attempt), HTTP_BACKOFF_CAP)


def sleep_with_jitter(base_delay: float) -> float:
    delay = min(base_delay, HTTP_BACKOFF_CAP)
    jitter = random.uniform(HTTP_JITTER_MIN, HTTP_JITTER_MAX)
    final_delay = delay + jitter
    time.sleep(final_delay)
    return final_delay


def should_retry_http_status(status_code: int) -> bool:
    return status_code == 429 or 500 <= status_code < 600


def should_retry_exception(exc: Exception) -> bool:
    return isinstance(exc, (requests.Timeout, requests.ConnectionError))


def should_retry_graphql_errors(errors: list) -> bool:
    text = str(errors).lower()
    markers = [
        "complexity",
        "rate limit",
        "maxconcurrencyexceeded",
        "temporarily unavailable",
        "internal server error",
        "timeout",
        "too many requests",
    ]
    return any(m in text for m in markers)
