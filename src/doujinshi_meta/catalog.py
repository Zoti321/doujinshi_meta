from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import TextIO

from doujinshi_meta.models import (
    CatalogStats,
    Source,
    TagCatalogResponse,
    normalize_kinds,
    utc_now_iso,
    validate_kinds_for_source,
)
from doujinshi_meta.sources.bika import BikaClient
from doujinshi_meta.sources.bika_ops import extract_tags_bika, open_bika_client
from doujinshi_meta.sources.jmcomic_ops import create_jmcomic_client, extract_tags_jmcomic
from doujinshi_meta.tag_counter import TagCounter

DEFAULT_DELAY = {Source.BIKA: 1.5, Source.JMCOMIC: 0.4}


def _log(stderr: TextIO, message: str) -> None:
    print(message, file=stderr)


def build_catalog(
    source: Source | str,
    *,
    proxy: str | None = None,
    delay: float | None = None,
    limit: int | None = None,
    kinds: list[str] | None = None,
    checkpoint: Path | None = None,
    resume: bool = False,
    stderr: TextIO | None = None,
    credentials_path: Path | None = None,
) -> TagCatalogResponse:
    src = Source(source)
    normalized_kinds = normalize_kinds(kinds)
    validate_kinds_for_source(src, normalized_kinds)
    err_stream = stderr or sys.stderr
    wait = delay if delay is not None else DEFAULT_DELAY[src]
    counter = TagCounter()
    stats = CatalogStats()
    seen_ids: set[str] = set()
    pending_ids: list[str] = []
    phase = "enum"

    if checkpoint and resume and checkpoint.is_file():
        state = json.loads(checkpoint.read_text(encoding="utf-8"))
        checkpoint_kinds = state.get("kinds")
        if checkpoint_kinds is not None:
            checkpoint_kinds = normalize_kinds(checkpoint_kinds)
        if checkpoint_kinds != normalized_kinds:
            raise RuntimeError(
                "checkpoint kinds 与当前 --kind 不一致："
                f"checkpoint={checkpoint_kinds or '全量'}, current={normalized_kinds or '全量'}"
            )
        counter = TagCounter.from_checkpoint_dict(state.get("tag_counter", {}))
        seen_ids = set(state.get("seen_ids", []))
        pending_ids = list(state.get("pending_ids", []))
        phase = state.get("phase", "detail")
        stats.albums_scanned = state.get("stats", {}).get("albums_scanned", 0)
        stats.errors = state.get("stats", {}).get("errors", 0)
        _log(err_stream, f"[catalog] resumed: phase={phase}, seen={len(seen_ids)}")

    def save_checkpoint() -> None:
        if not checkpoint:
            return
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "1.0",
            "source": src.value,
            "phase": phase,
            "kinds": normalized_kinds,
            "seen_ids": sorted(seen_ids),
            "pending_ids": pending_ids,
            "tag_counter": counter.to_checkpoint_dict(),
            "stats": {
                "albums_scanned": stats.albums_scanned,
                "errors": stats.errors,
            },
        }
        checkpoint.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if src == Source.JMCOMIC:
        client = create_jmcomic_client(proxy)

        def fetch_tags_for_id(cid: str):
            album = client.get_album_detail(cid)
            return extract_tags_jmcomic(album)

        def iter_ids():
            from doujinshi_meta.sources.jmcomic_ops import iter_comic_ids_jmcomic

            yield from iter_comic_ids_jmcomic(client)

    else:
        bika = open_bika_client(proxy, credentials_path=credentials_path)
        client = bika

        def fetch_tags_for_id(cid: str):
            comic = bika.get_comic(cid)
            return extract_tags_bika(comic)

        def iter_ids():
            from doujinshi_meta.sources.bika_ops import iter_comic_ids_bika

            yield from iter_comic_ids_bika(bika)

    try:
        if phase == "enum" and not pending_ids:
            _log(err_stream, "[catalog] enumerating comic ids...")
            for cid in iter_ids():
                if cid not in seen_ids:
                    seen_ids.add(cid)
                    pending_ids.append(cid)
                if limit and len(pending_ids) >= limit:
                    break
            phase = "detail"
            save_checkpoint()
            _log(err_stream, f"[catalog] enum done: {len(pending_ids)} ids")

        _log(err_stream, "[catalog] fetching details...")
        processed = 0
        while pending_ids:
            cid = pending_ids.pop(0)
            try:
                tags = fetch_tags_for_id(cid)
                counter.absorb(tags)
                stats.albums_scanned += 1
                processed += 1
                if processed % 50 == 0:
                    save_checkpoint()
                    _log(err_stream, f"[catalog] progress: {stats.albums_scanned} albums")
            except Exception as exc:
                stats.errors += 1
                _log(err_stream, f"[catalog] error {cid}: {exc}")
            if limit and stats.albums_scanned >= limit:
                break
            time.sleep(wait)
    finally:
        if src == Source.BIKA and isinstance(client, BikaClient):
            client.close()
        save_checkpoint()

    kind_filter = set(normalized_kinds) if normalized_kinds is not None else None
    tags = counter.to_entries(kinds=kind_filter)
    stats.tags_unique = len(tags)
    return TagCatalogResponse(
        source=src.value,
        generated_at=utc_now_iso(),
        stats=stats,
        kinds=normalized_kinds,
        tags=tags,
    )
