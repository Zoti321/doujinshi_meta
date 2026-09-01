from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum

from doujinshi_meta.models import AmbiguousCandidate, ComicTagsItem


@dataclass(frozen=True)
class SearchCandidate:
    external_id: str
    title: str
    list_page_count: int | None = None

    def to_ambiguous_candidate(self) -> AmbiguousCandidate:
        return AmbiguousCandidate(
            external_id=self.external_id,
            title=self.title,
            page_count=self.list_page_count,
        )


@dataclass(frozen=True)
class EnrichedCandidate:
    candidate: SearchCandidate
    page_count: int | None


class DisambiguationOutcome(StrEnum):
    UNIQUE = "unique"
    AMBIGUOUS = "ambiguous"
    NO_PAGE_DATA = "no_page_data"


@dataclass(frozen=True)
class DisambiguationDecision:
    outcome: DisambiguationOutcome
    winner: SearchCandidate | None = None
    tied: tuple[SearchCandidate, ...] = ()
    all_candidates: tuple[SearchCandidate, ...] = ()


def decide_by_page_hint(
    enriched: Sequence[EnrichedCandidate],
    hint_pages: int,
) -> DisambiguationDecision:
    if not enriched:
        return DisambiguationDecision(
            outcome=DisambiguationOutcome.NO_PAGE_DATA,
            all_candidates=(),
        )

    with_pages = [
        entry for entry in enriched if entry.page_count is not None
    ]
    if not with_pages:
        return DisambiguationDecision(
            outcome=DisambiguationOutcome.NO_PAGE_DATA,
            all_candidates=tuple(entry.candidate for entry in enriched),
        )

    min_diff = min(abs(entry.page_count - hint_pages) for entry in with_pages)
    winners = [
        entry.candidate
        for entry in with_pages
        if abs(entry.page_count - hint_pages) == min_diff
    ]

    if len(winners) > 1:
        return DisambiguationDecision(
            outcome=DisambiguationOutcome.AMBIGUOUS,
            tied=tuple(winners),
        )

    return DisambiguationDecision(
        outcome=DisambiguationOutcome.UNIQUE,
        winner=winners[0],
    )


def enrich_page_counts(
    candidates: Sequence[SearchCandidate],
    fetch_comic: Callable[[str], ComicTagsItem],
    *,
    wait: float = 0,
    sleep: Callable[[float], None] = time.sleep,
    on_fetch_error: Callable[[str, Exception], None] | None = None,
) -> tuple[list[EnrichedCandidate], dict[str, ComicTagsItem]]:
    enriched: list[EnrichedCandidate] = []
    prefetched: dict[str, ComicTagsItem] = {}

    for index, candidate in enumerate(candidates):
        page_count = candidate.list_page_count
        if page_count is None:
            if index > 0 and wait:
                sleep(wait)
            try:
                item = fetch_comic(candidate.external_id)
                prefetched[candidate.external_id] = item
                page_count = item.page_count
            except Exception as exc:
                if on_fetch_error is not None:
                    on_fetch_error(candidate.external_id, exc)
        enriched.append(EnrichedCandidate(candidate=candidate, page_count=page_count))

    return enriched, prefetched
