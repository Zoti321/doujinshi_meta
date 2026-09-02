from __future__ import annotations

import importlib.util
import sys
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_build():
    path = PROJECT_ROOT / "scripts" / "build.py"
    scripts_dir = path.parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    spec = importlib.util.spec_from_file_location("build", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_nuitka_command_default_is_onefile() -> None:
    mod = _load_build()
    cmd = mod.nuitka_command(Path("out"), onedir=False)
    assert "--onefile" in cmd
    assert "--standalone" not in cmd


def test_nuitka_command_onedir_is_standalone_not_onefile() -> None:
    mod = _load_build()
    cmd = mod.nuitka_command(Path("out"), onedir=True)
    assert "--standalone" in cmd
    assert "--onefile" not in cmd


def test_clean_artifacts_removes_version_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_build()
    version = "0.3.0"
    dist_root = tmp_path / "dist"
    out_dir = dist_root / f"djm-{version}-windows-x64"
    out_dir.mkdir(parents=True)
    (out_dir / "djm.exe").write_bytes(b"exe")
    (out_dir / "manifest.json").write_text("{}", encoding="utf-8")
    (dist_root / f"djm-{version}-windows-x64.zip").write_bytes(b"zip")
    (dist_root / f"doujinshi_meta-{version}-py3-none-any.whl").write_bytes(b"whl")
    (dist_root / f"doujinshi_meta-{version}.tar.gz").write_bytes(b"sdist")
    (dist_root / "other-version.whl").write_bytes(b"keep")

    monkeypatch.setattr(mod, "project_root", lambda: tmp_path)
    mod.clean_artifacts(version)

    assert not out_dir.exists()
    assert not (dist_root / f"djm-{version}-windows-x64.zip").exists()
    assert not (dist_root / f"doujinshi_meta-{version}-py3-none-any.whl").exists()
    assert not (dist_root / f"doujinshi_meta-{version}.tar.gz").exists()
    assert (dist_root / "other-version.whl").is_file()


def test_create_release_zip_contains_exe_and_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_build()
    version = "0.3.0"
    dist_root = tmp_path / "dist"
    out_dir = dist_root / f"djm-{version}-windows-x64"
    out_dir.mkdir(parents=True)
    (out_dir / "djm.exe").write_bytes(b"fake-exe")
    (out_dir / "manifest.json").write_text('{"artifact":"djm.exe"}', encoding="utf-8")
    (out_dir / "extra.dll").write_bytes(b"skip")

    monkeypatch.setattr(mod, "project_root", lambda: tmp_path)
    zip_path = mod.create_release_zip(out_dir, version)

    assert zip_path == dist_root / f"djm-{version}-windows-x64.zip"
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
    assert names == {"djm.exe", "manifest.json"}


def test_build_wheel_invokes_uv_build(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_build()
    dist_root = tmp_path / "dist"
    dist_root.mkdir()
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return MagicMock(returncode=0)

    monkeypatch.setattr(mod, "project_root", lambda: tmp_path)
    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    mod.build_wheel()

    assert len(calls) == 1
    assert calls[0][0:2] == ["uv", "build"]
    assert calls[0][2].startswith("--out-dir=")
    assert str(dist_root) in calls[0][2]


def test_create_release_zip_requires_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_build()
    version = "0.3.0"
    dist_root = tmp_path / "dist"
    out_dir = dist_root / f"djm-{version}-windows-x64"
    out_dir.mkdir(parents=True)
    (out_dir / "djm.exe").write_bytes(b"fake-exe")

    monkeypatch.setattr(mod, "project_root", lambda: tmp_path)
    with pytest.raises(RuntimeError, match="manifest"):
        mod.create_release_zip(out_dir, version)


def test_smoke_full_runs_jmcomic_fetch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_build()
    exe = tmp_path / "djm.exe"
    exe.write_bytes(b"x")
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return MagicMock(returncode=0)

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    mod.smoke_full_binary(exe)

    assert calls == [
        [str(exe), "fetch", "--source", "jmcomic", "--ids", "410090"],
    ]


def test_smoke_full_raises_on_nonzero_exit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_build()
    exe = tmp_path / "djm.exe"
    exe.write_bytes(b"x")

    def fake_run(cmd, **kwargs):
        return MagicMock(returncode=1, stderr="network error")

    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="smoke-full"):
        mod.smoke_full_binary(exe)
