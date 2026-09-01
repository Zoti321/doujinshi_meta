from __future__ import annotations

from doujinshi_meta.models import AmbiguousCandidate, ComicTagsItem, TagRef
from doujinshi_meta.page_disambiguation import (
    DisambiguationOutcome,
    EnrichedCandidate,
    SearchCandidate,
    decide_by_page_hint,
    enrich_page_counts,
)


def _candidate(
    external_id: str,
    *,
    title: str = "t",
    list_page_count: int | None = None,
) -> SearchCandidate:
    return SearchCandidate(
        external_id=external_id,
        title=title,
        list_page_count=list_page_count,
    )


def _enriched(candidate: SearchCandidate, page_count: int | None) -> EnrichedCandidate:
    return EnrichedCandidate(candidate=candidate, page_count=page_count)


def test_decide_picks_closest_page_count() -> None:
    enriched = [
        _enriched(_candidate("40", list_page_count=40), 40),
        _enriched(_candidate("42", list_page_count=42), 42),
        _enriched(_candidate("50", list_page_count=50), 50),
    ]

    decision = decide_by_page_hint(enriched, 42)

    assert decision.outcome == DisambiguationOutcome.UNIQUE
    assert decision.winner is not None
    assert decision.winner.external_id == "42"


def test_decide_tie_goes_to_ambiguous() -> None:
    enriched = [
        _enriched(_candidate("40"), 40),
        _enriched(_candidate("44"), 44),
    ]

    decision = decide_by_page_hint(enriched, 42)

    assert decision.outcome == DisambiguationOutcome.AMBIGUOUS
    assert {c.external_id for c in decision.tied} == {"40", "44"}


def test_decide_no_page_data() -> None:
    enriched = [
        _enriched(_candidate("1"), None),
        _enriched(_candidate("2"), None),
    ]

    decision = decide_by_page_hint(enriched, 42)

    assert decision.outcome == DisambiguationOutcome.NO_PAGE_DATA
    assert len(decision.all_candidates) == 2


def test_decide_empty_candidates() -> None:
    decision = decide_by_page_hint([], 42)

    assert decision.outcome == DisambiguationOutcome.NO_PAGE_DATA
    assert decision.all_candidates == ()


def test_search_candidate_to_ambiguous_candidate() -> None:
    candidate = _candidate("x", title="Title", list_page_count=10)

    assert candidate.to_ambiguous_candidate() == AmbiguousCandidate(
        external_id="x",
        title="Title",
        page_count=10,
    )


def _item(comic_id: str, *, page_count: int | None = None) -> ComicTagsItem:
    return ComicTagsItem(
        external_id=comic_id,
        title="title",
        tags=[TagRef(kind="tag", name="sample")],
        page_count=page_count,
    )


def test_enrich_page_counts_uses_list_page_count_when_present() -> None:
    candidates = [_candidate("1", list_page_count=24)]

    enriched, prefetched = enrich_page_counts(candidates, lambda _cid: _item("1", page_count=99))

    assert enriched == [_enriched(candidates[0], 24)]
    assert prefetched == {}


def test_enrich_page_counts_fetches_missing_page_count() -> None:
    candidates = [_candidate("1", list_page_count=None)]
    fetched: list[str] = []

    def fetch(cid: str) -> ComicTagsItem:
        fetched.append(cid)
        return _item(cid, page_count=42)

    enriched, prefetched = enrich_page_counts(candidates, fetch, wait=0)

    assert fetched == ["1"]
    assert enriched == [_enriched(candidates[0], 42)]
    assert "1" in prefetched


def test_enrich_page_counts_skips_failed_fetch() -> None:
    candidates = [_candidate("bad", list_page_count=None)]
    errors: list[str] = []

    def fetch(_cid: str) -> ComicTagsItem:
        raise RuntimeError("boom")

    enriched, prefetched = enrich_page_counts(
        candidates,
        fetch,
        on_fetch_error=lambda cid, _exc: errors.append(cid),
    )

    assert errors == ["bad"]
    assert enriched == [_enriched(candidates[0], None)]
    assert prefetched == {}

