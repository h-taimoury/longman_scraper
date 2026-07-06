"""Parses EXAMPLE, GramExa, and ColloExa elements into Example objects.

Mirrors the structure of the source HTML, where a sense (or subsense) can
contain direct <span class="EXAMPLE"> children, as well as <span
class="GramExa"> (a grammar pattern followed by examples) and <span
class="ColloExa"> (a collocation followed by examples).
"""

from __future__ import annotations

from bs4.element import Tag

from .._text import clean_text
from ..schema import Example


def parse_examples(container: Tag) -> list[Example]:
    """Extract every Example found directly under `container`, preserving the
    order in which they appear in the source HTML.

    `container` is expected to be a Sense or Subsense element. Only direct
    children are inspected (matching the original site's nesting), so
    examples belonging to a *different* sense are never picked up.
    """
    examples: list[Example] = []

    for child in container.find_all("span", recursive=False):
        classes = child.get("class") or []

        if "EXAMPLE" in classes:
            examples.append(_build_example(child))
        elif "GramExa" in classes:
            examples.extend(_parse_gram_exa(child))
        elif "ColloExa" in classes:
            examples.extend(_parse_collo_exa(child))

    return examples


def _build_example(example_el: Tag, usage: str | None = None) -> Example:
    return Example(text=clean_text(example_el.get_text()), usage=usage)


def _parse_gram_exa(gram_exa_el: Tag) -> list[Example]:
    pattern_el = gram_exa_el.find("span", class_="PROPFORMPREP", recursive=False) or (
        gram_exa_el.find("span", class_="PROPFORM", recursive=False)
    )
    gloss_el = gram_exa_el.find("span", class_="GLOSS", recursive=False)

    pattern_text = pattern_el.get_text() if pattern_el else ""
    gloss_text = gloss_el.get_text() if gloss_el else ""
    usage = clean_text(pattern_text + gloss_text) or None

    return [
        _build_example(example_el, usage=usage)
        for example_el in gram_exa_el.find_all(
            "span", class_="EXAMPLE", recursive=False
        )
    ]


def _parse_collo_exa(collo_exa_el: Tag) -> list[Example]:
    collo_el = collo_exa_el.find("span", class_="COLLO", recursive=False)
    gloss_el = collo_exa_el.find("span", class_="GLOSS", recursive=False)

    collo_text = collo_el.get_text() if collo_el else ""
    gloss_text = gloss_el.get_text() if gloss_el else ""
    usage = clean_text(collo_text + gloss_text) or None

    return [
        _build_example(example_el, usage=usage)
        for example_el in collo_exa_el.find_all(
            "span", class_="EXAMPLE", recursive=False
        )
    ]
