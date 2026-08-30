from __future__ import annotations

from typing import Iterator

from doujinshi_tag_getter.models import ComicTagsItem, TagKind, TagRef
from doujinshi_tag_getter.sources.bika import BikaClient


def extract_tags_bika(comic: dict) -> list[TagRef]:
    tags: list[TagRef] = []
    for name in comic.get("tags") or []:
        tags.append(TagRef(kind=TagKind.TAG, name=name))
    for name in comic.get("categories") or []:
        tags.append(TagRef(kind=TagKind.CATEGORY, name=name))
    author = comic.get("author")
    if author:
        tags.append(TagRef(kind=TagKind.AUTHOR, name=author))
    return tags


def fetch_comic_bika(client: BikaClient, comic_id: str) -> ComicTagsItem:
    comic = client.get_comic(comic_id)
    return ComicTagsItem(
        external_id=comic["_id"],
        title=comic.get("title") or "",
        tags=extract_tags_bika(comic),
    )


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
