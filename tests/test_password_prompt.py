from __future__ import annotations

import pytest

from doujinshi_tag_getter import config


def test_password_input_broken_under_msystem(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MSYSTEM", "MINGW64")
    assert config.password_input_broken() is True


def test_password_input_broken_under_mintty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MSYSTEM", raising=False)
    monkeypatch.setenv("TERM_PROGRAM", "mintty")
    assert config.password_input_broken() is True


def test_password_input_ok_without_msystem(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MSYSTEM", raising=False)
    monkeypatch.delenv("TERM_PROGRAM", raising=False)
    assert config.password_input_broken() is False


def test_falls_back_to_visible_input_when_getpass_broken(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DTG_BIKA_EMAIL", raising=False)
    monkeypatch.delenv("DTG_BIKA_PASSWORD", raising=False)
    monkeypatch.setenv("MSYSTEM", "MINGW64")
    getpass_calls: list[str] = []

    def fake_getpass(msg: str) -> str:
        getpass_calls.append(msg)
        raise AssertionError("getpass must not be used under MSYSTEM")

    monkeypatch.setattr(config.getpass, "getpass", fake_getpass)
    monkeypatch.setattr("builtins.input", lambda _msg: "visible-pass")

    email, password = config.require_bika_credentials(
        prompt=lambda _m: "user@example.com",
    )

    assert email == "user@example.com"
    assert password == "visible-pass"
    assert getpass_calls == []
