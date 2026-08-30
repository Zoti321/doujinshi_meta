from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class Source(StrEnum):
    BIKA = "bika"
    JMCOMIC = "jmcomic"


class TagKind(StrEnum):
    TAG = "tag"
    CATEGORY = "category"
    WORK = "work"
    ACTOR = "actor"
    AUTHOR = "author"


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
    tags: list[TagCatalogEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FetchTagsResponse:
    schema_version: str = "1.0"
    command: str = "fetch"
    source: str = ""
    generated_at: str = ""
    items: list[ComicTagsItem] = field(default_factory=list)
    errors: list[FetchError] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
