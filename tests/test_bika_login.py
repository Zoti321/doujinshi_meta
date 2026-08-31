from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from doujinshi_meta.sources.bika import BikaClient


def _mock_post(payload: dict, *, status: int = 200) -> MagicMock:
    response = MagicMock()
    response.status_code = status
    response.json.return_value = payload
    response.raise_for_status = MagicMock()
    return response


def test_login_code200_without_data_raises_runtime_error() -> None:
    """Repro: API may return code=200 but omit data (e.g. bad signature)."""
    client = BikaClient("user@example.com", "secret")
    client._client.post = MagicMock(return_value=_mock_post({"code": 200, "message": "success"}))

    with pytest.raises(RuntimeError, match="token|data|登录"):
        client.login()


def test_login_code200_empty_data_raises_runtime_error() -> None:
    client = BikaClient("user@example.com", "secret")
    client._client.post = MagicMock(return_value=_mock_post({"code": 200, "data": {}}))

    with pytest.raises(RuntimeError, match="token|登录"):
        client.login()


def test_login_success_sets_token() -> None:
    client = BikaClient("user@example.com", "secret")
    client._client.post = MagicMock(
        return_value=_mock_post({"code": 200, "data": {"token": "tok-abc"}})
    )

    client.login()

    assert client._token == "tok-abc"
