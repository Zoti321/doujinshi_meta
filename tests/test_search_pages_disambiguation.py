from __future__ import annotations

from unittest.mock import patch

from doujinshi_meta.models import ComicTagsItem, Source, TagRef
from doujinshi_meta.search import search_tags
from tests.fake_session import FakeSourceSession, search_candidate


def _item(comic_id: str, *, page_count: int | None = None, title: str = "title") -> ComicTagsItem:
    return ComicTagsItem(
        external_id=comic_id,
        title=title,
        tags=[TagRef(kind="tag", name="sample")],
        page_count=page_count,
    )


def test_search_pages_picks_closest_page_count() -> None:
    hits = [
        search_candidate("40", "a", list_page_count=40),
        search_candidate("42", "b", list_page_count=42),
        search_candidate("50", "c", list_page_count=50),
    ]
    fake = FakeSourceSession(
        hits=hits,
        total=3,
        fetch_fn=lambda cid: _item(cid, page_count=int(cid)),
    )

    with patch("doujinshi_meta.search.open_source_session", return_value=fake):
        result = search_tags("keyword", "jmcomic", pages=42, delay=0)

    assert len(result.items) == 1
    assert result.items[0].external_id == "42"
    assert result.items[0].page_count == 42
    assert result.ambiguous == []
    assert fake.fetch_calls == ["42"]


def test_search_pages_tie_goes_to_ambiguous() -> None:
    hits = [
        search_candidate("40", "a", list_page_count=40),
        search_candidate("44", "b", list_page_count=44),
    ]
    fake = FakeSourceSession(
        hits=hits,
        total=2,
        fetch_fn=lambda cid: _item(cid, page_count=int(cid)),
    )

    with patch("doujinshi_meta.search.open_source_session", return_value=fake):
        result = search_tags("keyword", "jmcomic", pages=42, delay=0)

    assert result.items == []
    assert len(result.ambiguous) == 1
    assert result.ambiguous[0].query == "keyword"
    assert {c.external_id for c in result.ambiguous[0].candidates} == {"40", "44"}


def test_search_pages_no_page_data_goes_to_ambiguous() -> None:
    hits = [
        search_candidate("1", "a"),
        search_candidate("2", "b"),
    ]
    fake = FakeSourceSession(
        hits=hits,
        total=2,
        fetch_fn=lambda _cid: _item("1", page_count=None),
    )

    with patch("doujinshi_meta.search.open_source_session", return_value=fake):
        result = search_tags("keyword", "jmcomic", pages=42, delay=0)

    assert result.items == []
    assert len(result.ambiguous) == 1
    assert len(result.ambiguous[0].candidates) == 2


def test_search_without_pages_regression() -> None:
    hits = [
        search_candidate("1", "a", list_page_count=10),
        search_candidate("2", "b", list_page_count=20),
    ]
    fake = FakeSourceSession(hits=hits, total=2, fetch_fn=lambda cid: _item(cid))

    with patch("doujinshi_meta.search.open_source_session", return_value=fake):
        result = search_tags("keyword", "jmcomic", limit=10, delay=0)

    assert len(result.items) == 2
    assert result.ambiguous == []
    assert len(fake.fetch_calls) == 2


def test_search_pages_bika_uses_list_page_count_without_prefetch() -> None:
    """哔咔搜索列表带 pagesCount 时，消歧无需为每条候选 prefetch。"""
    hits = [
        search_candidate("40", "a", list_page_count=40),
        search_candidate("42", "b", list_page_count=42),
    ]
    fake = FakeSourceSession(
        source=Source.BIKA,
        hits=hits,
        total=2,
        fetch_fn=lambda cid: _item(cid, page_count=int(cid)),
    )

    with patch("doujinshi_meta.search.open_source_session", return_value=fake):
        result = search_tags("keyword", "bika", pages=42, delay=0)

    assert len(result.items) == 1
    assert result.items[0].external_id == "42"
    assert fake.fetch_calls == ["42"]
