from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ARTIFACT_NAME = "djm.exe"
PACKAGE_NAME = "doujinshi-meta"
PLATFORM = "windows-x64"


def sha256_hex(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_payload(
    *,
    version: str,
    artifact_path: Path,
    built_at: datetime | None = None,
) -> dict[str, Any]:
    built = built_at or datetime.now(timezone.utc)
    return {
        "name": PACKAGE_NAME,
        "version": version,
        "platform": PLATFORM,
        "artifact": ARTIFACT_NAME,
        "sha256": sha256_hex(artifact_path),
        "built_at": built.isoformat(timespec="seconds"),
    }


def write_manifest(manifest_path: Path, payload: dict[str, Any]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
