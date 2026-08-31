from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from doujinshi_meta.config import (
    load_bika_credentials,
    load_config,
    migrate_user_config,
    require_bika_credentials,
    resolve_proxy,
    save_bika_credentials,
    save_config,
    UserConfig,
)


def test_resolve_proxy_prefers_djm_over_dtg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DJM_PROXY", "http://new:1")
    monkeypatch.setenv("DTG_PROXY", "http://old:1")

    assert resolve_proxy() == "http://new:1"


def test_resolve_proxy_falls_back_to_dtg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DJM_PROXY", raising=False)
    monkeypatch.setenv("DTG_PROXY", "http://old:1")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert resolve_proxy() == "http://old:1"

    assert any(issubclass(w.category, DeprecationWarning) for w in caught)


def test_bika_env_prefers_djm_prefix(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DJM_BIKA_ACCOUNT", "new@example.com")
    monkeypatch.setenv("DJM_BIKA_PASSWORD", "new-pass")
    monkeypatch.setenv("DTG_BIKA_ACCOUNT", "old@example.com")
    monkeypatch.setenv("DTG_BIKA_PASSWORD", "old-pass")

    creds = require_bika_credentials(credentials_path=tmp_path / "credentials.toml")

    assert creds.account == "new@example.com"
    assert creds.password == "new-pass"


def test_migrate_copies_missing_files_from_legacy(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy"
    new = tmp_path / "new"
    legacy.mkdir()
    (legacy / "config.toml").write_text('proxy = "http://127.0.0.1:7890"\n', encoding="utf-8")
    (legacy / "credentials.toml").write_text(
        'bika_account = "a@b.c"\nbika_password = "secret"\n',
        encoding="utf-8",
    )

    migrated = migrate_user_config(new_dir=new, legacy_dir=legacy)

    assert set(migrated) == {"config.toml", "credentials.toml"}
    assert load_config(new / "config.toml").proxy == "http://127.0.0.1:7890"
    stored = load_bika_credentials(new / "credentials.toml")
    assert stored is not None
    assert stored.account == "a@b.c"
    assert stored.password == "secret"
    # legacy untouched
    assert (legacy / "config.toml").is_file()


def test_migrate_does_not_overwrite_existing_new_files(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy"
    new = tmp_path / "new"
    legacy.mkdir()
    new.mkdir()
    (legacy / "config.toml").write_text('proxy = "http://old"\n', encoding="utf-8")
    (new / "config.toml").write_text('proxy = "http://new"\n', encoding="utf-8")

    migrated = migrate_user_config(new_dir=new, legacy_dir=legacy)

    assert migrated == []
    assert load_config(new / "config.toml").proxy == "http://new"


def test_save_config_comment_uses_new_product_name(tmp_path: Path) -> None:
    path = save_config(UserConfig(proxy=None), tmp_path / "config.toml")
    text = path.read_text(encoding="utf-8")
    assert "doujinshi-meta" in text
    assert "doujinshi-tag-getter" not in text


def test_load_config_migrates_legacy_dir_on_first_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    legacy = tmp_path / "legacy"
    new = tmp_path / "new"
    legacy.mkdir()
    (legacy / "config.toml").write_text('proxy = "http://127.0.0.1:7890"\n', encoding="utf-8")
    monkeypatch.setattr("doujinshi_meta.config.legacy_config_dir", lambda: legacy)
    monkeypatch.setattr("doujinshi_meta.config.config_dir", lambda: new)

    cfg = load_config()

    assert cfg.proxy == "http://127.0.0.1:7890"
    assert (new / "config.toml").is_file()
    assert (legacy / "config.toml").is_file()


def test_save_config_writes_to_new_dir_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    legacy = tmp_path / "legacy"
    new = tmp_path / "new"
    legacy.mkdir()
    monkeypatch.setattr("doujinshi_meta.config.legacy_config_dir", lambda: legacy)
    monkeypatch.setattr("doujinshi_meta.config.config_dir", lambda: new)

    path = save_config(UserConfig(proxy="http://new:1"))

    assert path.parent == new
    assert path.read_text(encoding="utf-8").startswith("# doujinshi-meta")


def test_save_credentials_comment_uses_new_product_name(tmp_path: Path) -> None:
    path = save_bika_credentials("a@b.c", "x", path=tmp_path / "credentials.toml")
    text = path.read_text(encoding="utf-8")
    assert "doujinshi-meta" in text
    assert "doujinshi-tag-getter" not in text
