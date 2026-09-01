from __future__ import annotations

import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import TextIO

from doujinshi_meta.models import (
    ComicTagsItem,
    FetchError,
    SearchAmbiguous,
    SearchTagsResponse,
    Source,
    utc_now_iso,
)
from doujinshi_meta.page_disambiguation import (
    DisambiguationOutcome,
    SearchCandidate,
    decide_by_page_hint,
    enrich_page_counts,
)
from doujinshi_meta.sources.session import DEFAULT_DELAY, open_source_session

FetchOne = Callable[[str], ComicTagsItem]


def _log(stderr: TextIO, message: str) -> None:
    print(message, file=stderr)


def _resolve_by_pages(
    query: str,
    candidates: list[SearchCandidate],
    hint_pages: int,
    fetch_one: FetchOne,
    *,
    wait: float,
    stderr: TextIO,
) -> tuple[list[ComicTagsItem], list[SearchAmbiguous], list[FetchError]]:
    enriched, prefetched = enrich_page_counts(
        candidates,
        fetch_one,
        wait=wait,
        on_fetch_error=lambda external_id, exc: _log(
            stderr, f"[search] skip {external_id}: {exc}"
        ),
    )
    decision = decide_by_page_hint(enriched, hint_pages)

    if decision.outcome == DisambiguationOutcome.NO_PAGE_DATA:
        ambiguous = SearchAmbiguous(
            query=query,
            candidates=[c.to_ambiguous_candidate() for c in decision.all_candidates],
        )
        return [], [ambiguous], []

    if decision.outcome == DisambiguationOutcome.AMBIGUOUS:
        ambiguous = SearchAmbiguous(
            query=query,
            candidates=[c.to_ambiguous_candidate() for c in decision.tied],
        )
        return [], [ambiguous], []

    winner = decision.winner
    assert winner is not None
    if winner.external_id in prefetched:
        return [prefetched[winner.external_id]], [], []

    try:
        item = fetch_one(winner.external_id)
        return [item], [], []
    except Exception as exc:
        _log(stderr, f"[search] error {winner.external_id}: {exc}")
        return [], [], [FetchError(external_id=winner.external_id, message=str(exc))]


def _fetch_hits_without_pages(
    candidates: list[SearchCandidate],
    limit: int,
    fetch_one: FetchOne,
    *,
    wait: float,
    stderr: TextIO,
) -> tuple[list[ComicTagsItem], list[FetchError]]:
    items: list[ComicTagsItem] = []
    errors: list[FetchError] = []

    for index, candidate in enumerate(candidates):
        if index > 0:
            time.sleep(wait)
        comic_id = candidate.external_id.strip()
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
        candidates, total_hits = session.search(query)
        response.total_hits = total_hits
        _log(err_stream, f"[search] {len(candidates)} hits (total {total_hits}) for {query!r}")

        fetch_one = session.fetch_comic
        scan_candidates = candidates[:limit]
        if pages is None:
            items, errors = _fetch_hits_without_pages(
                scan_candidates,
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
                scan_candidates,
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
