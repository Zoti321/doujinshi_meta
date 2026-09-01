from __future__ import annotations

import json
from unittest.mock import patch

from typer.testing import CliRunner

from doujinshi_meta.cli import app
from doujinshi_meta.models import ComicTagsItem, FetchError, SearchTagsResponse, TagRef

runner = CliRunner()


def _sample_search(*, items: list[ComicTagsItem] | None = None) -> SearchTagsResponse:
    return SearchTagsResponse(
        source="jmcomic",
        query="keyword",
        total_hits=1,
        generated_at="2026-09-01T00:00:00Z",
        items=items
        if items is not None
        else [
            ComicTagsItem(
                external_id="410090",
                title="Sample",
                tags=[TagRef(kind="tag", name="全彩")],
            )
        ],
    )


def test_search_stdout_json() -> None:
    with patch("doujinshi_meta.cli.search_tags", return_value=_sample_search()):
        result = runner.invoke(
            app,
            ["search", "--source", "jmcomic", "keyword"],
        )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["command"] == "search"
    assert payload["query"] == "keyword"
    assert payload["total_hits"] == 1
    assert payload["items"][0]["external_id"] == "410090"


def test_search_empty_query_exits_2() -> None:
    with patch("doujinshi_meta.cli.search_tags") as mock_search:
        result = runner.invoke(app, ["search", "--source", "jmcomic", "   "])

    assert result.exit_code == 2
    mock_search.assert_not_called()


def test_search_partial_errors_exit_1() -> None:
    response = _sample_search()
    response.errors.append(FetchError(external_id="bad", message="fail"))
    with patch("doujinshi_meta.cli.search_tags", return_value=response):
        result = runner.invoke(app, ["search", "--source", "jmcomic", "kw"])

    assert result.exit_code == 1


def test_search_all_errors_exit_2() -> None:
    response = SearchTagsResponse(
        source="jmcomic",
        query="kw",
        total_hits=1,
        generated_at="2026-09-01T00:00:00Z",
        items=[],
        errors=[FetchError(external_id="bad", message="fail")],
    )
    with patch("doujinshi_meta.cli.search_tags", return_value=response):
        result = runner.invoke(app, ["search", "--source", "jmcomic", "kw"])

    assert result.exit_code == 2
