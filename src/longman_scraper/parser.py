"""Top-level parsing: turns a word page's HTML into a list of Entry objects.

Business-dictionary entries are excluded unconditionally here — an entry
whose markup contains a "bussdictEntry" wrapper is never turned into an
Entry, full stop. There is no flag to opt back into them.
"""

from __future__ import annotations

from bs4 import BeautifulSoup
from bs4.element import Tag
from playwright.async_api import Browser

from .fields import head, sense
from .fields.crossref import fetch_cross_reference_sense
from .schema import Entry, Pronunciation, Sense

DICTENTRY_SELECTOR = "div.dictionary span.dictentry"


async def parse_word_page(html: str, browser: Browser, base_url: str) -> list[Entry]:
    """Parse a word page's HTML into a list of non-business Entry objects.
    Remember that an entry is a single part-of-speech block of a word, and that a word page may contain multiple entries (e.g. "book" has noun and verb entries).
    """
    soup = BeautifulSoup(html, "lxml")
    dictentry_els = soup.select(DICTENTRY_SELECTOR)

    shared_pronunciation: Pronunciation | None = None
    entries: list[Entry] = []

    for dictentry_el in dictentry_els:
        if _is_business_entry(dictentry_el):
            continue

        entry, shared_pronunciation = await _parse_entry(
            dictentry_el, browser, base_url, shared_pronunciation
        )
        if entry is not None:
            print(
                f"[entry] {entry.word} ({entry.part_of_speech}) - {len(entry.senses)} senses",
                flush=True,
            )
            entries.append(entry)

    return entries


def _is_business_entry(dictentry_el: Tag) -> bool:
    """A dictentry is a business-dictionary block if it wraps a bussdictEntry."""
    return dictentry_el.find(class_="bussdictEntry") is not None


async def _parse_entry(
    entry_el: Tag,
    browser: Browser,
    base_url: str,
    shared_pronunciation: Pronunciation | None,
) -> tuple[Entry | None, Pronunciation | None]:
    word = head.parse_word(entry_el)
    if not word:
        return None, shared_pronunciation

    pronunciation = head.parse_pronunciation(entry_el)
    if pronunciation is not None:
        shared_pronunciation = pronunciation
    else:
        pronunciation = shared_pronunciation or Pronunciation()

    part_of_speech = head.parse_part_of_speech(entry_el)

    entry = Entry(
        word=word,
        part_of_speech=part_of_speech,
        pronunciation=pronunciation,
        frequency=head.parse_frequency(entry_el),
        inflections=head.parse_inflections(entry_el),
        register=head.parse_register(entry_el),
    )

    sense_els = entry_el.select("span.Sense")
    has_multiple_senses = len(sense_els) > 1

    for index, sense_el in enumerate(sense_els, start=1):
        resolved_sense = await _resolve_sense(
            sense_el,
            browser,
            base_url,
            word,
            part_of_speech,
            index,
            has_multiple_senses,
        )
        if resolved_sense is not None:
            print(f"  [sense] {resolved_sense.title}", flush=True)
            entry.senses.append(resolved_sense)

    return entry, shared_pronunciation


async def _resolve_sense(
    sense_el: Tag,
    browser: Browser,
    base_url: str,
    word: str,
    part_of_speech: str,
    index: int,
    has_multiple_senses: bool,
) -> Sense | None:
    is_cross_reference = False
    cross_reference_source_url: str | None = None
    target_sense_el = sense_el

    if sense.is_cross_reference_only(sense_el):
        url = sense.crossref_target_url(sense_el, base_url)
        if url is None:
            return None
        print(f"  [crossref] following link to {url}", flush=True)
        resolved = await fetch_cross_reference_sense(browser, url)
        if resolved is None:
            return None
        target_sense_el = resolved
        is_cross_reference = True
        cross_reference_source_url = url

    title = sense.build_title(
        word, part_of_speech, index, has_multiple_senses=has_multiple_senses
    )

    return Sense(
        sense_number=sense.parse_sense_number(
            sense_el, has_multiple_senses=has_multiple_senses
        ),
        title=title,
        definition=sense.parse_definition(target_sense_el),
        lex_unit=sense.parse_lex_unit(target_sense_el),
        geo=sense.parse_geo(target_sense_el),
        register=sense.parse_sense_register(target_sense_el),
        synonyms=sense.parse_synonyms(target_sense_el),
        opposites=sense.parse_opposites(target_sense_el),
        examples=sense.parse_sense_examples(target_sense_el),
        is_cross_reference=is_cross_reference,
        cross_reference_source_url=cross_reference_source_url,
    )
