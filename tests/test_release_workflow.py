from __future__ import annotations

from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "release.yml"


def _workflow_text() -> str:
    assert WORKFLOW.is_file(), f"缺少 workflow 文件: {WORKFLOW}"
    return WORKFLOW.read_text(encoding="utf-8")


def test_release_workflow_triggers_on_version_tags() -> None:
    text = _workflow_text()
    assert "workflow_dispatch" in text
    assert "v*" in text


def test_release_workflow_runs_on_windows() -> None:
    assert "windows-latest" in _workflow_text()


def test_release_workflow_syncs_dev_and_builds_wheel() -> None:
    text = _workflow_text()
    assert "uv sync" in text
    assert "scripts/build.py" in text
    assert "--wheel" in text


def test_release_workflow_validates_tag_against_pyproject_version() -> None:
    text = _workflow_text()
    assert "Validate release tag matches project version" in text
    assert "github.ref_name" in text
    assert "steps.version.outputs.value" in text


def test_release_workflow_smokes_binary_without_network_fetch() -> None:
    text = _workflow_text()
    assert "--version" in text
    assert "--help" in text
    assert "steps.version.outputs.value" in text
    assert "--smoke-full" not in text
    assert "fetch" not in text


def test_release_workflow_fails_on_missing_release_files() -> None:
    text = _workflow_text()
    assert "fail_on_unmatched_files: true" in text


def test_release_workflow_uploads_zip_wheel_and_sdist() -> None:
    text = _workflow_text()
    assert "softprops/action-gh-release" in text
    assert ".zip" in text
    assert ".whl" in text
    assert ".tar.gz" in text


def test_release_workflow_places_release_after_build() -> None:
    text = _workflow_text()
    build_idx = text.index("scripts/build.py")
    release_idx = text.index("softprops/action-gh-release")
    assert build_idx < release_idx
