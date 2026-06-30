"""Custom exceptions raised by longman_scraper."""

from __future__ import annotations


class ScrapeError(Exception):
    """Base class for all errors raised by this package."""


class WordNotFoundError(ScrapeError):
    """Raised when the requested word has no dictionary entries on the page."""

    def __init__(self, word: str, url: str) -> None:
        self.word = word
        self.url = url
        super().__init__(f"No dictionary entries found for {word!r} at {url}")


class PageLoadError(ScrapeError):
    """Raised when a page fails to load (network error, timeout, etc.)."""

    def __init__(self, url: str, original_error: Exception) -> None:
        self.url = url
        self.original_error = original_error
        super().__init__(f"Failed to load {url}: {original_error}")
