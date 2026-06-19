from __future__ import annotations

from typing import Any, Iterable, List


def chunk_list(values: List[Any], size: int) -> List[List[Any]]:
    return [values[i : i + size] for i in range(0, len(values), size)]


def chunked(values: List[Any], size: int) -> Iterable[List[Any]]:
    for i in range(0, len(values), size):
        yield values[i : i + size]
