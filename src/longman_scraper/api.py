"""Public entrypoints for longman_scraper."""

from __future__ import annotations

import asyncio

from .browser import launch_browser, open_word_page
from .exceptions import WordNotFoundError
from .parser import parse_word_page
from .schema import WordResult

BASE_URL = "https://www.ldoceonline.com"
DICTIONARY_PATH = "/dictionary/"
DEFAULT_AUDIO_DIR = "./pronunciation_audios"


async def scrape_word(word: str, audio_dir: str = DEFAULT_AUDIO_DIR) -> WordResult:
    """Scrape a single word from ldoceonline.com, downloading its British
    and American pronunciation audio into `audio_dir` along the way.

    Launches and tears down its own browser instance. For scraping many
    words, prefer `scrape_words`, which shares one browser across all of
    them.

    Raises:
        WordNotFoundError: if the page loads but has no dictionary entries.
        PageLoadError: if the page fails to load.
        AudioDownloadError: if a pronunciation audio file fails to download.
    """
    async with launch_browser() as browser:
        return await _scrape_word_with_browser(word, browser, audio_dir)


async def scrape_words(
    words: list[str], audio_dir: str = DEFAULT_AUDIO_DIR
) -> dict[str, WordResult]:
    """Scrape multiple words concurrently, sharing a single browser instance.

    All words' audio files are saved into the same `audio_dir`.

    Returns a dict keyed by the original word string. If scraping a word
    raises, that exception propagates.
    """
    async with launch_browser() as browser:
        results = await asyncio.gather(
            *(_scrape_word_with_browser(word, browser, audio_dir) for word in words)
        )
    return dict(zip(words, results))


async def _scrape_word_with_browser(word: str, browser, audio_dir: str) -> WordResult:  # type: ignore[no-untyped-def]
    url = BASE_URL + DICTIONARY_PATH + word
    page = await open_word_page(browser, url)
    try:
        html = await page.content()
        entries = await parse_word_page(html, browser, page, BASE_URL, word, audio_dir)
    finally:
        await page.close()

    if not entries:
        raise WordNotFoundError(word, url)

    return WordResult(word=word, entries=entries)
