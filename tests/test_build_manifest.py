from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

MANIFEST_FIELDS = ("name", "version", "platform", "artifact", "sha256", "built_at")


def _load_build_manifest():
    path = Path(__file__).resolve().parents[1] / "scripts" / "build_manifest.py"
    spec = importlib.util.spec_from_file_location("build_manifest", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_sha256_hex_known_content(tmp_path: Path) -> None:
    mod = _load_build_manifest()
    artifact = tmp_path / "sample.bin"
    artifact.write_bytes(b"hello")

    assert mod.sha256_hex(artifact) == (
        "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    )


def test_manifest_payload_shape_and_sha256(tmp_path: Path) -> None:
    mod = _load_build_manifest()
    artifact = tmp_path / "djm.exe"
    artifact.write_bytes(b"fake-exe")
    built_at = datetime(2026, 9, 2, 5, 0, 0, tzinfo=timezone.utc)

    payload = mod.manifest_payload(
        version="0.3.0",
        artifact_path=artifact,
        built_at=built_at,
    )

    assert set(payload.keys()) == set(MANIFEST_FIELDS)
    assert payload["name"] == "doujinshi-meta"
    assert payload["version"] == "0.3.0"
    assert payload["platform"] == "windows-x64"
    assert payload["artifact"] == "djm.exe"
    assert payload["sha256"] == mod.sha256_hex(artifact)
    assert payload["built_at"] == "2026-09-02T05:00:00+00:00"


def test_write_manifest_roundtrip(tmp_path: Path) -> None:
    mod = _load_build_manifest()
    artifact = tmp_path / "djm.exe"
    artifact.write_bytes(b"x")
    payload = mod.manifest_payload(
        version="1.0.0",
        artifact_path=artifact,
        built_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    manifest_path = tmp_path / "manifest.json"

    mod.write_manifest(manifest_path, payload)

    loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert loaded == payload
    assert loaded["sha256"] == mod.sha256_hex(artifact)
