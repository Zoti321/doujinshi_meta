from __future__ import annotations

import getpass
import os
import shutil
import sys
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

APP_NAME = "doujinshi-meta"
LEGACY_APP_NAME = "doujinshi-tag-getter"
_MIGRATE_FILENAMES = ("config.toml", "credentials.toml")


def _platform_user_config_dir(app_name: str) -> Path:
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home())) / app_name
    return Path.home() / ".config" / app_name


def config_dir() -> Path:
    return _platform_user_config_dir(APP_NAME)


def legacy_config_dir() -> Path:
    return _platform_user_config_dir(LEGACY_APP_NAME)


def migrate_user_config(
    *,
    new_dir: Path | None = None,
    legacy_dir: Path | None = None,
) -> list[str]:
    """Copy legacy user config files into the new app dir when missing.

    Does not overwrite files that already exist in ``new_dir``. Returns the
    basenames that were copied. Legacy files are left in place.
    """
    dest = new_dir if new_dir is not None else config_dir()
    src = legacy_dir if legacy_dir is not None else legacy_config_dir()
    if not src.is_dir():
        return []
    migrated: list[str] = []
    for name in _MIGRATE_FILENAMES:
        src_file = src / name
        dest_file = dest / name
        if not src_file.is_file() or dest_file.exists():
            continue
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest_file)
        migrated.append(name)
    return migrated


def _ensure_defaults_migrated() -> None:
    migrated = migrate_user_config()
    if migrated:
        print(
            f"已从 {LEGACY_APP_NAME} 迁移配置到 {APP_NAME}："
            f"{', '.join(migrated)}。旧目录可手动删除。",
            file=sys.stderr,
        )


DEFAULT_CONFIG_PATH = config_dir() / "config.toml"
DEFAULT_CREDENTIALS_PATH = config_dir() / "credentials.toml"


def default_config_path() -> Path:
    """User config.toml path; migrates legacy app dir on first use."""
    _ensure_defaults_migrated()
    return config_dir() / "config.toml"


def default_credentials_path() -> Path:
    """User credentials.toml path; migrates legacy app dir on first use."""
    _ensure_defaults_migrated()
    return config_dir() / "credentials.toml"


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
        _ensure_defaults_migrated()
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
    if path is None:
        _ensure_defaults_migrated()
        config_path = config_dir() / "config.toml"
    else:
        config_path = path
    if not config_path.is_file():
        return UserConfig()
    return _parse_toml_proxy(config_path.read_text(encoding="utf-8"))


def save_config(cfg: UserConfig, path: Path | None = None) -> Path:
    if path is None:
        _ensure_defaults_migrated()
        config_path = config_dir() / "config.toml"
    else:
        config_path = path
    config_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# doujinshi-meta user config", "# proxy: omit for direct connection (default)"]
    if cfg.proxy:
        lines.append(f"proxy = {_toml_quoted(cfg.proxy)}")
    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return config_path


def load_bika_credentials(path: Path | None = None) -> BikaStoredCredentials | None:
    if path is None:
        _ensure_defaults_migrated()
        cred_path = config_dir() / "credentials.toml"
    else:
        cred_path = path
    if not cred_path.is_file():
        return None
    return _parse_bika_credentials(cred_path.read_text(encoding="utf-8"))


def save_bika_credentials(
    account: str,
    password: str,
    path: Path | None = None,
) -> Path:
    if path is None:
        _ensure_defaults_migrated()
        cred_path = config_dir() / "credentials.toml"
    else:
        cred_path = path
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
    if path is None:
        _ensure_defaults_migrated()
        cred_path = config_dir() / "credentials.toml"
    else:
        cred_path = path
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
    dtg = os.environ.get("DTG_PROXY")
    if dtg:
        warnings.warn(
            "DTG_PROXY is deprecated; use DJM_PROXY instead (removed in 0.3.0)",
            DeprecationWarning,
            stacklevel=2,
        )
        return dtg
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
    djm = (os.environ.get("DJM_BIKA_ACCOUNT") or "").strip()
    if djm:
        return djm
    legacy = (
        os.environ.get("DTG_BIKA_ACCOUNT") or os.environ.get("DTG_BIKA_EMAIL") or ""
    ).strip()
    if legacy:
        warnings.warn(
            "DTG_BIKA_ACCOUNT / DTG_BIKA_EMAIL are deprecated; "
            "use DJM_BIKA_ACCOUNT instead (removed in 0.3.0)",
            DeprecationWarning,
            stacklevel=2,
        )
    return legacy


def _env_bika_password() -> str:
    djm = os.environ.get("DJM_BIKA_PASSWORD") or ""
    if djm:
        return djm
    legacy = os.environ.get("DTG_BIKA_PASSWORD") or ""
    if legacy:
        warnings.warn(
            "DTG_BIKA_PASSWORD is deprecated; use DJM_BIKA_PASSWORD instead "
            "(removed in 0.3.0)",
            DeprecationWarning,
            stacklevel=2,
        )
    return legacy


def require_bika_credentials(
    *,
    prompt: Callable[[str], str] | None = None,
    get_password: Callable[[str], str] | None = None,
    credentials_path: Path | None = None,
    ignore_stored: bool = False,
) -> ResolvedBikaCredentials:
    """Resolve Bika credentials: env → credentials file → interactive.

    Field-wise merge is allowed. ``DJM_BIKA_ACCOUNT`` is preferred;
    ``DTG_BIKA_*`` / ``DTG_BIKA_EMAIL`` remain compatibility aliases until 0.3.0.
    """
    ask = prompt or (lambda message: input(message))
    ask_password = get_password or _default_get_password
    if credentials_path is not None:
        cred_path = credentials_path
    else:
        _ensure_defaults_migrated()
        cred_path = config_dir() / "credentials.toml"

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
