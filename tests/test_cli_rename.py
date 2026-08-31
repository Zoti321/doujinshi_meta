from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from doujinshi_meta.cli import app, run

runner = CliRunner()


def test_cli_help_uses_djm_name() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage: djm" in result.stdout


def test_run_invokes_app(monkeypatch) -> None:
    called: list[bool] = []

    monkeypatch.setattr("doujinshi_meta.cli.app", lambda: called.append(True))

    run()

    assert called == [True]


def test_pyproject_scripts_only_djm() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert 'djm = "doujinshi_meta.cli:run"' in text
    assert "dtg =" not in text
