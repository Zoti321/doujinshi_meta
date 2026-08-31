from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from doujinshi_meta.config import load_bika_credentials, save_bika_credentials
from doujinshi_meta.sources import bika as bika_mod
from doujinshi_meta.sources.bika_ops import open_bika_client


def _login_payload(token: str | None) -> dict:
    if token is None:
        return {"code": 200, "data": {}}
    return {"code": 200, "data": {"token": token}}


def _install_login_sequence(
    monkeypatch: pytest.MonkeyPatch, payloads: list[dict]
) -> list[tuple[str, str]]:
    """Replace BikaClient login transport; record (email, password) per login."""
    attempts: list[tuple[str, str]] = []
    queue = list(payloads)

    original_init = bika_mod.BikaClient.__init__

    def init_with_queue(
        self: bika_mod.BikaClient,
        email: str,
        password: str,
        proxy: str | None = None,
    ) -> None:
        original_init(self, email, password, proxy=proxy)

        def post(*_args, **_kwargs):
            attempts.append((self._email, self._password))
            payload = queue.pop(0)
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = payload
            response.raise_for_status = MagicMock()
            return response

        self._client.post = MagicMock(side_effect=post)

    monkeypatch.setattr(bika_mod.BikaClient, "__init__", init_with_queue)
    return attempts


def test_open_saves_when_prompted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("DJM_BIKA_ACCOUNT", raising=False)
    monkeypatch.delenv("DJM_BIKA_PASSWORD", raising=False)
    path = tmp_path / "credentials.toml"
    _install_login_sequence(monkeypatch, [_login_payload("tok")])

    monkeypatch.setattr(
        "doujinshi_meta.sources.bika_ops.require_bika_credentials",
        lambda **_kwargs: __import__(
            "doujinshi_meta.config", fromlist=["ResolvedBikaCredentials"]
        ).ResolvedBikaCredentials(
            account="typed@example.com",
            password="typed-pass",
            from_interactive=True,
            from_file=False,
        ),
    )

    client = open_bika_client(credentials_path=path)
    client.close()

    loaded = load_bika_credentials(path)
    assert loaded is not None
    assert loaded.account == "typed@example.com"
    assert loaded.password == "typed-pass"


def test_open_does_not_save_when_from_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "credentials.toml"
    monkeypatch.setenv("DJM_BIKA_ACCOUNT", "env@example.com")
    monkeypatch.setenv("DJM_BIKA_PASSWORD", "env-pass")
    _install_login_sequence(monkeypatch, [_login_payload("tok")])

    client = open_bika_client(credentials_path=path)
    client.close()

    assert load_bika_credentials(path) is None


def test_open_does_not_save_when_from_file_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("DJM_BIKA_ACCOUNT", raising=False)
    monkeypatch.delenv("DJM_BIKA_PASSWORD", raising=False)
    path = tmp_path / "credentials.toml"
    save_bika_credentials("file@example.com", "file-pass", path=path)
    _install_login_sequence(monkeypatch, [_login_payload("tok")])

    client = open_bika_client(credentials_path=path)
    client.close()

    loaded = load_bika_credentials(path)
    assert loaded is not None
    assert loaded.account == "file@example.com"


def test_open_reprompts_on_file_auth_failure_then_saves(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("DJM_BIKA_ACCOUNT", raising=False)
    monkeypatch.delenv("DJM_BIKA_PASSWORD", raising=False)
    path = tmp_path / "credentials.toml"
    save_bika_credentials("bad@example.com", "bad-pass", path=path)
    attempts = _install_login_sequence(
        monkeypatch,
        [_login_payload(None), _login_payload("tok")],
    )

    from doujinshi_meta.config import ResolvedBikaCredentials

    calls = {"n": 0}

    def fake_require(**kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return ResolvedBikaCredentials(
                account="bad@example.com",
                password="bad-pass",
                from_interactive=False,
                from_file=True,
            )
        assert kwargs.get("ignore_stored") is True
        return ResolvedBikaCredentials(
            account="good@example.com",
            password="good-pass",
            from_interactive=True,
            from_file=False,
        )

    monkeypatch.setattr(
        "doujinshi_meta.sources.bika_ops.require_bika_credentials",
        fake_require,
    )

    client = open_bika_client(credentials_path=path)
    client.close()

    assert attempts == [
        ("bad@example.com", "bad-pass"),
        ("good@example.com", "good-pass"),
    ]
    loaded = load_bika_credentials(path)
    assert loaded is not None
    assert loaded.account == "good@example.com"
    assert loaded.password == "good-pass"


def test_open_does_not_reprompt_on_network_error_with_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("DJM_BIKA_ACCOUNT", raising=False)
    monkeypatch.delenv("DJM_BIKA_PASSWORD", raising=False)
    path = tmp_path / "credentials.toml"
    save_bika_credentials("file@example.com", "file-pass", path=path)

    original_init = bika_mod.BikaClient.__init__

    def init_with_failing_transport(
        self: bika_mod.BikaClient,
        email: str,
        password: str,
        proxy: str | None = None,
    ) -> None:
        original_init(self, email, password, proxy=proxy)
        self._client.post = MagicMock(
            side_effect=httpx.ConnectError("connection refused")
        )

    monkeypatch.setattr(bika_mod.BikaClient, "__init__", init_with_failing_transport)

    with pytest.raises(RuntimeError, match="网络连接失败"):
        open_bika_client(credentials_path=path)

    loaded = load_bika_credentials(path)
    assert loaded is not None
    assert loaded.account == "file@example.com"
