from __future__ import annotations

from unittest.mock import patch

from doujinshi_meta.fetch import fetch_tags
from doujinshi_meta.models import ComicTagsItem, TagRef
from tests.fake_session import FakeSourceSession


def _item(comic_id: str) -> ComicTagsItem:
    return ComicTagsItem(
        external_id=comic_id,
        title="title",
        tags=[TagRef(kind="tag", name="sample")],
    )


def test_fetch_tags_uses_source_session() -> None:
    fake = FakeSourceSession(fetch_fn=lambda cid: _item(cid))

    with patch("doujinshi_meta.fetch.open_source_session", return_value=fake):
        result = fetch_tags("jmcomic", ["a", "b"], delay=0)

    assert len(result.items) == 2
    assert result.errors == []
    assert fake.fetch_calls == ["a", "b"]
    assert fake.closed


def test_fetch_tags_records_fetch_errors() -> None:
    def fetch_fn(cid: str) -> ComicTagsItem:
        if cid == "bad":
            raise RuntimeError("boom")
        return _item(cid)

    fake = FakeSourceSession(fetch_fn=fetch_fn)

    with patch("doujinshi_meta.fetch.open_source_session", return_value=fake):
        result = fetch_tags("jmcomic", ["ok", "bad"], delay=0)

    assert len(result.items) == 1
    assert len(result.errors) == 1
    assert result.errors[0].external_id == "bad"
