from __future__ import annotations

from doujinshi_tag_getter.models import TagRef, normalize_kinds
from doujinshi_tag_getter.tag_counter import TagCounter


def test_normalize_kinds_lowercases() -> None:
    assert normalize_kinds(["TAG", "Author"]) == ["author", "tag"]


def test_to_entries_filters_by_kind() -> None:
    counter = TagCounter()
    counter.absorb(
        [
            TagRef(kind="tag", name="巨乳"),
            TagRef(kind="work", name="原神"),
            TagRef(kind="author", name="作者A"),
        ]
    )

    entries = counter.to_entries(kinds={"tag"})

    assert len(entries) == 1
    assert entries[0].kind == "tag"
    assert entries[0].name == "巨乳"


def test_to_entries_without_kinds_returns_all() -> None:
    counter = TagCounter()
    counter.absorb(
        [
            TagRef(kind="tag", name="a"),
            TagRef(kind="work", name="b"),
        ]
    )

    entries = counter.to_entries()

    assert len(entries) == 2
