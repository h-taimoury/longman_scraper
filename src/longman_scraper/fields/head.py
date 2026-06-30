"""Parses entry-level fields found in the <span class="Head"> block.

These fields apply to an entire Entry (e.g. all senses of "book" as a noun)
rather than to an individual Sense.
"""

from __future__ import annotations

from bs4.element import Tag

from .._text import clean_text
from ..schema import Frequency, Pronunciation

BASE_AUDIO_HOST = "https://www.ldoceonline.com"


def parse_word(entry_el: Tag) -> str:
    """Extract the head word, e.g. "book". Falls back to phrasal-verb head."""
    hwd_el = entry_el.select_one("span.Head span.HWD")
    if hwd_el is not None:
        return clean_text(hwd_el.get_text())

    phrvb_el = entry_el.select_one(".PHRVBHWD")
    return clean_text(phrvb_el.get_text()) if phrvb_el else ""


def parse_part_of_speech(entry_el: Tag) -> str:
    pos_el = entry_el.select_one("span.Head span.POS")
    return clean_text(pos_el.get_text()) if pos_el else ""


def parse_inflections(entry_el: Tag) -> str | None:
    inflections_el = entry_el.select_one("span.Inflections")
    if inflections_el is None:
        return None
    text = clean_text(inflections_el.get_text())
    return text or None


def parse_register(entry_el: Tag) -> str | None:
    register_els = entry_el.select("span.Head span.REGISTERLAB")
    if not register_els:
        return None
    text = " ".join(clean_text(el.get_text()) for el in register_els)
    return text.strip() or None


def parse_frequency(entry_el: Tag) -> list[Frequency]:
    frequency: list[Frequency] = []
    for freq_el in entry_el.select("span.Head > span.FREQ"):
        label = clean_text(freq_el.get_text())
        description = freq_el.get("title", "")
        frequency.append(Frequency(label=label, description=description))
    return frequency


def parse_pronunciation(entry_el: Tag) -> Pronunciation | None:
    """Extract British/American IPA + audio URLs, if present on this entry.

    Some entries (later homonyms of the same word) omit pronunciation because
    it's identical to a previous entry's. In that case the caller should
    reuse the previously-seen Pronunciation, mirroring the original scraper's
    `sharedData.pronunciation` fallback.
    """
    pron_codes_el = entry_el.select_one("span.Head > span.PronCodes")
    if pron_codes_el is None:
        return None

    pronunciation = Pronunciation(british=clean_text(pron_codes_el.get_text()))

    british_audio_el = entry_el.select_one("span.Head span.brefile")
    if british_audio_el is not None:
        pronunciation.british_audio_url = british_audio_el.get("data-src-mp3")

    american_audio_el = entry_el.select_one("span.Head span.amefile")
    if american_audio_el is not None:
        pronunciation.american_audio_url = american_audio_el.get("data-src-mp3")

    return pronunciation
