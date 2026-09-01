from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import TextIO

from doujinshi_meta.models import FetchError, SearchTagsResponse, Source, utc_now_iso
from doujinshi_meta.sources.bika import BikaClient
from doujinshi_meta.sources.bika_ops import fetch_comic_bika, open_bika_client, search_comics_bika
from doujinshi_meta.sources.jmcomic_ops import (
    create_jmcomic_client,
    fetch_comic_jmcomic,
    search_comics_jmcomic,
)

DEFAULT_DELAY = {Source.BIKA: 1.5, Source.JMCOMIC: 0.4}


def _log(stderr: TextIO, message: str) -> None:
    print(message, file=stderr)


def search_tags(
    query: str,
    source: Source | str,
    *,
    limit: int = 10,
    proxy: str | None = None,
    delay: float | None = None,
    stderr: TextIO | None = None,
    credentials_path: Path | None = None,
) -> SearchTagsResponse:
    src = Source(source)
    err_stream = stderr or sys.stderr
    wait = delay if delay is not None else DEFAULT_DELAY[src]
    response = SearchTagsResponse(
        source=src.value,
        query=query,
        generated_at=utc_now_iso(),
    )
    client: BikaClient | object | None = None

    try:
        if src == Source.JMCOMIC:
            client = create_jmcomic_client(proxy)
            search_fn = search_comics_jmcomic
            fetch_one = lambda cid: fetch_comic_jmcomic(client, cid)
        else:
            bika = open_bika_client(proxy, credentials_path=credentials_path)
            client = bika
            search_fn = search_comics_bika
            fetch_one = lambda cid: fetch_comic_bika(bika, cid)

        hits, total_hits = search_fn(client, query)
        response.total_hits = total_hits
        _log(err_stream, f"[search] {len(hits)} hits (total {total_hits}) for {query!r}")

        for index, (comic_id, _title) in enumerate(hits[:limit]):
            if index > 0:
                time.sleep(wait)
            comic_id = comic_id.strip()
            if not comic_id:
                continue
            try:
                item = fetch_one(comic_id)
                response.items.append(item)
                _log(err_stream, f"[search] ok {comic_id} ({len(item.tags)} tags)")
            except Exception as exc:
                response.errors.append(FetchError(external_id=comic_id, message=str(exc)))
                _log(err_stream, f"[search] error {comic_id}: {exc}")
    finally:
        if isinstance(client, BikaClient):
            client.close()

    return response
