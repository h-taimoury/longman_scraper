"""Resolves cross-reference senses (e.g. "→ books") by fetching the target
dictionary page and pulling out its sense content.

A cross-reference sense on the original page has no definition of its own —
it only points elsewhere. To give callers a usable Sense, we fetch the
target page and substitute its first defined sense in place of the pointer.
"""

from __future__ import annotations

from bs4 import BeautifulSoup
from bs4.element import Tag
from playwright.async_api import Page

from ..browser import fetch_html_in_page
from .sense import has_definition


async def fetch_cross_reference_sense(page: Page, url: str) -> Tag | None:
    """Fetch `url` and return its first dictionary sense that has a definition.

    Returns None if the page has no such sense (e.g. it also turns out to be
    another pointer). Fetch failures propagate as PageLoadError.
    """
    html = await fetch_html_in_page(page, url)
    soup = BeautifulSoup(html, "lxml")

    for sense_el in soup.select("div.dictionary span.dictentry span.Sense"):
        if has_definition(sense_el):
            return sense_el
    return None
