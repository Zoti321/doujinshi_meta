from __future__ import annotations

import getpass
import os
import sys
from collections.abc import Callable
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


def password_input_broken() -> bool:
    """True when getpass cannot read keystrokes (Git Bash / mintty on Windows).

    On Win32, ``getpass`` uses ``msvcrt.getwch()``, which only sees the Windows
    console — not mintty/MSYS PTYs. Typing appears to do nothing after the
    password prompt.
    """
    if os.environ.get("MSYSTEM"):
        return True
    if os.environ.get("TERM_PROGRAM", "").lower() == "mintty":
        return True
    return False


def _default_get_password(message: str) -> str:
    if password_input_broken():
        print(
            "（当前终端无法隐藏密码输入，输入将可见）",
            file=sys.stderr,
        )
        return input(message)
    return getpass.getpass(message)


def require_bika_credentials(
    *,
    prompt: Callable[[str], str] | None = None,
    get_password: Callable[[str], str] | None = None,
) -> tuple[str, str]:
    """Resolve Bika user credentials: env first, then interactive prompt.

    Env vars ``DTG_BIKA_EMAIL`` / ``DTG_BIKA_PASSWORD`` win when both are
    non-empty. Otherwise prompt for missing fields (password is masked when
    the terminal supports it).
    """
    ask = prompt or (lambda message: input(message))
    ask_password = get_password or _default_get_password

    email = (os.environ.get("DTG_BIKA_EMAIL") or "").strip()
    password = os.environ.get("DTG_BIKA_PASSWORD") or ""

    if email and password:
        return email, password

    print(
        "未设置完整的 DTG_BIKA_EMAIL / DTG_BIKA_PASSWORD，请手动输入哔咔账号。",
        file=sys.stderr,
    )
    try:
        if not email:
            email = ask("哔咔邮箱/账号: ").strip()
        if not password:
            password = ask_password("哔咔密码: ")
    except EOFError as exc:
        raise RuntimeError(
            "哔咔需要 DTG_BIKA_EMAIL 与 DTG_BIKA_PASSWORD，"
            "或在交互终端中手动输入"
        ) from exc

    if not email or not password:
        raise RuntimeError("哔咔邮箱与密码不能为空")
    return email, password
