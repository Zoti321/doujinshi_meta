"""Doujinshi metadata crawler (Bika / JMComic)."""

from doujinshi_meta.catalog import build_catalog
from doujinshi_meta.fetch import fetch_tags
from doujinshi_meta.models import Source
from doujinshi_meta.search import search_tags
from doujinshi_meta.search_batch import search_batch_tags

__all__ = [
    "build_catalog",
    "fetch_tags",
    "search_tags",
    "search_batch_tags",
    "Source",
]
