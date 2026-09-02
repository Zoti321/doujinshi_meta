from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from build_manifest import manifest_payload, write_manifest

PREFLIGHT_EXIT = 2
BUILD_TOOLS_URL = "https://visualstudio.microsoft.com/visual-cpp-build-tools/"


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def read_project_version() -> str:
    data = tomllib.loads((project_root() / "pyproject.toml").read_text(encoding="utf-8"))
    return data["project"]["version"]


def dist_dir(version: str) -> Path:
    return project_root() / "dist" / f"djm-{version}-windows-x64"


def _vswhere_cl_path() -> Path | None:
    program_files_x86 = os.environ.get("ProgramFiles(x86)")
    if not program_files_x86:
        return None
    vswhere = (
        Path(program_files_x86)
        / "Microsoft Visual Studio"
        / "Installer"
        / "vswhere.exe"
    )
    if not vswhere.is_file():
        return None
    try:
        result = subprocess.run(
            [
                str(vswhere),
                "-latest",
                "-products",
                "*",
                "-requires",
                "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                "-property",
                "installationPath",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    install_path = result.stdout.strip()
    if not install_path:
        return None
    tools_root = Path(install_path) / "VC" / "Tools" / "MSVC"
    if not tools_root.is_dir():
        return None
    for version_dir in sorted(tools_root.iterdir(), reverse=True):
        cl = version_dir / "bin" / "Hostx64" / "x64" / "cl.exe"
        if cl.is_file():
            return cl
    return None


def msvc_available() -> bool:
    if shutil.which("cl"):
        return True
    return _vswhere_cl_path() is not None


def preflight_error() -> str | None:
    if sys.platform != "win32":
        return (
            f"Nuitka 构建仅支持 Windows x64（当前平台: {sys.platform}）。"
            "请在 Windows x64 上运行本脚本。"
        )
    if not msvc_available():
        return (
            "未检测到 MSVC 编译器 (cl.exe)。"
            "请安装 Visual Studio Build Tools 并勾选「使用 C++ 的桌面开发」："
            f"{BUILD_TOOLS_URL}"
        )
    return None


def nuitka_command(output_dir: Path) -> list[str]:
    cli_entry = project_root() / "src" / "doujinshi_meta" / "cli.py"
    return [
        sys.executable,
        "-m",
        "nuitka",
        "--onefile",
        f"--output-dir={output_dir}",
        "--output-filename=djm.exe",
        "--assume-yes-for-downloads",
        "--include-package=doujinshi_meta",
        "--include-package=jmcomic",
        "--include-package-data=jmcomic",
        "--include-package=httpx",
        "--include-package=typer",
        "--include-package=rich",
        str(cli_entry),
    ]


def build_binary(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(nuitka_command(output_dir), check=True, cwd=project_root())
    exe = output_dir / "djm.exe"
    if not exe.is_file():
        raise RuntimeError(f"Nuitka 未产出 {exe}")
    return exe


def smoke_binary(exe: Path, version: str) -> None:
    version_result = subprocess.run(
        [str(exe), "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if version_result.returncode != 0:
        raise RuntimeError(
            f"冒烟失败: {exe} --version exit {version_result.returncode}\n"
            f"{version_result.stderr}"
        )
    if version_result.stdout.strip() != version:
        raise RuntimeError(
            f"版本不匹配: 期望 {version!r}, 得到 {version_result.stdout.strip()!r}"
        )

    help_result = subprocess.run(
        [str(exe), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    if help_result.returncode != 0:
        raise RuntimeError(
            f"冒烟失败: {exe} --help exit {help_result.returncode}\n"
            f"{help_result.stderr}"
        )


def main() -> None:
    error = preflight_error()
    if error:
        print(error, file=sys.stderr)
        raise SystemExit(PREFLIGHT_EXIT)

    version = read_project_version()
    out_dir = dist_dir(version)
    exe = build_binary(out_dir)
    write_manifest(out_dir / "manifest.json", manifest_payload(version=version, artifact_path=exe))
    smoke_binary(exe, version)
    print(f"Built {exe}")
    print(f"Manifest {out_dir / 'manifest.json'}")


if __name__ == "__main__":
    main()
