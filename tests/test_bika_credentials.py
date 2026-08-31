from __future__ import annotations

from pathlib import Path

import pytest

from doujinshi_meta.config import (
    load_bika_credentials,
    require_bika_credentials,
    save_bika_credentials,
)


def test_uses_env_account_when_both_set(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DTG_BIKA_ACCOUNT", "user@example.com")
    monkeypatch.setenv("DTG_BIKA_PASSWORD", "secret")
    prompts: list[str] = []

    creds = require_bika_credentials(
        prompt=lambda msg: prompts.append(msg) or "ignored",
        get_password=lambda msg: "ignored",
        credentials_path=tmp_path / "credentials.toml",
    )

    assert creds.account == "user@example.com"
    assert creds.password == "secret"
    assert creds.from_interactive is False
    assert creds.from_file is False
    assert prompts == []


def test_accepts_legacy_email_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DTG_BIKA_ACCOUNT", raising=False)
    monkeypatch.setenv("DTG_BIKA_EMAIL", "legacy@example.com")
    monkeypatch.setenv("DTG_BIKA_PASSWORD", "secret")

    creds = require_bika_credentials(credentials_path=tmp_path / "credentials.toml")

    assert creds.account == "legacy@example.com"
    assert creds.password == "secret"


def test_prefers_account_env_over_email(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DTG_BIKA_ACCOUNT", "new@example.com")
    monkeypatch.setenv("DTG_BIKA_EMAIL", "old@example.com")
    monkeypatch.setenv("DTG_BIKA_PASSWORD", "secret")

    creds = require_bika_credentials(credentials_path=tmp_path / "credentials.toml")

    assert creds.account == "new@example.com"


def test_prompts_when_env_and_file_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("DJM_BIKA_ACCOUNT", raising=False)
    monkeypatch.delenv("DJM_BIKA_PASSWORD", raising=False)
    monkeypatch.delenv("DTG_BIKA_ACCOUNT", raising=False)
    monkeypatch.delenv("DTG_BIKA_EMAIL", raising=False)
    monkeypatch.delenv("DTG_BIKA_PASSWORD", raising=False)
    prompts: list[str] = []
    password_prompts: list[str] = []

    creds = require_bika_credentials(
        prompt=lambda msg: prompts.append(msg) or "typed@example.com",
        get_password=lambda msg: password_prompts.append(msg) or "typed-pass",
        credentials_path=tmp_path / "credentials.toml",
    )

    assert creds.account == "typed@example.com"
    assert creds.password == "typed-pass"
    assert creds.from_interactive is True
    assert any("账号" in p for p in prompts)
    assert password_prompts


def test_loads_from_credentials_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DJM_BIKA_ACCOUNT", raising=False)
    monkeypatch.delenv("DJM_BIKA_PASSWORD", raising=False)
    monkeypatch.delenv("DTG_BIKA_ACCOUNT", raising=False)
    monkeypatch.delenv("DTG_BIKA_EMAIL", raising=False)
    monkeypatch.delenv("DTG_BIKA_PASSWORD", raising=False)
    path = tmp_path / "credentials.toml"
    save_bika_credentials("file@example.com", "file-pass", path=path)

    creds = require_bika_credentials(
        prompt=lambda _msg: "should-not-run",
        get_password=lambda _msg: "should-not-run",
        credentials_path=path,
    )

    assert creds.account == "file@example.com"
    assert creds.password == "file-pass"
    assert creds.from_file is True
    assert creds.from_interactive is False


def test_merges_env_account_with_file_password(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DTG_BIKA_ACCOUNT", "env@example.com")
    monkeypatch.delenv("DTG_BIKA_EMAIL", raising=False)
    monkeypatch.delenv("DTG_BIKA_PASSWORD", raising=False)
    path = tmp_path / "credentials.toml"
    save_bika_credentials("file@example.com", "file-pass", path=path)

    creds = require_bika_credentials(credentials_path=path)

    assert creds.account == "env@example.com"
    assert creds.password == "file-pass"
    assert creds.from_file is True


def test_ignore_stored_skips_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DJM_BIKA_ACCOUNT", raising=False)
    monkeypatch.delenv("DJM_BIKA_PASSWORD", raising=False)
    monkeypatch.delenv("DTG_BIKA_ACCOUNT", raising=False)
    monkeypatch.delenv("DTG_BIKA_EMAIL", raising=False)
    monkeypatch.delenv("DTG_BIKA_PASSWORD", raising=False)
    path = tmp_path / "credentials.toml"
    save_bika_credentials("file@example.com", "file-pass", path=path)

    creds = require_bika_credentials(
        prompt=lambda _msg: "retyped@example.com",
        get_password=lambda _msg: "retyped-pass",
        credentials_path=path,
        ignore_stored=True,
    )

    assert creds.account == "retyped@example.com"
    assert creds.password == "retyped-pass"
    assert creds.from_file is False
    assert creds.from_interactive is True


def test_prompts_when_env_empty(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DJM_BIKA_ACCOUNT", "")
    monkeypatch.setenv("DJM_BIKA_PASSWORD", "")
    monkeypatch.setenv("DTG_BIKA_ACCOUNT", "")
    monkeypatch.setenv("DTG_BIKA_EMAIL", "")
    monkeypatch.setenv("DTG_BIKA_PASSWORD", "")

    creds = require_bika_credentials(
        prompt=lambda _msg: "  a@b.com  ",
        get_password=lambda _msg: "pw",
        credentials_path=tmp_path / "credentials.toml",
    )

    assert creds.account == "a@b.com"
    assert creds.password == "pw"


def test_rejects_empty_interactive_input(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("DJM_BIKA_ACCOUNT", raising=False)
    monkeypatch.delenv("DJM_BIKA_PASSWORD", raising=False)
    monkeypatch.delenv("DTG_BIKA_ACCOUNT", raising=False)
    monkeypatch.delenv("DTG_BIKA_EMAIL", raising=False)
    monkeypatch.delenv("DTG_BIKA_PASSWORD", raising=False)

    with pytest.raises(RuntimeError, match="不能为空"):
        require_bika_credentials(
            prompt=lambda _msg: "   ",
            get_password=lambda _msg: "pw",
            credentials_path=tmp_path / "credentials.toml",
        )


def test_prompts_only_missing_password(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DTG_BIKA_ACCOUNT", "only@example.com")
    monkeypatch.delenv("DTG_BIKA_EMAIL", raising=False)
    monkeypatch.delenv("DTG_BIKA_PASSWORD", raising=False)
    prompts: list[str] = []

    creds = require_bika_credentials(
        prompt=lambda msg: prompts.append(msg) or "should-not-run",
        get_password=lambda _msg: "only-pass",
        credentials_path=tmp_path / "credentials.toml",
    )

    assert creds.account == "only@example.com"
    assert creds.password == "only-pass"
    assert creds.from_interactive is True
    assert prompts == []


def test_eof_during_prompt_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DJM_BIKA_ACCOUNT", raising=False)
    monkeypatch.delenv("DJM_BIKA_PASSWORD", raising=False)
    monkeypatch.delenv("DTG_BIKA_ACCOUNT", raising=False)
    monkeypatch.delenv("DTG_BIKA_EMAIL", raising=False)
    monkeypatch.delenv("DTG_BIKA_PASSWORD", raising=False)

    def boom(_msg: str) -> str:
        raise EOFError

    with pytest.raises(RuntimeError, match="环境变量|手动输入|credentials"):
        require_bika_credentials(
            prompt=boom,
            get_password=lambda _m: "x",
            credentials_path=tmp_path / "credentials.toml",
        )


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "credentials.toml"
    save_bika_credentials('user"quote', "p\\ass", path=path)
    loaded = load_bika_credentials(path)
    assert loaded is not None
    assert loaded.account == 'user"quote'
    assert loaded.password == "p\\ass"
