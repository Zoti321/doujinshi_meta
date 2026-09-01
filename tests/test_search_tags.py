from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from doujinshi_meta.models import ComicTagsItem, TagRef
from doujinshi_meta.search import search_tags


def _item(comic_id: str, title: str = "title") -> ComicTagsItem:
    return ComicTagsItem(
        external_id=comic_id,
        title=title,
        tags=[TagRef(kind="tag", name="sample")],
    )


def test_search_tags_jmcomic_returns_items_and_total_hits() -> None:
    hits = [("1", "a"), ("2", "b"), ("3", "c")]

    with (
        patch("doujinshi_meta.search.create_jmcomic_client", return_value=MagicMock()),
        patch("doujinshi_meta.search.search_comics_jmcomic", return_value=(hits, 42)) as mock_search,
        patch(
            "doujinshi_meta.search.fetch_comic_jmcomic",
            side_effect=lambda _client, cid: _item(cid),
        ) as mock_fetch,
    ):
        result = search_tags("keyword", "jmcomic", limit=10, delay=0)

    assert result.command == "search"
    assert result.source == "jmcomic"
    assert result.query == "keyword"
    assert result.total_hits == 42
    assert len(result.items) == 3
    assert result.errors == []
    mock_search.assert_called_once()
    assert mock_fetch.call_count == 3


def test_search_tags_limit_truncates_fetch_calls() -> None:
    hits = [(str(i), f"t{i}") for i in range(20)]

    with (
        patch("doujinshi_meta.search.create_jmcomic_client", return_value=MagicMock()),
        patch("doujinshi_meta.search.search_comics_jmcomic", return_value=(hits, 20)),
        patch(
            "doujinshi_meta.search.fetch_comic_jmcomic",
            side_effect=lambda _client, cid: _item(cid),
        ) as mock_fetch,
    ):
        result = search_tags("q", "jmcomic", limit=5, delay=0)

    assert len(result.items) == 5
    assert result.total_hits == 20
    assert mock_fetch.call_count == 5


def test_search_tags_empty_results() -> None:
    with (
        patch("doujinshi_meta.search.create_jmcomic_client", return_value=MagicMock()),
        patch("doujinshi_meta.search.search_comics_jmcomic", return_value=([], 0)),
    ):
        result = search_tags("missing", "jmcomic", delay=0)

    assert result.items == []
    assert result.errors == []
    assert result.total_hits == 0


def test_search_tags_detail_failure_records_error() -> None:
    hits = [("ok", "a"), ("bad", "b"), ("ok2", "c")]

    def fetch_side_effect(_client, cid: str) -> ComicTagsItem:
        if cid == "bad":
            raise RuntimeError("not found")
        return _item(cid)

    with (
        patch("doujinshi_meta.search.create_jmcomic_client", return_value=MagicMock()),
        patch("doujinshi_meta.search.search_comics_jmcomic", return_value=(hits, 3)),
        patch("doujinshi_meta.search.fetch_comic_jmcomic", side_effect=fetch_side_effect),
    ):
        result = search_tags("q", "jmcomic", delay=0)

    assert len(result.items) == 2
    assert len(result.errors) == 1
    assert result.errors[0].external_id == "bad"
    assert "not found" in result.errors[0].message


def test_search_tags_bika_uses_bika_ops() -> None:
    hits = [("bika-1", "title")]

    with (
        patch("doujinshi_meta.search.open_bika_client") as mock_open,
        patch("doujinshi_meta.search.search_comics_bika", return_value=(hits, 1)) as mock_search,
        patch(
            "doujinshi_meta.search.fetch_comic_bika",
            return_value=_item("bika-1"),
        ) as mock_fetch,
    ):
        mock_client = MagicMock()
        mock_open.return_value = mock_client
        result = search_tags("q", "bika", delay=0)

    assert result.source == "bika"
    assert len(result.items) == 1
    mock_search.assert_called_once_with(mock_client, "q")
    mock_fetch.assert_called_once_with(mock_client, "bika-1")


def test_search_tags_delay_sleeps_between_fetches() -> None:
    hits = [("1", "a"), ("2", "b"), ("3", "c")]

    with (
        patch("doujinshi_meta.search.create_jmcomic_client", return_value=MagicMock()),
        patch("doujinshi_meta.search.search_comics_jmcomic", return_value=(hits, 3)),
        patch(
            "doujinshi_meta.search.fetch_comic_jmcomic",
            side_effect=lambda _client, cid: _item(cid),
        ),
        patch("doujinshi_meta.search.time.sleep") as mock_sleep,
    ):
        search_tags("q", "jmcomic", limit=10, delay=0.5)

    assert mock_sleep.call_count == 2
    mock_sleep.assert_called_with(0.5)

