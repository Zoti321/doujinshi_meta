from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, TextIO

from doujinshi_meta.models import (
    BatchAmbiguous,
    BatchError,
    BatchScrapeItem,
    SearchBatchResponse,
    Source,
    utc_now_iso,
)
from doujinshi_meta.search import search_tags
from doujinshi_meta.sources.session import DEFAULT_DELAY


def _log(stderr: TextIO, message: str) -> None:
    print(message, file=stderr)


def _parse_batch_line(raw_line: str, line_no: int) -> tuple[dict[str, Any] | None, BatchError | None]:
    line = raw_line.strip()
    if not line or line.startswith("#"):
        return None, None
    try:
        payload = json.loads(line)
    except json.JSONDecodeError as exc:
        return None, BatchError(local_id=f"line:{line_no}", message=str(exc))
    if not isinstance(payload, dict):
        return None, BatchError(local_id=f"line:{line_no}", message="每行必须是 JSON 对象")
    return payload, None


def _validate_batch_row(payload: dict[str, Any], line_no: int) -> BatchError | None:
    local_id = payload.get("local_id")
    title = payload.get("title")
    if not isinstance(local_id, str) or not local_id.strip():
        return BatchError(local_id=f"line:{line_no}", message="缺少 local_id")
    if not isinstance(title, str) or not title.strip():
        return BatchError(local_id=str(local_id), message="缺少 title")
    pages = payload.get("pages")
    if pages is not None and not isinstance(pages, int):
        return BatchError(local_id=str(local_id), message="pages 必须是整数")
    if isinstance(pages, int) and pages < 1:
        return BatchError(local_id=str(local_id), message="pages 必须是正整数")
    return None


def search_batch_tags(
    input_path: Path | str,
    source: Source | str,
    *,
    limit: int = 10,
    proxy: str | None = None,
    delay: float | None = None,
    stderr: TextIO | None = None,
    credentials_path: Path | None = None,
) -> SearchBatchResponse:
    src = Source(source)
    err_stream = stderr or sys.stderr
    wait = delay if delay is not None else DEFAULT_DELAY[src]
    path = Path(input_path)
    response = SearchBatchResponse(source=src.value, generated_at=utc_now_iso())

    if not path.is_file():
        raise RuntimeError(f"输入文件不存在: {path}")

    lines = path.read_text(encoding="utf-8").splitlines()
    valid_rows = 0

    for line_no, raw_line in enumerate(lines, start=1):
        payload, parse_error = _parse_batch_line(raw_line, line_no)
        if parse_error is not None:
            response.errors.append(parse_error)
            continue
        if payload is None:
            continue

        row_error = _validate_batch_row(payload, line_no)
        if row_error is not None:
            response.errors.append(row_error)
            continue

        valid_rows += 1
        local_id = str(payload["local_id"]).strip()
        title = str(payload["title"]).strip()
        pages_raw = payload.get("pages")
        pages = int(pages_raw) if pages_raw is not None else None

        if valid_rows > 1:
            time.sleep(wait)

        _log(err_stream, f"[search-batch] {local_id!r} {title!r}")
        try:
            result = search_tags(
                title,
                src,
                limit=limit,
                pages=pages,
                proxy=proxy,
                delay=0,
                stderr=err_stream,
                credentials_path=credentials_path,
            )
        except RuntimeError as exc:
            response.errors.append(BatchError(local_id=local_id, message=str(exc)))
            continue

        if result.items:
            item = result.items[0]
            response.items.append(
                BatchScrapeItem(
                    local_id=local_id,
                    external_id=item.external_id,
                    title=item.title,
                    tags=item.tags,
                    page_count=item.page_count,
                )
            )
            continue

        if result.ambiguous:
            response.ambiguous.append(
                BatchAmbiguous(
                    local_id=local_id,
                    title=title,
                    candidates=result.ambiguous[0].candidates,
                )
            )
            continue

        if result.errors:
            response.errors.append(
                BatchError(local_id=local_id, message=result.errors[0].message)
            )
            continue

        response.errors.append(BatchError(local_id=local_id, message="无匹配结果"))

    if valid_rows == 0:
        raise RuntimeError("输入文件无有效行")

    return response
