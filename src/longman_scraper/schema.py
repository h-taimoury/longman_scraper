"""Structured data types returned by longman_scraper.

These are plain dataclasses with no framework dependency. Consumers (e.g. a
Django backend) are expected to map these onto their own models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ExampleKind = Literal["example", "collocation", "grammar_pattern"]


@dataclass
class Frequency:
    """One frequency band shown next to a head word, e.g. S1 / W1."""

    label: str
    """Short code, e.g. "S1"."""

    description: str
    """Human-readable meaning, e.g. "Top 1000 spoken words"."""


@dataclass
class Pronunciation:
    """British/American pronunciation info for a head word."""

    british: str | None = None
    """IPA pronunciation, e.g. "/bʊk/"."""

    american: str | None = None
    """IPA pronunciation if it differs from British; otherwise None."""

    british_audio_url: str | None = None
    american_audio_url: str | None = None


@dataclass
class Example:
    """A single example sentence, collocation, or grammar pattern."""

    kind: ExampleKind
    text: str


@dataclass
class Sense:
    """One dictionary sense (one distinct meaning) within an Entry."""

    sense_number: str | None
    """e.g. "1", "2"; None if the entry has only a single, unnumbered sense."""

    title: str
    """Stable identifier for this sense, e.g. "book_noun_2"."""

    definition: str

    lex_unit: str | None = None
    """e.g. "in my book" — the specific phrase this sense defines, if any."""

    geo: str | None = None
    """Regional label, e.g. "British English"."""

    register: str | None = None
    """e.g. "informal", "spoken"."""

    synonyms: list[str] = field(default_factory=list)
    opposites: list[str] = field(default_factory=list)
    examples: list[Example] = field(default_factory=list)

    is_cross_reference: bool = False
    """True if this sense was resolved by following a "→ see X" link."""

    cross_reference_source_url: str | None = None
    """The URL the sense was fetched from, if is_cross_reference is True."""


@dataclass
class Entry:
    """One dictionary entry: a single word + part-of-speech block.

    An entry groups together every Sense that shares the same head word,
    pronunciation, and part of speech (e.g. all the noun senses of "book").
    Business-dictionary entries are never represented here — they are
    excluded entirely during parsing.
    """

    word: str
    part_of_speech: str
    pronunciation: Pronunciation
    frequency: list[Frequency] = field(default_factory=list)
    inflections: str | None = None
    register: str | None = None
    senses: list[Sense] = field(default_factory=list)


@dataclass
class WordResult:
    """Top-level result of scraping a single word."""

    word: str
    source_url: str
    entries: list[Entry] = field(default_factory=list)
