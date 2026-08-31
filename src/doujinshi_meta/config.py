from __future__ import annotations

import getpass
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

APP_NAME = "doujinshi-meta"


def _platform_user_config_dir(app_name: str) -> Path:
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home())) / app_name
    return Path.home() / ".config" / app_name


def config_dir() -> Path:
    return _platform_user_config_dir(APP_NAME)


def default_config_path() -> Path:
    """User config.toml path."""
    return config_dir() / "config.toml"


@dataclass
class UserConfig:
    proxy: str | None = None


@dataclass(frozen=True)
class BikaStoredCredentials:
    account: str
    password: str


@dataclass(frozen=True)
class ResolvedBikaCredentials:
    account: str
    password: str
    from_interactive: bool = False
    from_file: bool = False


def credentials_path_beside(config_path: Path | None = None) -> Path:
    """credentials.toml next to config.toml (or the default user dir)."""
    if config_path is None:
        return config_dir() / "credentials.toml"
    return config_path.parent / "credentials.toml"


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


def _parse_toml_string_value(raw: str) -> str:
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
        value = value.replace('\\"', '"').replace("\\\\", "\\")
    return value


def _toml_quoted(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _parse_bika_credentials(text: str) -> BikaStoredCredentials | None:
    account = ""
    password = ""
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, raw = line.partition("=")
        key = key.strip()
        if key == "bika_account":
            account = _parse_toml_string_value(raw).strip()
        elif key == "bika_password":
            password = _parse_toml_string_value(raw)
    if account and password:
        return BikaStoredCredentials(account=account, password=password)
    return None


def load_config(path: Path | None = None) -> UserConfig:
    config_path = config_dir() / "config.toml" if path is None else path
    if not config_path.is_file():
        return UserConfig()
    return _parse_toml_proxy(config_path.read_text(encoding="utf-8"))


def save_config(cfg: UserConfig, path: Path | None = None) -> Path:
    config_path = config_dir() / "config.toml" if path is None else path
    config_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# doujinshi-meta user config", "# proxy: omit for direct connection (default)"]
    if cfg.proxy:
        lines.append(f"proxy = {_toml_quoted(cfg.proxy)}")
    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return config_path


def load_bika_credentials(path: Path | None = None) -> BikaStoredCredentials | None:
    cred_path = config_dir() / "credentials.toml" if path is None else path
    if not cred_path.is_file():
        return None
    return _parse_bika_credentials(cred_path.read_text(encoding="utf-8"))


def save_bika_credentials(
    account: str,
    password: str,
    path: Path | None = None,
) -> Path:
    cred_path = config_dir() / "credentials.toml" if path is None else path
    cred_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# doujinshi-meta credentials (plaintext; keep private)",
        f"bika_account = {_toml_quoted(account)}",
        f"bika_password = {_toml_quoted(password)}",
    ]
    cred_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        os.chmod(cred_path, 0o600)
    except OSError:
        pass
    return cred_path


def clear_bika_credentials(path: Path | None = None) -> Path:
    cred_path = config_dir() / "credentials.toml" if path is None else path
    if cred_path.is_file():
        cred_path.unlink()
    return cred_path


def mask_account(account: str) -> str:
    if len(account) <= 2:
        return "*" * len(account)
    return f"{account[0]}***{account[-1]}"


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
    djm = os.environ.get("DJM_PROXY")
    if djm:
        return djm
    return None


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


def _env_bika_account() -> str:
    return (os.environ.get("DJM_BIKA_ACCOUNT") or "").strip()


def _env_bika_password() -> str:
    return os.environ.get("DJM_BIKA_PASSWORD") or ""


def require_bika_credentials(
    *,
    prompt: Callable[[str], str] | None = None,
    get_password: Callable[[str], str] | None = None,
    credentials_path: Path | None = None,
    ignore_stored: bool = False,
) -> ResolvedBikaCredentials:
    """Resolve Bika credentials: env → credentials file → interactive.

    Field-wise merge is allowed via ``DJM_BIKA_ACCOUNT`` / ``DJM_BIKA_PASSWORD``.
    """
    ask = prompt or (lambda message: input(message))
    ask_password = get_password or _default_get_password
    cred_path = (
        credentials_path if credentials_path is not None else config_dir() / "credentials.toml"
    )

    account = _env_bika_account()
    password = _env_bika_password()
    from_file = False
    from_interactive = False

    if not ignore_stored:
        stored = load_bika_credentials(cred_path)
        if stored:
            if not account:
                account = stored.account
                from_file = True
            if not password:
                password = stored.password
                from_file = True

    if account and password:
        return ResolvedBikaCredentials(
            account=account,
            password=password,
            from_interactive=False,
            from_file=from_file,
        )

    print(
        "未设置完整的 DJM_BIKA_ACCOUNT / DJM_BIKA_PASSWORD，请手动输入哔咔账号。",
        file=sys.stderr,
    )
    try:
        if not account:
            account = ask("哔咔账号: ").strip()
            from_interactive = True
        if not password:
            password = ask_password("哔咔密码: ")
            from_interactive = True
    except EOFError as exc:
        raise RuntimeError(
            "哔咔需要 DJM_BIKA_ACCOUNT 与 DJM_BIKA_PASSWORD、"
            "已保存的 credentials.toml，或在交互终端中手动输入"
        ) from exc

    if not account or not password:
        raise RuntimeError("哔咔账号与密码不能为空")
    return ResolvedBikaCredentials(
        account=account,
        password=password,
        from_interactive=from_interactive,
        from_file=from_file,
    )


def is_bika_network_error(exc: BaseException) -> bool:
    return "网络连接失败" in str(exc)
