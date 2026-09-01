from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import TextIO

from doujinshi_meta.models import FetchError, FetchTagsResponse, Source, utc_now_iso
from doujinshi_meta.sources.session import DEFAULT_DELAY, open_source_session


def _log(stderr: TextIO, message: str) -> None:
    print(message, file=stderr)


def fetch_tags(
    source: Source | str,
    ids: list[str],
    *,
    proxy: str | None = None,
    delay: float | None = None,
    stderr: TextIO | None = None,
    credentials_path: Path | None = None,
) -> FetchTagsResponse:
    src = Source(source)
    err_stream = stderr or sys.stderr
    wait = delay if delay is not None else DEFAULT_DELAY[src]
    response = FetchTagsResponse(source=src.value, generated_at=utc_now_iso())
    session = open_source_session(src, proxy=proxy, credentials_path=credentials_path)

    try:
        for index, comic_id in enumerate(ids):
            if index > 0:
                time.sleep(wait)
            comic_id = comic_id.strip()
            if not comic_id:
                continue
            try:
                item = session.fetch_comic(comic_id)
                response.items.append(item)
                _log(err_stream, f"[fetch] ok {comic_id} ({len(item.tags)} tags)")
            except Exception as exc:
                response.errors.append(FetchError(external_id=comic_id, message=str(exc)))
                _log(err_stream, f"[fetch] error {comic_id}: {exc}")
    finally:
        session.close()

    return response
