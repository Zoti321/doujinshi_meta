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
    CATEGORY = "category"
    WORK = "work"
    ACTOR = "actor"
    AUTHOR = "author"


SOURCE_KINDS: dict[Source, frozenset[str]] = {
    Source.BIKA: frozenset({TagKind.TAG, TagKind.CATEGORY, TagKind.AUTHOR}),
    Source.JMCOMIC: frozenset({TagKind.TAG, TagKind.WORK, TagKind.ACTOR, TagKind.AUTHOR}),
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
        return asdict(self)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
