from __future__ import annotations

from typing import Iterator

from jmcomic import JmMagicConstants, JmOption

from doujinshi_meta.models import ComicTagsItem, TagKind, TagRef

JMCOMIC_CATEGORIES = [
    JmMagicConstants.CATEGORY_ALL,
    JmMagicConstants.CATEGORY_DOUJIN,
    JmMagicConstants.CATEGORY_SINGLE,
    JmMagicConstants.CATEGORY_SHORT,
    JmMagicConstants.CATEGORY_HANMAN,
    JmMagicConstants.CATEGORY_MEIMAN,
    JmMagicConstants.CATEGORY_3D,
]


def create_jmcomic_client(proxy: str | None = None):
    option_dict = {
        "log": False,
        "client": {
            "impl": "api",
            "retry_times": 5,
            "cache": "level_option",
        },
    }
    if proxy:
        option_dict["client"]["postman"] = {
            "meta_data": {"proxies": proxy},
        }
    else:
        option_dict["client"]["postman"] = {
            "meta_data": {"proxies": None},
        }
    option = JmOption.construct(option_dict)
    return option.new_jm_client()


def extract_tags_jmcomic(album) -> list[TagRef]:
    tags: list[TagRef] = []
    for name in album.tags or []:
        tags.append(TagRef(kind=TagKind.TAG, name=name))
    for name in album.works or []:
        tags.append(TagRef(kind=TagKind.PARODY, name=name))
    for name in album.actors or []:
        tags.append(TagRef(kind=TagKind.CHARACTER, name=name))
    for name in album.authors or []:
        tags.append(TagRef(kind=TagKind.AUTHOR, name=name))
    return tags


def _album_page_count(album) -> int | None:
    raw = getattr(album, "page_count", None)
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def fetch_comic_jmcomic(client, album_id: str) -> ComicTagsItem:
    album = client.get_album_detail(album_id)
    return ComicTagsItem(
        external_id=str(album.album_id),
        title=album.name or "",
        tags=extract_tags_jmcomic(album),
        page_count=_album_page_count(album),
    )


def search_comics_jmcomic(
    client, keyword: str
) -> tuple[list[tuple[str, str, int | None]], int]:
    page = client.search_site(keyword, page=1)
    hits = [(str(album_id), title, None) for album_id, title in page.iter_id_title()]
    total_raw = getattr(page, "total", None)
    total_hits = int(total_raw) if total_raw is not None else len(hits)
    return hits, total_hits


def iter_comic_ids_jmcomic(client) -> Iterator[str]:
    seen: set[str] = set()
    for category in JMCOMIC_CATEGORIES:
        for page in client.categories_filter_gen(
            page=1,
            category=category,
            time=JmMagicConstants.TIME_ALL,
            order_by=JmMagicConstants.ORDER_BY_LATEST,
        ):
            for album_id, _title in page:
                aid = str(album_id)
                if aid not in seen:
                    seen.add(aid)
                    yield aid
