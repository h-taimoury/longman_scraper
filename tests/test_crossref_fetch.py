"""Cross-reference transport tests, without network, audio files, or Django."""
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from longman_scraper.browser import fetch_html_in_page
from longman_scraper.exceptions import PageLoadError
from longman_scraper.parser import parse_word_page
from longman_scraper.parsers.crossref import fetch_cross_reference_sense

URL = "https://www.ldoceonline.com/dictionary/books"
HTML = '<div class="dictionary"><span class="dictentry"><span class="Sense"><span class="DEF">target definition</span></span></span></div>'


def test_fetch_uses_existing_page_without_navigation_or_close():
    page = MagicMock()
    page.evaluate = AsyncMock(return_value=HTML)
    assert asyncio.run(fetch_html_in_page(page, URL, timeout_ms=1234)) == HTML
    assert page.evaluate.call_args.args[1] == {"url": URL, "timeoutMs": 1234}
    page.goto.assert_not_called()
    page.close.assert_not_called()
    page.context.new_page.assert_not_called()


@pytest.mark.parametrize("message", ["HTTP 403", "HTTP 503", "AbortError", "Failed to fetch"])
def test_fetch_errors_preserve_url_and_cause_without_closing_page(message):
    page = MagicMock()
    error = RuntimeError(message)
    page.evaluate = AsyncMock(side_effect=error)
    with pytest.raises(PageLoadError) as caught:
        asyncio.run(fetch_html_in_page(page, URL))
    assert caught.value.url == URL
    assert caught.value.original_error is error
    assert caught.value.__cause__ is error
    page.close.assert_not_called()


def test_target_without_definition_still_returns_none():
    page = MagicMock()
    page.evaluate = AsyncMock(return_value='<div class="dictionary"></div>')
    assert asyncio.run(fetch_cross_reference_sense(page, URL)) is None


def test_parser_passes_original_word_page_to_crossref_transport():
    page = MagicMock()
    page.evaluate = AsyncMock(return_value=HTML)
    browser = MagicMock()
    fixture = Path(__file__).parent / "fixtures" / "book.html"
    with patch("longman_scraper.parser.resolve_pronunciations", new=AsyncMock(return_value=[None])):
        entries = asyncio.run(parse_word_page(
            fixture.read_text(encoding="utf-8"), browser, page,
            "https://www.ldoceonline.com", "book", "unused",
        ))
    resolved = next(s for s in entries[0].senses if s.definition == "target definition")
    assert resolved.title == "book_n_3"
    assert len(entries[0].senses) == 5
    assert page.evaluate.call_args.args[1]["url"] == URL
    browser.new_page.assert_not_called()
    page.goto.assert_not_called()
    page.close.assert_not_called()
