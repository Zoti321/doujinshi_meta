from __future__ import annotations

from pathlib import Path

import pytest

from doujinshi_meta.config import (
    load_bika_credentials,
    load_config,
    require_bika_credentials,
    resolve_proxy,
    save_bika_credentials,
    save_config,
    UserConfig,
)


def test_resolve_proxy_uses_djm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DJM_PROXY", "http://new:1")
    monkeypatch.delenv("DTG_PROXY", raising=False)

    assert resolve_proxy() == "http://new:1"


def test_resolve_proxy_ignores_dtg_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DJM_PROXY", raising=False)
    monkeypatch.setenv("DTG_PROXY", "http://old:1")

    assert resolve_proxy() is None


def test_bika_env_uses_djm_when_both_prefixes_set(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DJM_BIKA_ACCOUNT", "new@example.com")
    monkeypatch.setenv("DJM_BIKA_PASSWORD", "new-pass")
    monkeypatch.setenv("DTG_BIKA_ACCOUNT", "old@example.com")
    monkeypatch.setenv("DTG_BIKA_PASSWORD", "old-pass")

    creds = require_bika_credentials(credentials_path=tmp_path / "credentials.toml")

    assert creds.account == "new@example.com"
    assert creds.password == "new-pass"


def test_bika_env_ignores_legacy_dtg_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("DJM_BIKA_ACCOUNT", raising=False)
    monkeypatch.delenv("DJM_BIKA_PASSWORD", raising=False)
    monkeypatch.setenv("DTG_BIKA_ACCOUNT", "old@example.com")
    monkeypatch.setenv("DTG_BIKA_EMAIL", "legacy@example.com")
    monkeypatch.setenv("DTG_BIKA_PASSWORD", "old-pass")

    creds = require_bika_credentials(
        prompt=lambda _msg: "typed@example.com",
        get_password=lambda _msg: "typed-pass",
        credentials_path=tmp_path / "credentials.toml",
    )

    assert creds.account == "typed@example.com"
    assert creds.password == "typed-pass"
    assert creds.from_interactive is True


def test_load_config_does_not_migrate_from_legacy_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    legacy = tmp_path / "doujinshi-tag-getter"
    new = tmp_path / "doujinshi-meta"
    legacy.mkdir()
    (legacy / "config.toml").write_text('proxy = "http://127.0.0.1:7890"\n', encoding="utf-8")
    monkeypatch.setattr("doujinshi_meta.config.config_dir", lambda: new)

    cfg = load_config()

    assert cfg.proxy is None
    assert not (new / "config.toml").exists()


def test_load_config_reads_existing_config_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    new = tmp_path / "doujinshi-meta"
    new.mkdir()
    (new / "config.toml").write_text('proxy = "http://127.0.0.1:7890"\n', encoding="utf-8")
    monkeypatch.setattr("doujinshi_meta.config.config_dir", lambda: new)

    cfg = load_config()

    assert cfg.proxy == "http://127.0.0.1:7890"


def test_save_config_comment_uses_product_name(tmp_path: Path) -> None:
    path = save_config(UserConfig(proxy=None), tmp_path / "config.toml")
    text = path.read_text(encoding="utf-8")
    assert "doujinshi-meta" in text
    assert "doujinshi-tag-getter" not in text


def test_save_config_writes_to_config_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    new = tmp_path / "doujinshi-meta"
    monkeypatch.setattr("doujinshi_meta.config.config_dir", lambda: new)

    path = save_config(UserConfig(proxy="http://new:1"))

    assert path.parent == new
    assert path.read_text(encoding="utf-8").startswith("# doujinshi-meta")


def test_save_credentials_comment_uses_product_name(tmp_path: Path) -> None:
    path = save_bika_credentials("a@b.c", "x", path=tmp_path / "credentials.toml")
    text = path.read_text(encoding="utf-8")
    assert "doujinshi-meta" in text
    assert "doujinshi-tag-getter" not in text
