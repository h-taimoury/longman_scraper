from __future__ import annotations

from bs4 import BeautifulSoup
from bs4.element import Tag
from playwright.async_api import Browser, Page

from .parsers import head, sense
from .parsers.crossref import fetch_cross_reference_sense
from .parsers.pronunciation import resolve_pronunciations
from .schema import Entry, Pronunciation, Sense

DICTENTRY_SELECTOR = "div.dictionary span.dictentry"


async def parse_word_page(
    html: str,
    browser: Browser,
    page: Page,
    base_url: str,
    word: str,
    audio_dir: str,
) -> list[Entry]:
    """Parse a word page's HTML into a list of non-business Entry objects.

    `page` must be the live Playwright page that loaded this HTML (audio
    downloads run inside its JS context). `word` is the originally-searched
    word, used as the base for audio filenames — not each entry's own
    parsed word text, which can differ (e.g. "Hello!" vs "hello").
    """
    soup = BeautifulSoup(html, "lxml")
    dictentry_els = soup.select(DICTENTRY_SELECTOR)
    non_business_els = [el for el in dictentry_els if not _is_business_entry(el)]

    pronunciations = await resolve_pronunciations(
        non_business_els, page, audio_dir, word
    )

    entries: list[Entry] = []
    for entry_el, pronunciation in zip(non_business_els, pronunciations):
        entry = await _parse_entry(entry_el, browser, base_url, pronunciation)
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
    pronunciation: Pronunciation | None,
) -> Entry | None:
    word = head.parse_word(entry_el)
    if not word:
        return None

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

    return entry


async def _resolve_sense(
    sense_el: Tag,
    browser: Browser,
    base_url: str,
    word: str,
    part_of_speech: str,
    index: int,
    has_multiple_senses: bool,
) -> Sense | None:
    target_sense_el = sense_el
    crossref_label: str | None = None

    if sense.is_cross_reference_only(sense_el):
        url = sense.crossref_target_url(sense_el, base_url)
        if url is None:
            return None
        crossref_label = sense.crossref_label(sense_el)
        print(f"  [crossref] following link to {url}", flush=True)
        resolved = await fetch_cross_reference_sense(browser, url)
        if resolved is None:
            return None
        target_sense_el = resolved

    title = sense.build_title(
        word, part_of_speech, index, has_multiple_senses=has_multiple_senses
    )

    return Sense(
        sense_number=sense.parse_sense_number(
            sense_el, has_multiple_senses=has_multiple_senses
        ),
        title=title,
        definition=sense.parse_definition(target_sense_el),
        lex_unit=crossref_label or sense.parse_lex_unit(target_sense_el),
        geo=sense.parse_geo(target_sense_el),
        register=sense.parse_sense_register(target_sense_el),
        synonyms=sense.parse_synonyms(target_sense_el),
        opposites=sense.parse_opposites(target_sense_el),
        examples=sense.parse_sense_examples(target_sense_el),
    )
