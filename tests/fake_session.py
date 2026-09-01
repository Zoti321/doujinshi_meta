from __future__ import annotations

from collections.abc import Callable
from typing import Iterator

from doujinshi_meta.models import ComicTagsItem, Source
from doujinshi_meta.page_disambiguation import SearchCandidate


class FakeSourceSession:
    def __init__(
        self,
        *,
        source: Source = Source.JMCOMIC,
        hits: list[SearchCandidate] | None = None,
        total: int | None = None,
        fetch_fn: Callable[[str], ComicTagsItem] | None = None,
        search_fn: Callable[[str], tuple[list[SearchCandidate], int]] | None = None,
        comic_ids: list[str] | None = None,
    ) -> None:
        self.source = source
        self._hits = hits or []
        self._total = total if total is not None else len(self._hits)
        self._fetch_fn = fetch_fn
        self._search_fn = search_fn
        self._comic_ids = comic_ids or []
        self.closed = False
        self.search_calls: list[str] = []
        self.fetch_calls: list[str] = []

    def search(self, keyword: str) -> tuple[list[SearchCandidate], int]:
        self.search_calls.append(keyword)
        if self._search_fn is not None:
            return self._search_fn(keyword)
        return self._hits, self._total

    def fetch_comic(self, external_id: str) -> ComicTagsItem:
        self.fetch_calls.append(external_id)
        if self._fetch_fn is None:
            raise RuntimeError("fetch_fn not configured")
        return self._fetch_fn(external_id)

    def iter_comic_ids(self) -> Iterator[str]:
        return iter(self._comic_ids)

    def close(self) -> None:
        self.closed = True


def search_candidate(
    external_id: str,
    title: str = "title",
    *,
    list_page_count: int | None = None,
) -> SearchCandidate:
    return SearchCandidate(
        external_id=external_id,
        title=title,
        list_page_count=list_page_count,
    )
