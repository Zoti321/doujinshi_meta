from __future__ import annotations

from unittest.mock import patch

from doujinshi_meta.models import ComicTagsItem, TagRef
from doujinshi_meta.search import search_tags
from tests.fake_session import FakeSourceSession


def _item(comic_id: str, *, page_count: int | None = None, title: str = "title") -> ComicTagsItem:
    return ComicTagsItem(
        external_id=comic_id,
        title=title,
        tags=[TagRef(kind="tag", name="sample")],
        page_count=page_count,
    )


def test_search_pages_picks_closest_page_count() -> None:
    hits = [("40", "a", 40), ("42", "b", 42), ("50", "c", 50)]
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
    hits = [("40", "a", 40), ("44", "b", 44)]
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
    hits = [("1", "a", None), ("2", "b", None)]
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
    hits = [("1", "a", 10), ("2", "b", 20)]
    fake = FakeSourceSession(hits=hits, total=2, fetch_fn=lambda cid: _item(cid))

    with patch("doujinshi_meta.search.open_source_session", return_value=fake):
        result = search_tags("keyword", "jmcomic", limit=10, delay=0)

    assert len(result.items) == 2
    assert result.ambiguous == []
    assert len(fake.fetch_calls) == 2
