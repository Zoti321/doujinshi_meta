from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "docs" / "integration.md"
README = ROOT / "README.md"


def test_integration_doc_has_standalone_binary_section() -> None:
    text = INTEGRATION.read_text(encoding="utf-8")
    assert "获取 Standalone 二进制" in text
    assert "manifest.json" in text
    assert "sha256" in text
    assert "djm-{version}-windows-x64.zip" in text or "windows-x64.zip" in text


def test_integration_doc_describes_manifest_fields_and_verification() -> None:
    text = INTEGRATION.read_text(encoding="utf-8")
    for field in ("name", "version", "platform", "artifact", "sha256", "built_at"):
        assert field in text


def test_integration_doc_has_flutter_bundling_pointer() -> None:
    text = INTEGRATION.read_text(encoding="utf-8")
    assert "Flutter" in text
    assert "native_assets" in text or "Process.run" in text or "子进程" in text


def test_integration_doc_links_release_and_wheel() -> None:
    text = INTEGRATION.read_text(encoding="utf-8")
    assert "GitHub Release" in text or "Release" in text
    assert ".whl" in text


def test_readme_has_build_prerequisites_and_commands() -> None:
    text = README.read_text(encoding="utf-8")
    assert "scripts/build.py" in text
    assert "MSVC" in text or "Visual Studio Build Tools" in text
    assert "uv" in text
    assert "Windows" in text


def test_readme_documents_build_script_options() -> None:
    text = README.read_text(encoding="utf-8")
    assert "--wheel" in text
    assert "--onedir" in text
    assert "--smoke-full" in text or "smoke-full" in text
    assert "--clean" in text


def test_docs_align_with_nuitka_adr_vocabulary() -> None:
    integration = INTEGRATION.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    assert "Standalone 二进制" in integration
    assert "Nuitka" in readme or "Nuitka" in integration
    assert "分发产物" in integration or "manifest.json" in integration
