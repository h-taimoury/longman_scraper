"""Public entrypoints for longman_scraper."""

from __future__ import annotations

import asyncio

from .browser import fetch_html, launch_browser
from .exceptions import WordNotFoundError
from .parser import parse_word_page
from .schema import WordResult

BASE_URL = "https://www.ldoceonline.com"
DICTIONARY_PATH = "/dictionary/"


async def scrape_word(word: str) -> WordResult:
    """Scrape a single word from ldoceonline.com.

    Launches and tears down its own browser instance. For scraping many
    words, prefer `scrape_words`, which shares one browser across all of
    them.

    Raises:
        WordNotFoundError: if the page loads but has no dictionary entries.
        PageLoadError: if the page fails to load.
    """
    async with launch_browser() as browser:
        return await _scrape_word_with_browser(word, browser)


async def scrape_words(words: list[str]) -> dict[str, WordResult]:
    """Scrape multiple words concurrently, sharing a single browser instance.

    Returns a dict keyed by the original word string. If scraping a word
    raises, that exception propagates (use `asyncio.gather(..., return_exceptions=True)`
    yourself via a custom loop if you need partial results instead).
    """
    async with launch_browser() as browser:
        results = await asyncio.gather(
            *(_scrape_word_with_browser(word, browser) for word in words)
        )
    return dict(zip(words, results))


async def _scrape_word_with_browser(word: str, browser) -> WordResult:  # type: ignore[no-untyped-def]
    url = BASE_URL + DICTIONARY_PATH + word
    html = await fetch_html(browser, url)
    entries = await parse_word_page(html, browser, BASE_URL)

    if not entries:
        raise WordNotFoundError(word, url)

    return WordResult(word=word, source_url=url, entries=entries)
