from __future__ import annotations

from unittest.mock import MagicMock, patch

from doujinshi_meta.models import ComicTagsItem, TagRef
from doujinshi_meta.search import search_tags


def _item(comic_id: str, *, page_count: int | None = None, title: str = "title") -> ComicTagsItem:
    return ComicTagsItem(
        external_id=comic_id,
        title=title,
        tags=[TagRef(kind="tag", name="sample")],
        page_count=page_count,
    )


def test_search_pages_picks_closest_page_count() -> None:
    hits = [("40", "a", 40), ("42", "b", 42), ("50", "c", 50)]

    with (
        patch("doujinshi_meta.search.create_jmcomic_client", return_value=MagicMock()),
        patch("doujinshi_meta.search.search_comics_jmcomic", return_value=(hits, 3)),
        patch(
            "doujinshi_meta.search.fetch_comic_jmcomic",
            side_effect=lambda _client, cid: _item(cid, page_count=int(cid)),
        ) as mock_fetch,
    ):
        result = search_tags("keyword", "jmcomic", pages=42, delay=0)

    assert len(result.items) == 1
    assert result.items[0].external_id == "42"
    assert result.items[0].page_count == 42
    assert result.ambiguous == []
    mock_fetch.assert_called_once()
    assert mock_fetch.call_args[0][1] == "42"


def test_search_pages_tie_goes_to_ambiguous() -> None:
    hits = [("40", "a", 40), ("44", "b", 44)]

    with (
        patch("doujinshi_meta.search.create_jmcomic_client", return_value=MagicMock()),
        patch("doujinshi_meta.search.search_comics_jmcomic", return_value=(hits, 2)),
        patch("doujinshi_meta.search.fetch_comic_jmcomic", side_effect=lambda _c, cid: _item(cid, page_count=int(cid))),
    ):
        result = search_tags("keyword", "jmcomic", pages=42, delay=0)

    assert result.items == []
    assert len(result.ambiguous) == 1
    assert result.ambiguous[0].query == "keyword"
    assert {c.external_id for c in result.ambiguous[0].candidates} == {"40", "44"}


def test_search_pages_no_page_data_goes_to_ambiguous() -> None:
    hits = [("1", "a", None), ("2", "b", None)]

    with (
        patch("doujinshi_meta.search.create_jmcomic_client", return_value=MagicMock()),
        patch("doujinshi_meta.search.search_comics_jmcomic", return_value=(hits, 2)),
        patch(
            "doujinshi_meta.search.fetch_comic_jmcomic",
            return_value=_item("1", page_count=None),
        ),
    ):
        result = search_tags("keyword", "jmcomic", pages=42, delay=0)

    assert result.items == []
    assert len(result.ambiguous) == 1
    assert len(result.ambiguous[0].candidates) == 2


def test_search_without_pages_regression() -> None:
    hits = [("1", "a", 10), ("2", "b", 20)]

    with (
        patch("doujinshi_meta.search.create_jmcomic_client", return_value=MagicMock()),
        patch("doujinshi_meta.search.search_comics_jmcomic", return_value=(hits, 2)),
        patch(
            "doujinshi_meta.search.fetch_comic_jmcomic",
            side_effect=lambda _client, cid: _item(cid),
        ) as mock_fetch,
    ):
        result = search_tags("keyword", "jmcomic", limit=10, delay=0)

    assert len(result.items) == 2
    assert result.ambiguous == []
    assert mock_fetch.call_count == 2
