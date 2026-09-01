from __future__ import annotations

from unittest.mock import patch

from doujinshi_meta.models import ComicTagsItem, Source, TagRef
from doujinshi_meta.search import search_tags
from tests.fake_session import FakeSourceSession, search_candidate


def _item(comic_id: str, title: str = "title") -> ComicTagsItem:
    return ComicTagsItem(
        external_id=comic_id,
        title=title,
        tags=[TagRef(kind="tag", name="sample")],
    )


def test_search_tags_jmcomic_returns_items_and_total_hits() -> None:
    hits = [
        search_candidate("1", "a"),
        search_candidate("2", "b"),
        search_candidate("3", "c"),
    ]
    fake = FakeSourceSession(
        hits=hits,
        total=42,
        fetch_fn=lambda cid: _item(cid),
    )

    with patch("doujinshi_meta.search.open_source_session", return_value=fake):
        result = search_tags("keyword", "jmcomic", limit=10, delay=0)

    assert result.command == "search"
    assert result.source == "jmcomic"
    assert result.query == "keyword"
    assert result.total_hits == 42
    assert len(result.items) == 3
    assert result.errors == []
    assert fake.search_calls == ["keyword"]
    assert fake.fetch_calls == ["1", "2", "3"]
    assert fake.closed


def test_search_tags_limit_truncates_fetch_calls() -> None:
    hits = [search_candidate(str(i), f"t{i}") for i in range(20)]
    fake = FakeSourceSession(hits=hits, total=20, fetch_fn=lambda cid: _item(cid))

    with patch("doujinshi_meta.search.open_source_session", return_value=fake):
        result = search_tags("q", "jmcomic", limit=5, delay=0)

    assert len(result.items) == 5
    assert result.total_hits == 20
    assert len(fake.fetch_calls) == 5


def test_search_tags_empty_results() -> None:
    fake = FakeSourceSession(hits=[], total=0)

    with patch("doujinshi_meta.search.open_source_session", return_value=fake):
        result = search_tags("missing", "jmcomic", delay=0)

    assert result.items == []
    assert result.errors == []
    assert result.total_hits == 0


def test_search_tags_detail_failure_records_error() -> None:
    hits = [
        search_candidate("ok", "a"),
        search_candidate("bad", "b"),
        search_candidate("ok2", "c"),
    ]

    def fetch_side_effect(cid: str) -> ComicTagsItem:
        if cid == "bad":
            raise RuntimeError("not found")
        return _item(cid)

    fake = FakeSourceSession(hits=hits, total=3, fetch_fn=fetch_side_effect)

    with patch("doujinshi_meta.search.open_source_session", return_value=fake):
        result = search_tags("q", "jmcomic", delay=0)

    assert len(result.items) == 2
    assert len(result.errors) == 1
    assert result.errors[0].external_id == "bad"
    assert "not found" in result.errors[0].message


def test_search_tags_bika_uses_session() -> None:
    hits = [search_candidate("bika-1", "title", list_page_count=24)]
    fake = FakeSourceSession(
        source=Source.BIKA,
        hits=hits,
        total=1,
        fetch_fn=lambda cid: _item("bika-1"),
    )

    with patch("doujinshi_meta.search.open_source_session", return_value=fake) as mock_open:
        result = search_tags("q", "bika", delay=0)

    assert result.source == "bika"
    assert len(result.items) == 1
    mock_open.assert_called_once()
    assert fake.search_calls == ["q"]
    assert fake.fetch_calls == ["bika-1"]


def test_search_tags_delay_sleeps_between_fetches() -> None:
    hits = [
        search_candidate("1", "a"),
        search_candidate("2", "b"),
        search_candidate("3", "c"),
    ]
    fake = FakeSourceSession(hits=hits, total=3, fetch_fn=lambda cid: _item(cid))

    with (
        patch("doujinshi_meta.search.open_source_session", return_value=fake),
        patch("doujinshi_meta.search.time.sleep") as mock_sleep,
    ):
        search_tags("q", "jmcomic", limit=10, delay=0.5)

    assert mock_sleep.call_count == 2
    mock_sleep.assert_called_with(0.5)
