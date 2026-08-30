"""Doujinshi tag metadata crawler."""

from doujinshi_tag_getter.catalog import build_catalog
from doujinshi_tag_getter.fetch import fetch_tags
from doujinshi_tag_getter.models import Source

__all__ = ["build_catalog", "fetch_tags", "Source"]
