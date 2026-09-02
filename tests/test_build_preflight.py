from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


def _load_build():
    path = Path(__file__).resolve().parents[1] / "scripts" / "build.py"
    scripts_dir = path.parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    spec = importlib.util.spec_from_file_location("build", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_preflight_rejects_non_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_build()
    monkeypatch.setattr(mod, "msvc_available", lambda: True)
    monkeypatch.setattr(mod.sys, "platform", "linux")

    message = mod.preflight_error()

    assert message is not None
    assert "Windows" in message


def test_preflight_rejects_missing_msvc(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_build()
    monkeypatch.setattr(mod.sys, "platform", "win32")
    monkeypatch.setattr(mod, "msvc_available", lambda: False)

    message = mod.preflight_error()

    assert message is not None
    assert "MSVC" in message or "cl.exe" in message


def test_preflight_ok_on_windows_with_msvc(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_build()
    monkeypatch.setattr(mod.sys, "platform", "win32")
    monkeypatch.setattr(mod, "msvc_available", lambda: True)

    assert mod.preflight_error() is None
