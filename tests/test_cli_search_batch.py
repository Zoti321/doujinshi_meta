from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from doujinshi_meta.cli import app
from doujinshi_meta.models import (
    BatchAmbiguous,
    BatchError,
    BatchScrapeItem,
    SearchBatchResponse,
    SearchTagsResponse,
    TagRef,
)

runner = CliRunner()


def test_search_passes_pages_to_library() -> None:
    response = SearchTagsResponse(
        source="jmcomic",
        query="kw",
        total_hits=1,
        generated_at="2026-09-01T00:00:00Z",
    )
    with patch("doujinshi_meta.cli.search_tags", return_value=response) as mock_search:
        result = runner.invoke(
            app,
            ["search", "--source", "jmcomic", "kw", "--pages", "42"],
        )

    assert result.exit_code == 0
    mock_search.assert_called_once()
    assert mock_search.call_args.kwargs["pages"] == 42


def test_search_batch_stdout_json(tmp_path: Path) -> None:
    input_path = tmp_path / "books.jsonl"
    input_path.write_text('{"local_id":"1","title":"T"}\n', encoding="utf-8")
    response = SearchBatchResponse(
        source="jmcomic",
        generated_at="2026-09-01T00:00:00Z",
        items=[
            BatchScrapeItem(
                local_id="1",
                external_id="410090",
                title="T",
                tags=[TagRef(kind="tag", name="全彩")],
                page_count=42,
            )
        ],
    )
    with patch("doujinshi_meta.cli.search_batch_tags", return_value=response):
        result = runner.invoke(
            app,
            ["search-batch", "--source", "jmcomic", "--input", str(input_path)],
        )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["command"] == "search-batch"
    assert payload["items"][0]["local_id"] == "1"


def test_search_batch_partial_exit_1(tmp_path: Path) -> None:
    input_path = tmp_path / "books.jsonl"
    input_path.write_text('{"local_id":"1","title":"T"}\n', encoding="utf-8")
    response = SearchBatchResponse(
        source="jmcomic",
        generated_at="2026-09-01T00:00:00Z",
        items=[
            BatchScrapeItem(
                local_id="1",
                external_id="410090",
                title="T",
                tags=[TagRef(kind="tag", name="全彩")],
            )
        ],
        ambiguous=[
            BatchAmbiguous(local_id="2", title="U", candidates=[]),
        ],
    )
    with patch("doujinshi_meta.cli.search_batch_tags", return_value=response):
        result = runner.invoke(
            app,
            ["search-batch", "--source", "jmcomic", "--input", str(input_path)],
        )

    assert result.exit_code == 1


def test_search_batch_all_errors_exit_2(tmp_path: Path) -> None:
    input_path = tmp_path / "books.jsonl"
    input_path.write_text('{"local_id":"1","title":"T"}\n', encoding="utf-8")
    response = SearchBatchResponse(
        source="jmcomic",
        generated_at="2026-09-01T00:00:00Z",
        errors=[BatchError(local_id="1", message="fail")],
    )
    with patch("doujinshi_meta.cli.search_batch_tags", return_value=response):
        result = runner.invoke(
            app,
            ["search-batch", "--source", "jmcomic", "--input", str(input_path)],
        )

    assert result.exit_code == 2
