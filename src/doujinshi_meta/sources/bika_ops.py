from __future__ import annotations

from pathlib import Path
from typing import Iterator

from doujinshi_meta.config import (
    is_bika_network_error,
    require_bika_credentials,
    save_bika_credentials,
)
from doujinshi_meta.models import ComicTagsItem, TagKind, TagRef
from doujinshi_meta.page_disambiguation import SearchCandidate
from doujinshi_meta.sources.bika import BikaClient


def open_bika_client(
    proxy: str | None = None,
    *,
    credentials_path: Path | None = None,
) -> BikaClient:
    """Resolve credentials, login, and persist after interactive success."""
    creds = require_bika_credentials(credentials_path=credentials_path)
    client = BikaClient(creds.account, creds.password, proxy=proxy)
    try:
        try:
            client.login()
        except RuntimeError as exc:
            if not creds.from_file or is_bika_network_error(exc):
                raise
            client.close()
            creds = require_bika_credentials(
                credentials_path=credentials_path,
                ignore_stored=True,
            )
            client = BikaClient(creds.account, creds.password, proxy=proxy)
            client.login()
        if creds.from_interactive:
            save_bika_credentials(
                creds.account,
                creds.password,
                path=credentials_path,
            )
        return client
    except Exception:
        client.close()
        raise


def extract_tags_bika(comic: dict) -> list[TagRef]:
    tags: list[TagRef] = []
    for name in comic.get("tags") or []:
        tags.append(TagRef(kind=TagKind.TAG, name=name))
    author = comic.get("author")
    if author:
        tags.append(TagRef(kind=TagKind.AUTHOR, name=author))
    return tags


def _bika_page_count(comic: dict) -> int | None:
    raw = comic.get("pagesCount")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def fetch_comic_bika(client: BikaClient, comic_id: str) -> ComicTagsItem:
    comic = client.get_comic(comic_id)
    return ComicTagsItem(
        external_id=comic["_id"],
        title=comic.get("title") or "",
        tags=extract_tags_bika(comic),
        page_count=_bika_page_count(comic),
    )


def search_comics_bika(
    client: BikaClient, keyword: str
) -> tuple[list[SearchCandidate], int]:
    result = client.search_comics_page(keyword, page=1)
    docs = result.get("docs") or []
    total_raw = result.get("total")
    total_hits = int(total_raw) if total_raw is not None else len(docs)
    hits: list[SearchCandidate] = []
    for doc in docs:
        if not isinstance(doc, dict):
            continue
        comic_id = doc.get("_id")
        if not comic_id:
            continue
        hits.append(
            SearchCandidate(
                external_id=str(comic_id),
                title=doc.get("title") or "",
                list_page_count=_bika_page_count(doc),
            )
        )
    return hits, total_hits


def iter_comic_ids_bika(client: BikaClient) -> Iterator[str]:
    categories = client.list_categories()
    seen: set[str] = set()
    for cat in categories:
        title = cat.get("title") or cat.get("name")
        if not title:
            continue
        page = 1
        while True:
            result = client.list_comics_page(title, page)
            docs = result.get("docs") or result.get("comics") or []
            if not docs:
                break
            for doc in docs:
                cid = doc.get("_id")
                if cid and cid not in seen:
                    seen.add(cid)
                    yield cid
            pages = result.get("pages") or 1
            if page >= pages:
                break
            page += 1
