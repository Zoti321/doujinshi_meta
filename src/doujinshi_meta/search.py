from __future__ import annotations

import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import TextIO

from doujinshi_meta.models import (
    AmbiguousCandidate,
    ComicTagsItem,
    FetchError,
    SearchAmbiguous,
    SearchTagsResponse,
    Source,
    utc_now_iso,
)
from doujinshi_meta.sources.session import DEFAULT_DELAY, SearchHit, open_source_session

FetchOne = Callable[[str], ComicTagsItem]


def _log(stderr: TextIO, message: str) -> None:
    print(message, file=stderr)


def _candidate_from_hit(hit: SearchHit) -> AmbiguousCandidate:
    external_id, title, page_count = hit
    return AmbiguousCandidate(
        external_id=external_id,
        title=title,
        page_count=page_count,
    )


def _resolve_by_pages(
    query: str,
    candidates: list[SearchHit],
    hint_pages: int,
    fetch_one: FetchOne,
    *,
    wait: float,
    stderr: TextIO,
) -> tuple[list[ComicTagsItem], list[SearchAmbiguous], list[FetchError]]:
    if not candidates:
        return [], [], []

    enriched: list[tuple[SearchHit, int | None]] = []
    prefetched: dict[str, ComicTagsItem] = {}

    for index, hit in enumerate(candidates):
        external_id, title, list_page_count = hit
        page_count = list_page_count
        if page_count is None:
            if index > 0:
                time.sleep(wait)
            try:
                item = fetch_one(external_id)
                prefetched[external_id] = item
                page_count = item.page_count
            except Exception as exc:
                _log(stderr, f"[search] skip {external_id}: {exc}")
        enriched.append(((external_id, title, list_page_count), page_count))

    with_pages = [(hit, page_count) for hit, page_count in enriched if page_count is not None]
    if not with_pages:
        ambiguous = SearchAmbiguous(
            query=query,
            candidates=[_candidate_from_hit(hit) for hit, _ in enriched],
        )
        return [], [ambiguous], []

    min_diff = min(abs(page_count - hint_pages) for _, page_count in with_pages)
    winners = [hit for hit, page_count in with_pages if abs(page_count - hint_pages) == min_diff]

    if len(winners) > 1:
        ambiguous = SearchAmbiguous(
            query=query,
            candidates=[_candidate_from_hit(hit) for hit in winners],
        )
        return [], [ambiguous], []

    winner_id = winners[0][0]
    if winner_id in prefetched:
        return [prefetched[winner_id]], [], []

    try:
        item = fetch_one(winner_id)
        return [item], [], []
    except Exception as exc:
        _log(stderr, f"[search] error {winner_id}: {exc}")
        return [], [], [FetchError(external_id=winner_id, message=str(exc))]


def _fetch_hits_without_pages(
    hits: list[SearchHit],
    limit: int,
    fetch_one: FetchOne,
    *,
    wait: float,
    stderr: TextIO,
) -> tuple[list[ComicTagsItem], list[FetchError]]:
    items: list[ComicTagsItem] = []
    errors: list[FetchError] = []

    for index, (comic_id, _title, _page_count) in enumerate(hits):
        if index > 0:
            time.sleep(wait)
        comic_id = comic_id.strip()
        if not comic_id:
            continue
        try:
            item = fetch_one(comic_id)
            items.append(item)
            _log(stderr, f"[search] ok {comic_id} ({len(item.tags)} tags)")
        except Exception as exc:
            errors.append(FetchError(external_id=comic_id, message=str(exc)))
            _log(stderr, f"[search] error {comic_id}: {exc}")

    return items, errors


def search_tags(
    query: str,
    source: Source | str,
    *,
    limit: int = 10,
    pages: int | None = None,
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
    session = open_source_session(src, proxy=proxy, credentials_path=credentials_path)

    try:
        hits, total_hits = session.search(query)
        response.total_hits = total_hits
        _log(err_stream, f"[search] {len(hits)} hits (total {total_hits}) for {query!r}")

        fetch_one = session.fetch_comic
        scan_hits = hits[:limit]
        if pages is None:
            items, errors = _fetch_hits_without_pages(
                scan_hits,
                limit,
                fetch_one,
                wait=wait,
                stderr=err_stream,
            )
            response.items = items
            response.errors = errors
        else:
            items, ambiguous, errors = _resolve_by_pages(
                query,
                scan_hits,
                pages,
                fetch_one,
                wait=wait,
                stderr=err_stream,
            )
            response.items = items
            response.ambiguous = ambiguous
            response.errors = errors
            if items:
                item = items[0]
                _log(
                    err_stream,
                    f"[search] ok {item.external_id} ({len(item.tags)} tags, pages={item.page_count})",
                )
    finally:
        session.close()

    return response
