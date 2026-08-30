from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

if sys.platform == "win32":
    _CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / "doujinshi-tag-getter"
else:
    _CONFIG_DIR = Path.home() / ".config" / "doujinshi-tag-getter"

DEFAULT_CONFIG_PATH = _CONFIG_DIR / "config.toml"


@dataclass
class UserConfig:
    proxy: str | None = None


def _parse_toml_proxy(text: str) -> UserConfig:
    cfg = UserConfig()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("proxy"):
            _, _, value = line.partition("=")
            value = value.strip().strip('"').strip("'")
            cfg.proxy = value or None
    return cfg


def load_config(path: Path | None = None) -> UserConfig:
    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        return UserConfig()
    return _parse_toml_proxy(config_path.read_text(encoding="utf-8"))


def save_config(cfg: UserConfig, path: Path | None = None) -> Path:
    config_path = path or DEFAULT_CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# doujinshi-tag-getter user config", "# proxy: omit for direct connection (default)"]
    if cfg.proxy:
        lines.append(f'proxy = "{cfg.proxy}"')
    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return config_path


def resolve_proxy(
    *,
    cli_proxy: str | None = None,
    cli_no_proxy: bool = False,
    config: UserConfig | None = None,
) -> str | None:
    if cli_no_proxy:
        return None
    if cli_proxy is not None:
        return cli_proxy or None
    if config and config.proxy:
        return config.proxy
    return os.environ.get("DTG_PROXY") or None


def require_bika_credentials() -> tuple[str, str]:
    try:
        email = os.environ["DTG_BIKA_EMAIL"]
        password = os.environ["DTG_BIKA_PASSWORD"]
    except KeyError as exc:
        raise RuntimeError(
            "哔咔需要环境变量 DTG_BIKA_EMAIL 与 DTG_BIKA_PASSWORD"
        ) from exc
    if not email or not password:
        raise RuntimeError("DTG_BIKA_EMAIL 与 DTG_BIKA_PASSWORD 不能为空")
    return email, password


def proxy_to_httpx(proxy: str | None) -> dict[str, str] | None:
    if not proxy:
        return None
    return {"http://": proxy, "https://": proxy}
