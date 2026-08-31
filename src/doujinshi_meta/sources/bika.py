from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from typing import Any

import httpx

API_BASE = "https://picaapi.picacomic.com/"
API_KEY = "C69BAF41DA5ABD1FFEDC6D2FEA56B"
# Must match hiczp / pica-cli / pica-go (63 chars, no trailing backtick).
SECRET_KEY = r"~d}$Q7$eIni=V)9\RK/P.RM4;9[7|@/CA}b~OW!3?EV`:<>M7pddUBL5n|0/*Cn"

DEFAULT_HEADERS = {
    "api-key": API_KEY,
    "accept": "application/vnd.picacomic.com.v1+json",
    "app-channel": "1",
    "app-version": "2.2.1.2.3.3",
    "app-build-version": "44",
    "app-platform": "android",
    "app-uuid": "defaultUuid",
    "User-Agent": "okhttp/3.8.1",
    "image-quality": "original",
}


def _parse_api_payload(payload: dict[str, Any], *, context: str) -> dict[str, Any]:
    if payload.get("code") != 200:
        raise RuntimeError(payload.get("message") or f"bika {context} failed")
    data = payload.get("data")
    if not isinstance(data, dict):
        if context == "login":
            raise RuntimeError(
                "哔咔登录失败：响应无 token（请检查账号/密码；"
                "若确认无误则为客户端签名密钥错误）"
            )
        raise RuntimeError(f"bika {context} response missing data")
    return data


PROXY_HINT = "可尝试 `djm config set proxy ...` 或 `--proxy`"


def _network_error_message(exc: BaseException, *, proxy: str | None) -> str:
    base = f"哔咔网络连接失败: {exc}"
    if proxy:
        return base
    return f"{base}；{PROXY_HINT}"


class BikaClient:
    def __init__(self, email: str, password: str, proxy: str | None = None) -> None:
        self._email = email
        self._password = password
        self._proxy = proxy
        self._token: str | None = None
        # httpx>=0.28: use `proxy=` (str URL); `proxies=` dict was removed
        self._client = httpx.Client(
            base_url=API_BASE,
            timeout=15.0,
            proxy=proxy,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> BikaClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _sign(self, method: str, path: str, timestamp: str, nonce: str) -> str:
        raw = f"{path}{timestamp}{nonce}{method.upper()}{API_KEY}".lower()
        return hmac.new(SECRET_KEY.encode(), raw.encode(), hashlib.sha256).hexdigest()

    def _headers(self, method: str, path: str, *, auth: bool = True) -> dict[str, str]:
        timestamp = str(int(time.time()))
        nonce = secrets.token_hex(16)
        headers = dict(DEFAULT_HEADERS)
        headers["time"] = timestamp
        headers["nonce"] = nonce
        headers["signature"] = self._sign(method, path, timestamp, nonce)
        if auth and self._token:
            headers["authorization"] = self._token
        return headers

    def _request(self, method: str, path: str, *, auth: bool = True, **kwargs: Any) -> dict[str, Any]:
        sign_path = path.lstrip("/")
        if "?" in sign_path:
            pass
        headers = self._headers(method, sign_path, auth=auth)
        try:
            response = self._client.request(method, path, headers=headers, **kwargs)
            if response.status_code == 401 and auth:
                self.login()
                headers = self._headers(method, sign_path, auth=True)
                response = self._client.request(method, path, headers=headers, **kwargs)
        except httpx.RequestError as exc:
            raise RuntimeError(
                _network_error_message(exc, proxy=self._proxy)
            ) from exc
        response.raise_for_status()
        payload = response.json()
        return _parse_api_payload(payload, context="api request")

    def login(self) -> None:
        path = "auth/sign-in"
        headers = self._headers("POST", path, auth=False)
        headers["Content-Type"] = "application/json; charset=UTF-8"
        try:
            response = self._client.post(
                path,
                headers=headers,
                json={"email": self._email, "password": self._password},
            )
        except httpx.RequestError as exc:
            raise RuntimeError(
                _network_error_message(exc, proxy=self._proxy)
            ) from exc
        response.raise_for_status()
        payload = response.json()
        data = _parse_api_payload(payload, context="login")
        token = data.get("token")
        if not token:
            raise RuntimeError(
                "哔咔登录失败：响应无 token（请检查账号/密码；"
                "若确认无误则为客户端签名密钥错误）"
            )
        self._token = token

    def get_comic(self, comic_id: str) -> dict[str, Any]:
        if not self._token:
            self.login()
        data = self._request("GET", f"comics/{comic_id}")
        return data["comic"]

    def list_categories(self) -> list[dict[str, Any]]:
        if not self._token:
            self.login()
        data = self._request("GET", "categories")
        categories = data.get("categories")
        if not isinstance(categories, list):
            raise RuntimeError("哔咔 categories 响应缺少 categories 列表")
        return [c for c in categories if isinstance(c, dict)]

    def list_comics_page(self, category: str, page: int, sort: str = "dd") -> dict[str, Any]:
        if not self._token:
            self.login()
        from urllib.parse import quote

        path = f"comics?c={quote(category)}&page={page}&s={sort}"
        data = self._request("GET", path)
        # Envelope is usually {"comics": {docs, pages, ...}}; some clients flatten.
        if isinstance(data.get("comics"), dict):
            return data["comics"]
        return data
