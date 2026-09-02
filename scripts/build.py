from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from build_manifest import manifest_payload, write_manifest

PREFLIGHT_EXIT = 2
BUILD_TOOLS_URL = "https://visualstudio.microsoft.com/visual-cpp-build-tools/"
SMOKE_FULL_COMIC_ID = "410090"


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def dist_root() -> Path:
    return project_root() / "dist"


def read_project_version() -> str:
    data = tomllib.loads((project_root() / "pyproject.toml").read_text(encoding="utf-8"))
    return data["project"]["version"]


def dist_dir(version: str) -> Path:
    return dist_root() / f"djm-{version}-windows-x64"


def release_zip_path(version: str) -> Path:
    return dist_root() / f"djm-{version}-windows-x64.zip"


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


def nuitka_command(output_dir: Path, *, onedir: bool = False) -> list[str]:
    cli_entry = project_root() / "src" / "doujinshi_meta" / "cli.py"
    cmd = [
        sys.executable,
        "-m",
        "nuitka",
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
    if onedir:
        cmd.insert(4, "--standalone")
    else:
        cmd.insert(4, "--onefile")
    return cmd


def find_exe(output_dir: Path) -> Path:
    direct = output_dir / "djm.exe"
    if direct.is_file():
        return direct
    for candidate in output_dir.rglob("djm.exe"):
        if candidate.is_file():
            return candidate
    raise RuntimeError(f"Nuitka 未产出 {output_dir}/**/djm.exe")


def build_binary(output_dir: Path, *, onedir: bool = False) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(nuitka_command(output_dir, onedir=onedir), check=True, cwd=project_root())
    return find_exe(output_dir)


def build_wheel() -> None:
    root = dist_root()
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["uv", "build", f"--out-dir={root}"],
        check=True,
        cwd=project_root(),
    )


def clean_artifacts(version: str) -> None:
    root = dist_root()
    targets: list[Path] = [
        dist_dir(version),
        release_zip_path(version),
        root / f"doujinshi_meta-{version}-py3-none-any.whl",
        root / f"doujinshi_meta-{version}.tar.gz",
    ]
    for path in targets:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.is_file():
            path.unlink()


def create_release_zip(out_dir: Path, version: str) -> Path:
    zip_path = release_zip_path(version)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    exe = find_exe(out_dir)
    manifest = out_dir / "manifest.json"
    if not manifest.is_file():
        raise RuntimeError(f"缺少 manifest: {manifest}")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(exe, arcname="djm.exe")
        archive.write(manifest, arcname="manifest.json")
    return zip_path


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


def smoke_full_binary(exe: Path) -> None:
    result = subprocess.run(
        [str(exe), "fetch", "--source", "jmcomic", "--ids", SMOKE_FULL_COMIC_ID],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"smoke-full 失败: {exe} fetch exit {result.returncode}\n"
            f"{result.stderr or result.stdout}"
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="构建 doujinshi-meta 分发产物")
    parser.add_argument(
        "--wheel",
        action="store_true",
        help="额外调用 uv build 产出 wheel 与 sdist",
    )
    parser.add_argument(
        "--onedir",
        action="store_true",
        help="Nuitka 目录模式（便于排查缺模块）",
    )
    parser.add_argument(
        "--smoke-full",
        action="store_true",
        help="构建后对 exe 执行真网 jmcomic fetch（仅本地推荐，需网络）",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="清理 dist/ 下当前版本相关产物；与 --no-binary --wheel 同用时仅清理不构建二进制",
    )
    parser.add_argument(
        "--no-binary",
        action="store_true",
        help="跳过 Nuitka 二进制构建",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    version = read_project_version()

    if args.clean:
        clean_artifacts(version)
        print(f"Cleaned dist artifacts for version {version}")

    if args.wheel:
        build_wheel()
        print(f"Built wheel/sdist in {dist_root()}")

    if args.no_binary:
        return

    error = preflight_error()
    if error:
        print(error, file=sys.stderr)
        raise SystemExit(PREFLIGHT_EXIT)

    out_dir = dist_dir(version)
    exe = build_binary(out_dir, onedir=args.onedir)
    write_manifest(out_dir / "manifest.json", manifest_payload(version=version, artifact_path=exe))
    smoke_binary(exe, version)
    if args.smoke_full:
        smoke_full_binary(exe)
    zip_path = create_release_zip(out_dir, version)
    print(f"Built {exe}")
    print(f"Manifest {out_dir / 'manifest.json'}")
    print(f"Release zip {zip_path}")


if __name__ == "__main__":
    main()
