"""Parses sense-level fields: definition, synonyms, opposites, geo, etc.

A "sense" here is already resolved — if the original sense was a
cross-reference, the caller (parser.py / fields/crossref.py) is expected to
have substituted the *target* page's sense element before these functions
ever see it. These functions only deal with extracting fields from a sense
element that actually has a definition.
"""

from __future__ import annotations

from bs4.element import Tag

from .._text import clean_text
from .examples import parse_examples
from ..schema import Example


def parse_sense_number(sense_el: Tag, *, has_multiple_senses: bool) -> str | None:
    if not has_multiple_senses:
        return None
    sensenum_el = sense_el.find("span", class_="sensenum", recursive=False)
    if sensenum_el is None:
        return None
    text = clean_text(sensenum_el.get_text())
    return text or None


def build_title(
    word: str, part_of_speech: str, index: int, *, has_multiple_senses: bool
) -> str:
    """Build a stable identifier like "book_noun_2", matching the admin UI."""
    if not has_multiple_senses:
        return word
    if part_of_speech == "phrasal verb":
        return f"{word}_{index}"
    return f"{word}_{part_of_speech}_{index}"


def parse_lex_unit(sense_el: Tag) -> str | None:
    """lex unit is sth like "in advance (of something)" or "be obsessing about/over" — the specific phrase this sense defines, if any"""
    lex_unit_el = sense_el.find("span", class_="LEXUNIT", recursive=False)
    if lex_unit_el is None:
        return None
    text = clean_text(lex_unit_el.get_text())
    return text or None


def parse_geo(sense_el: Tag) -> str | None:
    geo_el = sense_el.find("span", class_="GEO")
    if geo_el is None:
        return None
    text = clean_text(geo_el.get_text())
    return text or None


def parse_sense_register(sense_el: Tag) -> str | None:
    register_el = sense_el.find("span", class_="REGISTERLAB")
    if register_el is None:
        return None
    text = clean_text(register_el.get_text())
    return text or None


def parse_definition(sense_el: Tag) -> str:
    """Build the definition text, joining subsenses (a, b, c...) if present."""
    subsense_els = sense_el.find_all("span", class_="Subsense", recursive=False)
    if subsense_els:
        parts: list[str] = []
        for subsense_el in subsense_els:
            sub_number_el = subsense_el.find("span", class_="sensenum", recursive=False)
            def_el = subsense_el.find("span", class_="DEF", recursive=False)
            number_text = clean_text(sub_number_el.get_text()) if sub_number_el else ""
            def_text = def_el.get_text() if def_el else ""
            parts.append(clean_text(f"{number_text} {def_text}"))
        return clean_text(" ".join(parts))

    def_el = sense_el.find("span", class_="DEF", recursive=False)
    return clean_text(def_el.get_text()) if def_el else ""


def parse_synonyms(sense_el: Tag) -> list[str]:
    return [
        clean_text(el.get_text().replace("SYN", "", 1).replace(",", ""))
        for el in sense_el.find_all("span", class_="SYN")
    ]


def parse_opposites(sense_el: Tag) -> list[str]:
    return [
        clean_text(el.get_text().replace("OPP", "", 1).replace(",", ""))
        for el in sense_el.find_all("span", class_="OPP")
    ]


def parse_sense_examples(sense_el: Tag) -> list[Example]:
    """Collect examples from each Subsense if present, else from the sense itself."""
    subsense_els = sense_el.find_all("span", class_="Subsense", recursive=False)
    if subsense_els:
        examples: list[Example] = []
        for subsense_el in subsense_els:
            examples.extend(parse_examples(subsense_el))
        return examples
    return parse_examples(sense_el)


def has_definition(sense_el: Tag) -> bool:
    """A sense with no DEF and no Subsense is a pure cross-reference stub."""
    return bool(
        sense_el.find("span", class_="DEF", recursive=False)
        or sense_el.find("span", class_="Subsense", recursive=False)
    )


def is_cross_reference_only(sense_el: Tag) -> bool:
    """True if this sense element is just a "→ see X" pointer with no DEF."""
    has_crossref = sense_el.find("span", class_="Crossref", recursive=False) is not None
    return has_crossref and not has_definition(sense_el)


def crossref_target_url(sense_el: Tag, base_url: str) -> str | None:
    link_el = sense_el.select_one("span.Crossref a.crossRef")
    if link_el is None:
        return None
    href = link_el.get("href")
    if not href:
        return None
    return base_url.rstrip("/") + href
