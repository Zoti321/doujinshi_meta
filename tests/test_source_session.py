from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from doujinshi_meta.models import ComicTagsItem, Source, TagRef
from doujinshi_meta.sources.session import (
    BikaSourceSession,
    DEFAULT_DELAY,
    JmcomicSourceSession,
    SearchHit,
    open_source_session,
)


def _item(comic_id: str, *, page_count: int | None = None) -> ComicTagsItem:
    return ComicTagsItem(
        external_id=comic_id,
        title="title",
        tags=[TagRef(kind="tag", name="sample")],
        page_count=page_count,
    )


def test_default_delay_per_source() -> None:
    assert DEFAULT_DELAY[Source.BIKA] == 1.5
    assert DEFAULT_DELAY[Source.JMCOMIC] == 0.4


def test_open_source_session_jmcomic() -> None:
    mock_client = MagicMock()
    with patch(
        "doujinshi_meta.sources.session.create_jmcomic_client",
        return_value=mock_client,
    ) as mock_create:
        session = open_source_session(Source.JMCOMIC, proxy="http://127.0.0.1:7890")

    assert isinstance(session, JmcomicSourceSession)
    assert session.source == Source.JMCOMIC
    mock_create.assert_called_once_with("http://127.0.0.1:7890")
    session.close()


def test_open_source_session_bika() -> None:
    mock_client = MagicMock()
    with patch(
        "doujinshi_meta.sources.session.open_bika_client",
        return_value=mock_client,
    ) as mock_open:
        session = open_source_session("bika", credentials_path=None)

    assert isinstance(session, BikaSourceSession)
    assert session.source == Source.BIKA
    mock_open.assert_called_once_with(None, credentials_path=None)
    session.close()
    mock_client.close.assert_called_once()


def test_jmcomic_session_search_and_fetch() -> None:
    client = MagicMock()
    hits: list[SearchHit] = [("1", "a", None)]
    with (
        patch(
            "doujinshi_meta.sources.session.search_comics_jmcomic",
            return_value=(hits, 99),
        ) as mock_search,
        patch(
            "doujinshi_meta.sources.session.fetch_comic_jmcomic",
            return_value=_item("1"),
        ) as mock_fetch,
    ):
        session = JmcomicSourceSession(client)
        result_hits, total = session.search("kw")
        item = session.fetch_comic("1")

    assert result_hits == hits
    assert total == 99
    assert item.external_id == "1"
    mock_search.assert_called_once_with(client, "kw")
    mock_fetch.assert_called_once_with(client, "1")


def test_bika_session_closes_client() -> None:
    client = MagicMock()
    session = BikaSourceSession(client)
    session.close()
    client.close.assert_called_once()


def test_bika_session_iter_comic_ids() -> None:
    client = MagicMock()
    with patch(
        "doujinshi_meta.sources.session.iter_comic_ids_bika",
        return_value=iter(["a", "b"]),
    ):
        session = BikaSourceSession(client)
        assert list(session.iter_comic_ids()) == ["a", "b"]
