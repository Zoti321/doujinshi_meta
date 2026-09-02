from __future__ import annotations

import tomllib
from pathlib import Path

from typer.testing import CliRunner

import doujinshi_meta
from doujinshi_meta.cli import app

runner = CliRunner()


def _pyproject_version() -> str:
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    return data["project"]["version"]


def test_djm_version_stdout() -> None:
    expected = _pyproject_version()
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == expected


def test_package_version_matches_pyproject() -> None:
    assert doujinshi_meta.__version__ == _pyproject_version()


def test_package_version_matches_cli() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert doujinshi_meta.__version__ == result.stdout.strip()
