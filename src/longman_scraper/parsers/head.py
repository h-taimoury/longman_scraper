"""Parses entry-level fields found in the <span class="Head"> block.

These fields apply to an entire Entry (e.g. all senses of "book" as a noun)
rather than to an individual Sense.
"""

from __future__ import annotations

from bs4.element import Tag

from .._text import clean_text

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
    """sth like: (grabbed, grabbing)"""
    inflections_el = entry_el.select_one("span.Inflections")
    if inflections_el is None:
        return None
    text = clean_text(inflections_el.get_text())
    return text or None


def parse_register(entry_el: Tag) -> str | None:
    """sth like: 'spoken informal'
    Note that there are two kinds of registers: the one in the Head block (this function extracts it) and the one in each Sense block. The Head-level register applies to all senses of this entry, while the Sense-level register applies only to that sense. Pay attention to 'span.Head span.REGISTERLAB' that means we are looking for the register of the whole entry under the Head block. Note that the Head block contains the entry level information."""
    register_els = entry_el.select("span.Head span.REGISTERLAB")
    if not register_els:
        return None
    text = " ".join(clean_text(el.get_text()) for el in register_els)
    return text.strip() or None


def parse_frequency(entry_el: Tag) -> list[str]:
    """This function takes an entry element and returns a list of frequency bands like ["S1,"W2"]"""
    return [
        clean_text(freq_el.get_text())
        for freq_el in entry_el.select("span.Head > span.FREQ")
    ]


def parse_pronunciation(entry_el: Tag) -> str | None:
    """Extract the pronunciation text (British + American if shown), if present.

    Some entries (later homonyms of the same word) omit pronunciation because
    it's identical to a previous entry's; the caller falls back to the
    previously-seen value in that case.
    """
    pron_codes_el = entry_el.select_one("span.Head > span.PronCodes")
    if pron_codes_el is None:
        return None
    return clean_text(pron_codes_el.get_text()) or None


def has_own_pronunciation(entry_el: Tag) -> bool:
    """True if this entry has its own PronCodes block (not inherited from
    a neighboring entry)."""
    return entry_el.select_one("span.Head > span.PronCodes") is not None


def parse_audio_urls(entry_el: Tag) -> tuple[str | None, str | None]:
    """Extract (british_audio_url, american_audio_url) from the speaker
    icons in the Head block. Returns (None, None) if absent."""
    bre_el = entry_el.select_one("span.Head span.speaker.brefile")
    ame_el = entry_el.select_one("span.Head span.speaker.amefile")
    british_url = bre_el.get("data-src-mp3") if bre_el else None
    american_url = ame_el.get("data-src-mp3") if ame_el else None
    return british_url, american_url
