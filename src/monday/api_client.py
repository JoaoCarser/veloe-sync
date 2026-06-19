from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from src.config.settings import (
    HTTP_MAX_RETRIES,
    HTTP_REQUEST_TIMEOUT,
    MONDAY_API_URL,
    MONDAY_HEADERS,
    MONDAY_PAGE_SIZE,
    SHOW_PROGRESS,
)
from src.shared.logger import log_error, log_info, log_warn
from src.shared.retry import (
    build_backoff_delay,
    should_retry_exception,
    should_retry_graphql_errors,
    should_retry_http_status,
    sleep_with_jitter,
)


def execute_monday_query(
    query: str,
    variables: Optional[Dict[str, Any]] = None,
    operation_name: str = "graphql_request",
    timeout: int = HTTP_REQUEST_TIMEOUT,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables

    last_error: Optional[Exception] = None

    for attempt in range(HTTP_MAX_RETRIES + 1):
        try:
            response = requests.post(
                MONDAY_API_URL,
                headers=MONDAY_HEADERS,
                json=payload,
                timeout=timeout,
            )

            if response.status_code == 200:
                result = response.json()

                if "errors" in result:
                    errors = result["errors"]
                    err_txt = str(errors)[:1800]

                    if "CursorExpiredError" in err_txt:
                        raise ValueError(f"{operation_name} CursorExpiredError: {err_txt}")

                    if should_retry_graphql_errors(errors) and attempt < HTTP_MAX_RETRIES:
                        delay = sleep_with_jitter(build_backoff_delay(attempt))
                        log_warn(
                            f"{operation_name} GraphQL retryavel tentativa {attempt + 1}/{HTTP_MAX_RETRIES} "
                            f"retry={delay:.2f}s erro={err_txt}"
                        )
                        continue

                    log_error(f"{operation_name} GraphQL error: {err_txt}")
                    raise ValueError(f"{operation_name} GraphQL error: {err_txt}")

                return result.get("data", {})

            if should_retry_http_status(response.status_code) and attempt < HTTP_MAX_RETRIES:
                delay = sleep_with_jitter(build_backoff_delay(attempt))
                log_warn(
                    f"{operation_name} HTTP {response.status_code} tentativa {attempt + 1}/{HTTP_MAX_RETRIES} "
                    f"retry={delay:.2f}s"
                )
                continue

            log_error(f"{operation_name} HTTP {response.status_code}: {response.text[:500]}")
            response.raise_for_status()

        except Exception as exc:
            last_error = exc

            if isinstance(exc, requests.exceptions.HTTPError):
                code = exc.response.status_code if exc.response is not None else None
                if code and should_retry_http_status(code) and attempt < HTTP_MAX_RETRIES:
                    delay = sleep_with_jitter(build_backoff_delay(attempt))
                    log_warn(
                        f"{operation_name} HTTPError {code} tentativa {attempt + 1}/{HTTP_MAX_RETRIES} "
                        f"retry={delay:.2f}s"
                    )
                    continue
                raise

            if should_retry_exception(exc) and attempt < HTTP_MAX_RETRIES:
                delay = sleep_with_jitter(build_backoff_delay(attempt))
                log_warn(
                    f"{operation_name} {type(exc).__name__} tentativa {attempt + 1}/{HTTP_MAX_RETRIES} "
                    f"retry={delay:.2f}s"
                )
                continue

            raise

    raise RuntimeError(f"{operation_name} falhou apos retries") from last_error


def query_board_items_paginated(
    board_id: str,
    fields: str = "id name",
    limit: int = MONDAY_PAGE_SIZE,
    board_name: str = "",
    max_cursor_restarts: int = 6,
    empty_page_retries: int = 2,
) -> List[Dict[str, Any]]:
    """Busca todos os itens de um board com paginação por cursor."""
    from tqdm import tqdm

    q_initial = f"""
    query ($board_id: [ID!], $limit: Int!) {{
      boards(ids: $board_id) {{
        items_page(limit: $limit) {{
          cursor
          items {{ {fields} }}
        }}
      }}
    }}
    """
    q_next = f"""
    query ($cursor: String!, $limit: Int!) {{
      next_items_page(cursor: $cursor, limit: $limit) {{
        cursor
        items {{ {fields} }}
      }}
    }}
    """

    label = board_name or board_id
    all_items: Dict[str, Dict[str, Any]] = {}
    progress_bar = tqdm(desc=f"Board {label}", unit="pag", dynamic_ncols=True, disable=not SHOW_PROGRESS)

    restart = 0
    while restart <= max_cursor_restarts:
        restart += 1
        if restart > 1:
            log_warn(f"Board {label}: reinicio cursor ({restart - 1}/{max_cursor_restarts})")

        data = execute_monday_query(
            query=q_initial,
            variables={"board_id": [board_id], "limit": limit},
            operation_name=f"items_initial_{board_id}_r{restart}",
        )

        boards = data.get("boards", [])
        if not boards:
            break

        items_page = boards[0].get("items_page") or {}
        items = items_page.get("items", []) or []
        cursor = items_page.get("cursor")

        for it in items:
            iid = str(it.get("id", "")).strip()
            if iid:
                all_items[iid] = it
        progress_bar.update(1)
        progress_bar.set_postfix_str(f"itens={len(all_items)}")

        seen_cursors: set = set()
        needs_restart = False

        while cursor:
            if cursor in seen_cursors:
                log_warn(f"Board {label}: cursor repetido detectado")
                needs_restart = True
                break
            seen_cursors.add(cursor)

            try:
                page = execute_monday_query(
                    query=q_next,
                    variables={"cursor": cursor, "limit": limit},
                    operation_name=f"items_next_{board_id}_r{restart}",
                ).get("next_items_page", {})
            except Exception as exc:
                if "CursorExpiredError" in str(exc):
                    needs_restart = True
                    break
                raise

            page_items = page.get("items", []) or []
            next_cursor = page.get("cursor")

            if next_cursor and not page_items:
                recovered = False
                for retry_i in range(empty_page_retries):
                    delay = sleep_with_jitter(build_backoff_delay(retry_i))
                    log_warn(
                        f"Board {label}: pagina vazia com cursor ativo "
                        f"retry {retry_i + 1}/{empty_page_retries} delay={delay:.2f}s"
                    )
                    retry_page = execute_monday_query(
                        query=q_next,
                        variables={"cursor": cursor, "limit": limit},
                        operation_name=f"items_retry_{board_id}_r{restart}",
                    ).get("next_items_page", {})
                    retry_items = retry_page.get("items", []) or []
                    retry_cursor = retry_page.get("cursor")
                    if retry_items:
                        page_items = retry_items
                        next_cursor = retry_cursor
                        recovered = True
                        break

                if not recovered:
                    log_warn(f"Board {label}: pagina vazia persistente, reiniciando leitura")
                    needs_restart = True
                    break

            for it in page_items:
                iid = str(it.get("id", "")).strip()
                if iid:
                    all_items[iid] = it
            progress_bar.update(1)
            progress_bar.set_postfix_str(f"itens={len(all_items)}")
            cursor = next_cursor

        if not needs_restart:
            break

    progress_bar.close()
    log_info(f"Board {label}: leitura concluida total={len(all_items)}")
    return list(all_items.values())
