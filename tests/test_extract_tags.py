from __future__ import annotations

from types import SimpleNamespace

from doujinshi_meta.models import TagKind
from doujinshi_meta.sources.bika_ops import extract_tags_bika
from doujinshi_meta.sources.jmcomic_ops import extract_tags_jmcomic


def test_extract_tags_bika_skips_categories() -> None:
    tags = extract_tags_bika(
        {
            "tags": ["全彩"],
            "categories": ["同人"],
            "author": "作者A",
        }
    )
    assert {(t.kind, t.name) for t in tags} == {
        (TagKind.TAG, "全彩"),
        (TagKind.AUTHOR, "作者A"),
    }


def test_extract_tags_jmcomic_maps_parody_and_character() -> None:
    album = SimpleNamespace(
        tags=["巨乳"],
        works=["原神"],
        actors=["申鶴"],
        authors=["うぱ西"],
    )
    tags = extract_tags_jmcomic(album)
    assert {(t.kind, t.name) for t in tags} == {
        (TagKind.TAG, "巨乳"),
        (TagKind.PARODY, "原神"),
        (TagKind.CHARACTER, "申鶴"),
        (TagKind.AUTHOR, "うぱ西"),
    }
