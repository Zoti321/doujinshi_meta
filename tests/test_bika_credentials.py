from __future__ import annotations

import pytest

from doujinshi_tag_getter.config import require_bika_credentials


def test_uses_env_when_both_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DTG_BIKA_EMAIL", "user@example.com")
    monkeypatch.setenv("DTG_BIKA_PASSWORD", "secret")
    prompts: list[str] = []

    email, password = require_bika_credentials(
        prompt=lambda msg: prompts.append(msg) or "ignored",
        get_password=lambda msg: "ignored",
    )

    assert email == "user@example.com"
    assert password == "secret"
    assert prompts == []


def test_prompts_when_env_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DTG_BIKA_EMAIL", raising=False)
    monkeypatch.delenv("DTG_BIKA_PASSWORD", raising=False)
    prompts: list[str] = []
    password_prompts: list[str] = []

    email, password = require_bika_credentials(
        prompt=lambda msg: prompts.append(msg) or "typed@example.com",
        get_password=lambda msg: password_prompts.append(msg) or "typed-pass",
    )

    assert email == "typed@example.com"
    assert password == "typed-pass"
    assert any("邮箱" in p or "email" in p.lower() or "账号" in p for p in prompts)
    assert password_prompts


def test_prompts_when_env_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DTG_BIKA_EMAIL", "")
    monkeypatch.setenv("DTG_BIKA_PASSWORD", "")

    email, password = require_bika_credentials(
        prompt=lambda _msg: "  a@b.com  ",
        get_password=lambda _msg: "pw",
    )

    assert email == "a@b.com"
    assert password == "pw"


def test_rejects_empty_interactive_input(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DTG_BIKA_EMAIL", raising=False)
    monkeypatch.delenv("DTG_BIKA_PASSWORD", raising=False)

    with pytest.raises(RuntimeError, match="不能为空"):
        require_bika_credentials(
            prompt=lambda _msg: "   ",
            get_password=lambda _msg: "pw",
        )


def test_prompts_only_missing_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DTG_BIKA_EMAIL", "only@example.com")
    monkeypatch.delenv("DTG_BIKA_PASSWORD", raising=False)
    prompts: list[str] = []

    email, password = require_bika_credentials(
        prompt=lambda msg: prompts.append(msg) or "should-not-run",
        get_password=lambda _msg: "only-pass",
    )

    assert email == "only@example.com"
    assert password == "only-pass"
    assert prompts == []


def test_eof_during_prompt_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DTG_BIKA_EMAIL", raising=False)
    monkeypatch.delenv("DTG_BIKA_PASSWORD", raising=False)

    def boom(_msg: str) -> str:
        raise EOFError

    with pytest.raises(RuntimeError, match="环境变量|手动输入"):
        require_bika_credentials(prompt=boom, get_password=lambda _m: "x")
