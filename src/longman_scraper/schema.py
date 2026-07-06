"""Structured data types returned by longman_scraper.

These are plain dataclasses with no framework dependency. Consumers (e.g. a
Django backend) are expected to map these onto their own models.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Example:
    """A single example sentence, optionally tied to a usage pattern
    (a grammar pattern or a collocation)."""

    text: str  # A single example sentence, e.g. for the word "go", a example text is "Let’s go home."
    usage: str | None = (
        None  # The usage pattern this example illustrates. It can be a grammer pattern or a collocation or None (for examples that don't have a grammer or collocation info), e.g. for the word "go", a grammer pattern is "go to" and a collocation is "go by bus/train/car etc".
    )


@dataclass
class Sense:
    """One dictionary sense (one distinct meaning) within an Entry."""

    sense_number: str | None
    """e.g. "1", "2"; None if the entry has only a single, unnumbered sense."""

    title: str
    """Stable identifier for this sense, e.g. "book_noun_2"."""

    definition: str

    lex_unit: str | None = None
    """sth like: "in advance (of something)" or "be obsessing about/over" — the specific phrase this sense defines, if any. In a sense, the lex unit comes right before definition as a bold text"""

    geo: str | None = None
    """Regional label, e.g. "British English"."""

    register: str | None = None
    """e.g. "informal", "spoken"."""

    synonyms: list[str] = field(default_factory=list)
    opposites: list[str] = field(default_factory=list)
    examples: list[Example] = field(default_factory=list)


@dataclass
class Entry:
    """One dictionary entry: a single part-of-speech block of a word.

    An entry groups together every Sense that shares the same head word,
    pronunciation, and part of speech (e.g. all the noun senses of "book").
    Business-dictionary entries are never represented here — they are
    excluded entirely during parsing.
    """

    word: str
    part_of_speech: str
    pronunciation: str | None
    frequency: list[str] = field(default_factory=list)
    inflections: str | None = None  # sth like: "(grabbed, grabbing)"
    register: str | None = None  # sth like: "spoken informal"
    senses: list[Sense] = field(default_factory=list)


@dataclass
class WordResult:
    """Top-level result of scraping a single word."""

    word: str
    entries: list[Entry] = field(default_factory=list)
