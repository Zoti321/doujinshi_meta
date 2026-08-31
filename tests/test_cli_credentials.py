from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from doujinshi_meta.cli import app
from doujinshi_meta.config import save_bika_credentials, save_config, UserConfig

runner = CliRunner()


def test_config_show_masks_bika_account(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    save_config(UserConfig(proxy=None), config_path)
    save_bika_credentials("alice@example.com", "secret", path=tmp_path / "credentials.toml")

    result = runner.invoke(app, ["config", "show", "--config", str(config_path)])

    assert result.exit_code == 0
    assert "a***m" in result.stdout or "alice" not in result.stdout.lower()
    assert "secret" not in result.stdout
    assert "bika_account:" in result.stdout


def test_config_unset_bika_credentials(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    cred_path = tmp_path / "credentials.toml"
    save_config(UserConfig(proxy="http://127.0.0.1:7890"), config_path)
    save_bika_credentials("alice@example.com", "secret", path=cred_path)

    result = runner.invoke(
        app, ["config", "unset", "bika-credentials", "--config", str(config_path)]
    )

    assert result.exit_code == 0
    assert not cred_path.exists()
