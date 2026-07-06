"""longman_scraper: async scraper for ldoceonline.com.

Public API:
    scrape_word(word: str) -> WordResult
    scrape_words(words: list[str]) -> dict[str, WordResult]

"""

from .api import scrape_word, scrape_words
from .exceptions import PageLoadError, ScrapeError, WordNotFoundError
from .schema import Entry, Example, Sense, WordResult

__all__ = [
    "scrape_word",
    "scrape_words",
    "WordResult",
    "Entry",
    "Sense",
    "Example",
    "ScrapeError",
    "WordNotFoundError",
    "PageLoadError",
]
