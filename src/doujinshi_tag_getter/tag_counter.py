from __future__ import annotations

from collections import Counter

from doujinshi_tag_getter.models import TagCatalogEntry, TagRef


class TagCounter:
    def __init__(self) -> None:
        self._counter: Counter[tuple[str, str]] = Counter()

    def absorb(self, tags: list[TagRef]) -> None:
        self._counter.update(tag.key() for tag in tags)

    def merge(self, other: TagCounter) -> None:
        self._counter.update(other._counter)

    def to_entries(self, *, kinds: set[str] | None = None) -> list[TagCatalogEntry]:
        items = self._counter.most_common()
        if kinds is not None:
            items = [item for item in items if item[0][0] in kinds]
        return [
            TagCatalogEntry(kind=kind, name=name, count=count)
            for (kind, name), count in items
        ]
    def to_checkpoint_dict(self) -> dict[str, int]:
        return {f"{kind}:{name}": count for (kind, name), count in self._counter.items()}

    @classmethod
    def from_checkpoint_dict(cls, data: dict[str, int]) -> TagCounter:
        counter = cls()
        for key, count in data.items():
            kind, _, name = key.partition(":")
            counter._counter[(kind, name)] = count
        return counter
