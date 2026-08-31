from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

from doujinshi_meta.fetch import fetch_tags
from doujinshi_meta.sources import bika as bika_mod


def _install_connect_error(monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_fetch_tags_direct_connect_error_hints_proxy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DJM_BIKA_ACCOUNT", "user@example.com")
    monkeypatch.setenv("DJM_BIKA_PASSWORD", "secret")
    _install_connect_error(monkeypatch)

    with pytest.raises(RuntimeError, match=r"djm config set proxy|`--proxy`") as exc_info:
        fetch_tags("bika", ["comic-1"], proxy=None, delay=0)

    message = str(exc_info.value)
    assert "连接" in message or "网络" in message


def test_fetch_tags_proxied_connect_error_does_not_hint_set_proxy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DJM_BIKA_ACCOUNT", "user@example.com")
    monkeypatch.setenv("DJM_BIKA_PASSWORD", "secret")
    _install_connect_error(monkeypatch)

    with pytest.raises(RuntimeError) as exc_info:
        fetch_tags("bika", ["comic-1"], proxy="http://127.0.0.1:7890", delay=0)

    message = str(exc_info.value)
    assert "连接" in message or "网络" in message
    assert "djm config set proxy" not in message
    assert "--proxy" not in message


def _install_login_payload(monkeypatch: pytest.MonkeyPatch, payload: dict) -> None:
    original_init = bika_mod.BikaClient.__init__

    def init_with_payload(
        self: bika_mod.BikaClient,
        email: str,
        password: str,
        proxy: str | None = None,
    ) -> None:
        original_init(self, email, password, proxy=proxy)
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = payload
        response.raise_for_status = MagicMock()
        self._client.post = MagicMock(return_value=response)

    monkeypatch.setattr(bika_mod.BikaClient, "__init__", init_with_payload)


def test_fetch_tags_login_missing_token_does_not_hint_proxy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DJM_BIKA_ACCOUNT", "user@example.com")
    monkeypatch.setenv("DJM_BIKA_PASSWORD", "secret")
    _install_login_payload(monkeypatch, {"code": 200, "data": {}})

    with pytest.raises(RuntimeError, match="登录|账号|密码") as exc_info:
        fetch_tags("bika", ["comic-1"], proxy=None, delay=0)

    message = str(exc_info.value)
    assert "djm config set proxy" not in message
    assert "--proxy" not in message


def test_fetch_tags_login_missing_data_does_not_hint_proxy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DJM_BIKA_ACCOUNT", "user@example.com")
    monkeypatch.setenv("DJM_BIKA_PASSWORD", "secret")
    _install_login_payload(monkeypatch, {"code": 200, "message": "success"})

    with pytest.raises(RuntimeError, match="登录|账号|密码") as exc_info:
        fetch_tags("bika", ["comic-1"], proxy=None, delay=0)

    message = str(exc_info.value)
    assert "djm config set proxy" not in message
    assert "--proxy" not in message


def test_proxy_to_httpx_removed_from_config() -> None:
    import doujinshi_meta.config as config

    assert not hasattr(config, "proxy_to_httpx")


def test_bika_default_headers_baseline_channel_and_build() -> None:
    assert bika_mod.DEFAULT_HEADERS["app-channel"] == "1"
    assert bika_mod.DEFAULT_HEADERS["app-build-version"] == "44"
