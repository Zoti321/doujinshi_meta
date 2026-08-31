"""Bika catalog enumeration must unwrap API data envelopes."""

from __future__ import annotations

from unittest.mock import MagicMock

from doujinshi_tag_getter.sources.bika import BikaClient
from doujinshi_tag_getter.sources.bika_ops import iter_comic_ids_bika


def test_list_categories_unwraps_categories_array() -> None:
    client = BikaClient("u", "p")
    client._token = "tok"
    client._request = MagicMock(
        return_value={
            "categories": [
                {"title": "同人", "_id": "c1"},
                {"title": "短篇", "_id": "c2"},
            ]
        }
    )

    cats = client.list_categories()

    assert cats == [
        {"title": "同人", "_id": "c1"},
        {"title": "短篇", "_id": "c2"},
    ]


def test_list_comics_page_unwraps_comics_envelope() -> None:
    client = BikaClient("u", "p")
    client._token = "tok"
    client._request = MagicMock(
        return_value={
            "comics": {
                "docs": [{"_id": "a1", "title": "t"}],
                "page": 1,
                "pages": 1,
                "total": 1,
            }
        }
    )

    page = client.list_comics_page("同人", 1)

    assert page["docs"][0]["_id"] == "a1"
    assert page["pages"] == 1


def test_iter_comic_ids_bika_yields_ids_from_nested_shapes() -> None:
    client = MagicMock()
    client.list_categories.return_value = [{"title": "同人"}]
    client.list_comics_page.return_value = {
        "docs": [{"_id": "id-1"}, {"_id": "id-2"}],
        "pages": 1,
    }

    assert list(iter_comic_ids_bika(client)) == ["id-1", "id-2"]
