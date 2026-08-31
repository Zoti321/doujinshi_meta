from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from doujinshi_meta.cli import app
from doujinshi_meta.models import CatalogStats, TagCatalogEntry, TagCatalogResponse

runner = CliRunner()


def _sample_catalog(*, tags: list[TagCatalogEntry] | None = None) -> TagCatalogResponse:
    return TagCatalogResponse(
        source="jmcomic",
        generated_at="2026-08-31T00:00:00Z",
        stats=CatalogStats(albums_scanned=2, tags_unique=2, errors=0),
        tags=tags
        if tags is not None
        else [
            TagCatalogEntry(kind="tag", name="巨乳", count=10),
            TagCatalogEntry(kind="parody", name="原神", count=3),
        ],
    )


def test_catalog_table_prints_kind_name_count() -> None:
    with patch(
        "doujinshi_meta.cli.build_catalog",
        return_value=_sample_catalog(),
    ):
        result = runner.invoke(app, ["catalog", "--source", "jmcomic", "--table"])

    assert result.exit_code == 0
    out = result.stdout
    assert "kind" in out
    assert "name" in out
    assert "count" in out
    assert "巨乳" in out
    assert "原神" in out
    assert "10" in out
    assert "3" in out
    # Not JSON payload
    assert not out.lstrip().startswith("{")
    assert "schema_version" not in out
    assert "generated_at" not in out


def test_catalog_default_still_json() -> None:
    with patch(
        "doujinshi_meta.cli.build_catalog",
        return_value=_sample_catalog(),
    ):
        result = runner.invoke(app, ["catalog", "--source", "jmcomic"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["command"] == "catalog"
    assert payload["tags"][0]["name"] == "巨乳"
    assert payload["tags"][0]["count"] == 10


def test_catalog_table_empty_tags_prints_header_only() -> None:
    with patch(
        "doujinshi_meta.cli.build_catalog",
        return_value=_sample_catalog(tags=[]),
    ):
        result = runner.invoke(app, ["catalog", "--source", "jmcomic", "--table"])

    assert result.exit_code == 0
    out = result.stdout
    assert "kind" in out
    assert "name" in out
    assert "count" in out
    assert not out.lstrip().startswith("{")
    assert "schema_version" not in out


def test_catalog_table_and_output_are_mutually_exclusive(tmp_path: Path) -> None:
    out_path = tmp_path / "tags.json"
    with patch(
        "doujinshi_meta.cli.build_catalog",
        return_value=_sample_catalog(),
    ) as mock_build:
        result = runner.invoke(
            app,
            [
                "catalog",
                "--source",
                "jmcomic",
                "--table",
                "-o",
                str(out_path),
            ],
        )

    assert result.exit_code == 2
    assert "--table" in result.stderr
    assert "-o" in result.stderr or "output" in result.stderr
    mock_build.assert_not_called()
    assert not out_path.exists()


def test_catalog_table_preserves_tag_order() -> None:
    tags = [
        TagCatalogEntry(kind="tag", name="first", count=100),
        TagCatalogEntry(kind="tag", name="second", count=50),
        TagCatalogEntry(kind="author", name="third", count=1),
    ]
    with patch(
        "doujinshi_meta.cli.build_catalog",
        return_value=_sample_catalog(tags=tags),
    ):
        result = runner.invoke(app, ["catalog", "--source", "jmcomic", "--table"])

    assert result.exit_code == 0
    first_idx = result.stdout.index("first")
    second_idx = result.stdout.index("second")
    third_idx = result.stdout.index("third")
    assert first_idx < second_idx < third_idx
