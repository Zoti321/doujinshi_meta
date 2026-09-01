from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from doujinshi_meta.models import (
    AmbiguousCandidate,
    ComicTagsItem,
    SearchAmbiguous,
    TagRef,
)
from doujinshi_meta.page_disambiguation import SearchCandidate
from doujinshi_meta.search_batch import search_batch_tags
from tests.fake_session import FakeSourceSession, search_candidate


def _item(external_id: str = "410090", title: str = "Sample") -> ComicTagsItem:
    return ComicTagsItem(
        external_id=external_id,
        title=title,
        tags=[TagRef(kind="tag", name="全彩")],
        page_count=42,
    )


def test_search_batch_opens_session_once(tmp_path: Path) -> None:
    input_path = tmp_path / "books.jsonl"
    input_path.write_text(
        "\n".join(
            [
                '{"local_id":"a","title":"One"}',
                '{"local_id":"b","title":"Two"}',
                '{"local_id":"c","title":"Three"}',
            ]
        ),
        encoding="utf-8",
    )
    fake = FakeSourceSession(
        fetch_fn=lambda _cid: _item(),
        search_fn=lambda _title: ([search_candidate("410090", "Sample")], 1),
    )

    with patch("doujinshi_meta.search_batch.open_source_session", return_value=fake) as mock_open:
        result = search_batch_tags(input_path, "jmcomic", delay=0)

    mock_open.assert_called_once()
    assert fake.closed
    assert len(result.items) == 3
    assert len(fake.search_calls) == 3


def test_search_batch_sleep_between_rows_not_inside_search(tmp_path: Path) -> None:
    input_path = tmp_path / "books.jsonl"
    input_path.write_text(
        '{"local_id":"a","title":"One"}\n{"local_id":"b","title":"Two"}\n',
        encoding="utf-8",
    )
    fake = FakeSourceSession(
        fetch_fn=lambda _cid: _item(),
        search_fn=lambda _title: ([search_candidate("410090")], 1),
    )

    with (
        patch("doujinshi_meta.search_batch.open_source_session", return_value=fake),
        patch("doujinshi_meta.search_batch.time.sleep") as mock_sleep,
        patch("doujinshi_meta.search_batch.search_tags_with_session") as mock_search,
    ):
        from doujinshi_meta.models import SearchTagsResponse

        mock_search.return_value = SearchTagsResponse(
            source="jmcomic",
            query="One",
            total_hits=1,
            generated_at="2026-09-01T00:00:00Z",
            items=[_item()],
        )
        search_batch_tags(input_path, "jmcomic", delay=1.5)

    mock_sleep.assert_called_once_with(1.5)
    assert mock_search.call_count == 2
    assert all(call.kwargs.get("delay") == 0 for call in mock_search.call_args_list)


def test_search_batch_mixed_rows_with_session(tmp_path: Path) -> None:
    input_path = tmp_path / "books.jsonl"
    input_path.write_text(
        "\n".join(
            [
                '{"local_id":"ok","title":"Good","pages":42}',
                '{"local_id":"ambig","title":"Tie","pages":42}',
                '{"local_id":"bad","title":"Broken"}',
                "not json",
            ]
        ),
        encoding="utf-8",
    )

    def search_fn(title: str) -> tuple[list[SearchCandidate], int]:
        if title == "Good":
            return [search_candidate("410090", "Sample", list_page_count=42)], 1
        if title == "Tie":
            return [
                search_candidate("1", "a", list_page_count=40),
                search_candidate("2", "b", list_page_count=44),
            ], 2
        return [], 0

    fake = FakeSourceSession(
        fetch_fn=lambda cid: _item(external_id=cid, title=cid),
        search_fn=search_fn,
    )

    with patch("doujinshi_meta.search_batch.open_source_session", return_value=fake):
        result = search_batch_tags(input_path, "jmcomic", delay=0)

    assert result.command == "search-batch"
    assert len(result.items) == 1
    assert result.items[0].local_id == "ok"
    assert len(result.ambiguous) == 1
    assert result.ambiguous[0].local_id == "ambig"
    assert len(result.errors) == 2
