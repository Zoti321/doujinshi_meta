from __future__ import annotations

import json
import subprocess
import tomllib
from pathlib import Path

import pytest

DIST_ROOT = Path(__file__).resolve().parents[1] / "dist"


def _dist_dir() -> Path | None:
    data = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8"))
    version = data["project"]["version"]
    candidate = DIST_ROOT / f"djm-{version}-windows-x64"
    if (candidate / "djm.exe").is_file():
        return candidate
    return None


@pytest.mark.integration
def test_built_exe_smoke() -> None:
    dist = _dist_dir()
    if dist is None:
        pytest.skip("未找到本地构建产物 dist/djm-*-windows-x64/djm.exe")

    exe = dist / "djm.exe"
    manifest_path = dist / "manifest.json"
    version = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]["version"]

    version_result = subprocess.run([str(exe), "--version"], capture_output=True, text=True, check=False)
    assert version_result.returncode == 0
    assert version_result.stdout.strip() == version

    help_result = subprocess.run([str(exe), "--help"], capture_output=True, text=True, check=False)
    assert help_result.returncode == 0

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["version"] == version
    assert manifest["artifact"] == "djm.exe"
    assert len(manifest["sha256"]) == 64
