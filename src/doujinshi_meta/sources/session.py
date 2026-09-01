from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Protocol

from doujinshi_meta.models import ComicTagsItem, Source
from doujinshi_meta.sources.bika import BikaClient
from doujinshi_meta.sources.bika_ops import (
    fetch_comic_bika,
    iter_comic_ids_bika,
    open_bika_client,
    search_comics_bika,
)
from doujinshi_meta.sources.jmcomic_ops import (
    create_jmcomic_client,
    fetch_comic_jmcomic,
    iter_comic_ids_jmcomic,
    search_comics_jmcomic,
)

SearchHit = tuple[str, str, int | None]

DEFAULT_DELAY: dict[Source, float] = {
    Source.BIKA: 1.5,
    Source.JMCOMIC: 0.4,
}


class SourceSession(Protocol):
    @property
    def source(self) -> Source: ...

    def search(self, keyword: str) -> tuple[list[SearchHit], int]: ...

    def fetch_comic(self, external_id: str) -> ComicTagsItem: ...

    def iter_comic_ids(self) -> Iterator[str]: ...

    def close(self) -> None: ...


@dataclass
class BikaSourceSession:
    _client: BikaClient

    @property
    def source(self) -> Source:
        return Source.BIKA

    def search(self, keyword: str) -> tuple[list[SearchHit], int]:
        return search_comics_bika(self._client, keyword)

    def fetch_comic(self, external_id: str) -> ComicTagsItem:
        return fetch_comic_bika(self._client, external_id)

    def iter_comic_ids(self) -> Iterator[str]:
        return iter_comic_ids_bika(self._client)

    def close(self) -> None:
        self._client.close()


@dataclass
class JmcomicSourceSession:
    _client: object

    @property
    def source(self) -> Source:
        return Source.JMCOMIC

    def search(self, keyword: str) -> tuple[list[SearchHit], int]:
        return search_comics_jmcomic(self._client, keyword)

    def fetch_comic(self, external_id: str) -> ComicTagsItem:
        return fetch_comic_jmcomic(self._client, external_id)

    def iter_comic_ids(self) -> Iterator[str]:
        return iter_comic_ids_jmcomic(self._client)

    def close(self) -> None:
        return None


def open_source_session(
    source: Source | str,
    *,
    proxy: str | None = None,
    credentials_path: Path | None = None,
) -> SourceSession:
    src = Source(source)
    if src == Source.JMCOMIC:
        return JmcomicSourceSession(create_jmcomic_client(proxy))
    return BikaSourceSession(
        open_bika_client(proxy, credentials_path=credentials_path)
    )
