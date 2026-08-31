from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from doujinshi_meta.cli import app
from doujinshi_meta.models import CatalogStats, TagCatalogEntry, TagCatalogResponse

runner = CliRunner()


def _sample_catalog(
    *,
    tags: list[TagCatalogEntry] | None = None,
    kinds: list[str] | None = None,
) -> TagCatalogResponse:
    return TagCatalogResponse(
        source="jmcomic",
        generated_at="2026-08-31T00:00:00Z",
        stats=CatalogStats(albums_scanned=2, tags_unique=1, errors=0),
        kinds=kinds,
        tags=tags
        if tags is not None
        else [
            TagCatalogEntry(kind="tag", name="巨乳", count=10),
        ],
    )


def test_catalog_without_kind_passes_none() -> None:
    with patch("doujinshi_meta.cli.build_catalog") as mock_build:
        mock_build.return_value = _sample_catalog()
        result = runner.invoke(app, ["catalog", "--source", "jmcomic"])

    assert result.exit_code == 0
    mock_build.assert_called_once()
    assert mock_build.call_args.kwargs["kinds"] is None
    payload = json.loads(result.stdout)
    assert "kinds" not in payload


def test_catalog_kind_tag_passes_normalized_kinds() -> None:
    with patch("doujinshi_meta.cli.build_catalog") as mock_build:
        mock_build.return_value = _sample_catalog(kinds=["tag"])
        result = runner.invoke(
            app,
            ["catalog", "--source", "jmcomic", "--kind", "tag"],
        )

    assert result.exit_code == 0
    assert mock_build.call_args.kwargs["kinds"] == ["tag"]
    payload = json.loads(result.stdout)
    assert payload["kinds"] == ["tag"]


def test_catalog_multiple_kinds_deduped_and_sorted() -> None:
    with patch("doujinshi_meta.cli.build_catalog") as mock_build:
        mock_build.return_value = _sample_catalog(kinds=["author", "tag"])
        result = runner.invoke(
            app,
            [
                "catalog",
                "--source",
                "jmcomic",
                "--kind",
                "author",
                "--kind",
                "tag",
                "--kind",
                "author",
            ],
        )

    assert result.exit_code == 0
    assert mock_build.call_args.kwargs["kinds"] == ["author", "tag"]


def test_catalog_invalid_kind_for_source_exits_2() -> None:
    result = runner.invoke(
        app,
        ["catalog", "--source", "jmcomic", "--kind", "category"],
    )

    assert result.exit_code == 2
    assert "category" in result.stderr
    assert "tag" in result.stderr
    assert "parody" in result.stderr


def test_catalog_table_with_kind_shows_filtered_rows() -> None:
    tags = [
        TagCatalogEntry(kind="tag", name="巨乳", count=10),
        TagCatalogEntry(kind="parody", name="原神", count=3),
    ]
    with patch(
        "doujinshi_meta.cli.build_catalog",
        return_value=_sample_catalog(tags=[tags[0]], kinds=["tag"]),
    ):
        result = runner.invoke(
            app,
            ["catalog", "--source", "jmcomic", "--kind", "tag", "--table"],
        )

    assert result.exit_code == 0
    assert "巨乳" in result.stdout
    assert "原神" not in result.stdout


def test_catalog_resume_kind_mismatch_exits_2(tmp_path: Path) -> None:
    checkpoint = tmp_path / "progress.json"
    checkpoint.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "source": "jmcomic",
                "phase": "detail",
                "kinds": ["tag"],
                "seen_ids": [],
                "pending_ids": [],
                "tag_counter": {},
                "stats": {"albums_scanned": 0, "errors": 0},
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "catalog",
            "--source",
            "jmcomic",
            "--kind",
            "author",
            "--checkpoint",
            str(checkpoint),
            "--resume",
        ],
    )

    assert result.exit_code == 2
    assert "kinds" in result.stderr.lower() or "kind" in result.stderr.lower()
