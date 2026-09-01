from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from doujinshi_meta.models import (
    AmbiguousCandidate,
    BatchScrapeItem,
    ComicTagsItem,
    SearchAmbiguous,
    SearchTagsResponse,
    TagRef,
)
from doujinshi_meta.search_batch import search_batch_tags


def _search_result(*, items: list[ComicTagsItem] | None = None, ambiguous: bool = False) -> SearchTagsResponse:
    if ambiguous:
        return SearchTagsResponse(
            source="jmcomic",
            query="title",
            total_hits=2,
            generated_at="2026-09-01T00:00:00Z",
            ambiguous=[
                SearchAmbiguous(
                    query="title",
                    candidates=[
                        AmbiguousCandidate(external_id="1", title="a", page_count=40),
                        AmbiguousCandidate(external_id="2", title="b", page_count=44),
                    ],
                )
            ],
        )
    return SearchTagsResponse(
        source="jmcomic",
        query="title",
        total_hits=1,
        generated_at="2026-09-01T00:00:00Z",
        items=items
        or [
            ComicTagsItem(
                external_id="410090",
                title="Sample",
                tags=[TagRef(kind="tag", name="全彩")],
                page_count=42,
            )
        ],
    )


def test_search_batch_tags_mixed_rows(tmp_path: Path) -> None:
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

    def side_effect(_session, title: str, **_kwargs) -> SearchTagsResponse:
        if title == "Good":
            return _search_result()
        if title == "Tie":
            return _search_result(ambiguous=True)
        return SearchTagsResponse(
            source="jmcomic",
            query=title,
            total_hits=0,
            generated_at="2026-09-01T00:00:00Z",
            items=[],
        )

    with (
        patch("doujinshi_meta.search_batch.open_source_session") as mock_open,
        patch("doujinshi_meta.search_batch.search_tags_with_session", side_effect=side_effect),
    ):
        mock_open.return_value = MagicMock()
        result = search_batch_tags(input_path, "jmcomic", delay=0)

    mock_open.assert_called_once()
    assert result.command == "search-batch"
    assert len(result.items) == 1
    assert result.items[0].local_id == "ok"
    assert result.items[0].external_id == "410090"
    assert len(result.ambiguous) == 1
    assert result.ambiguous[0].local_id == "ambig"
    assert len(result.errors) == 2
    error_ids = {err.local_id for err in result.errors}
    assert error_ids == {"bad", "line:4"}


def test_search_batch_tags_empty_valid_rows_raises(tmp_path: Path) -> None:
    input_path = tmp_path / "empty.jsonl"
    input_path.write_text("# comment only\n", encoding="utf-8")

    with (
        patch("doujinshi_meta.search_batch.open_source_session") as mock_open,
        patch("doujinshi_meta.search_batch.search_tags_with_session") as mock_search,
    ):
        try:
            search_batch_tags(input_path, "jmcomic", delay=0)
        except RuntimeError as exc:
            assert "无有效行" in str(exc)
        else:
            raise AssertionError("expected RuntimeError")
        mock_open.assert_not_called()
        mock_search.assert_not_called()
