"""longman_scraper: async scraper for ldoceonline.com.

Public API:
    scrape_word(word: str) -> WordResult
    scrape_words(words: list[str]) -> dict[str, WordResult]

Business-dictionary entries are always excluded.
"""

from .api import scrape_word, scrape_words
from .exceptions import PageLoadError, ScrapeError, WordNotFoundError
from .schema import Entry, Example, Frequency, Pronunciation, Sense, WordResult

__all__ = [
    "scrape_word",
    "scrape_words",
    "WordResult",
    "Entry",
    "Sense",
    "Example",
    "Frequency",
    "Pronunciation",
    "ScrapeError",
    "WordNotFoundError",
    "PageLoadError",
]
