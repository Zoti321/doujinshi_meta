from __future__ import annotations

from typer.testing import CliRunner

from doujinshi_meta.cli import app, run

runner = CliRunner()


def test_cli_help_uses_djm_name() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage: djm" in result.stdout


def test_run_warns_when_invoked_as_dtg(monkeypatch, capsys) -> None:
    called: list[bool] = []
    monkeypatch.setattr("sys.argv", [r"C:\bin\dtg.exe"])
    monkeypatch.setattr("doujinshi_meta.cli.app", lambda: called.append(True))

    run()

    assert called == [True]
    err = capsys.readouterr().err
    assert "已弃用" in err
    assert "`djm`" in err


def test_run_silent_when_invoked_as_djm(monkeypatch, capsys) -> None:
    monkeypatch.setattr("sys.argv", ["djm"])
    monkeypatch.setattr("doujinshi_meta.cli.app", lambda: None)

    run()

    assert "已弃用" not in capsys.readouterr().err
