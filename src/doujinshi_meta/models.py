from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Sequence


class Source(StrEnum):
    BIKA = "bika"
    JMCOMIC = "jmcomic"


class TagKind(StrEnum):
    TAG = "tag"
    PARODY = "parody"
    CHARACTER = "character"
    AUTHOR = "author"


SOURCE_KINDS: dict[Source, frozenset[str]] = {
    Source.BIKA: frozenset({TagKind.TAG, TagKind.AUTHOR}),
    Source.JMCOMIC: frozenset(
        {TagKind.TAG, TagKind.PARODY, TagKind.CHARACTER, TagKind.AUTHOR}
    ),
}


def normalize_kinds(kinds: Sequence[str] | None) -> list[str] | None:
    if kinds is None:
        return None
    unique = sorted({kind.lower() for kind in kinds})
    if not unique:
        raise ValueError("至少指定一个 --kind")
    return unique


def validate_kinds_for_source(source: Source, kinds: list[str] | None) -> None:
    if kinds is None:
        return
    allowed = SOURCE_KINDS[source]
    invalid = [kind for kind in kinds if kind not in allowed]
    if invalid:
        allowed_str = ", ".join(sorted(allowed))
        invalid_str = ", ".join(invalid)
        raise ValueError(
            f"来源站 {source.value} 不支持 kind: {invalid_str}；允许: {allowed_str}"
        )


@dataclass
class TagRef:
    kind: str
    name: str

    def key(self) -> tuple[str, str]:
        return (self.kind, self.name)


@dataclass
class TagCatalogEntry:
    kind: str
    name: str
    count: int


@dataclass
class ComicTagsItem:
    external_id: str
    title: str
    tags: list[TagRef]
    page_count: int | None = None


@dataclass
class FetchError:
    external_id: str
    message: str


@dataclass
class CatalogStats:
    albums_scanned: int = 0
    tags_unique: int = 0
    errors: int = 0


@dataclass
class TagCatalogResponse:
    schema_version: str = "1.0"
    command: str = "catalog"
    source: str = ""
    generated_at: str = ""
    stats: CatalogStats = field(default_factory=CatalogStats)
    kinds: list[str] | None = None
    tags: list[TagCatalogEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if data.get("kinds") is None:
            data.pop("kinds", None)
        return data


@dataclass
class FetchTagsResponse:
    schema_version: str = "1.0"
    command: str = "fetch"
    source: str = ""
    generated_at: str = ""
    items: list[ComicTagsItem] = field(default_factory=list)
    errors: list[FetchError] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "command": self.command,
            "source": self.source,
            "generated_at": self.generated_at,
            "items": [_comic_tags_item_dict(item) for item in self.items],
            "errors": [asdict(err) for err in self.errors],
        }


@dataclass
class AmbiguousCandidate:
    external_id: str
    title: str
    page_count: int | None = None


@dataclass
class SearchAmbiguous:
    query: str
    candidates: list[AmbiguousCandidate]


@dataclass
class SearchTagsResponse:
    schema_version: str = "1.0"
    command: str = "search"
    source: str = ""
    query: str = ""
    total_hits: int = 0
    generated_at: str = ""
    items: list[ComicTagsItem] = field(default_factory=list)
    errors: list[FetchError] = field(default_factory=list)
    ambiguous: list[SearchAmbiguous] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "command": self.command,
            "source": self.source,
            "query": self.query,
            "total_hits": self.total_hits,
            "generated_at": self.generated_at,
            "items": [_comic_tags_item_dict(item) for item in self.items],
            "errors": [asdict(err) for err in self.errors],
            "ambiguous": [_search_ambiguous_dict(entry) for entry in self.ambiguous],
        }


@dataclass
class BatchScrapeItem(ComicTagsItem):
    local_id: str = ""


@dataclass
class BatchAmbiguous:
    local_id: str
    title: str
    candidates: list[AmbiguousCandidate]


@dataclass
class BatchError:
    local_id: str
    message: str


@dataclass
class SearchBatchResponse:
    schema_version: str = "1.0"
    command: str = "search-batch"
    source: str = ""
    generated_at: str = ""
    items: list[BatchScrapeItem] = field(default_factory=list)
    ambiguous: list[BatchAmbiguous] = field(default_factory=list)
    errors: list[BatchError] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "command": self.command,
            "source": self.source,
            "generated_at": self.generated_at,
            "items": [_batch_scrape_item_dict(item) for item in self.items],
            "ambiguous": [_batch_ambiguous_dict(entry) for entry in self.ambiguous],
            "errors": [asdict(err) for err in self.errors],
        }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _comic_tags_item_dict(item: ComicTagsItem) -> dict[str, Any]:
    data: dict[str, Any] = {
        "external_id": item.external_id,
        "title": item.title,
        "tags": [asdict(tag) for tag in item.tags],
    }
    if item.page_count is not None:
        data["page_count"] = item.page_count
    return data


def _ambiguous_candidate_dict(candidate: AmbiguousCandidate) -> dict[str, Any]:
    data: dict[str, Any] = {
        "external_id": candidate.external_id,
        "title": candidate.title,
    }
    if candidate.page_count is not None:
        data["page_count"] = candidate.page_count
    return data


def _search_ambiguous_dict(entry: SearchAmbiguous) -> dict[str, Any]:
    return {
        "query": entry.query,
        "candidates": [_ambiguous_candidate_dict(c) for c in entry.candidates],
    }


def _batch_scrape_item_dict(item: BatchScrapeItem) -> dict[str, Any]:
    data = _comic_tags_item_dict(item)
    data["local_id"] = item.local_id
    return data


def _batch_ambiguous_dict(entry: BatchAmbiguous) -> dict[str, Any]:
    return {
        "local_id": entry.local_id,
        "title": entry.title,
        "candidates": [_ambiguous_candidate_dict(c) for c in entry.candidates],
    }
