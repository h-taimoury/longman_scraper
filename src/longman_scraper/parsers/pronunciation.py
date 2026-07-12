"""Resolves pronunciation across all non-business entries of a word,
including downloading British/American audio files.

An entry's phonetics can be omitted from the markup when identical to a
neighboring entry's. Two cases show up on real pages:

- Trailing: an entry that comes *after* one with its own phonetics, and
  omits its own, shares that preceding entry's audio (e.g. several homonym
  entries of "book" that only show pronunciation once).
- Leading: entries that appear *before* any entry with phonetics at all
  (e.g. "Hello!" the magazine, which precedes "hello" the interjection)
  have no preceding entry to inherit from, so they borrow the *next*
  entry that does have its own phonetics.

Concretely: entries are grouped so that a new group starts at every entry
with its own phonetics, and entries without their own phonetics join the
current group — except for a leading run before the first phonetic entry,
which all attach to that first phonetic entry's group instead.

Audio is downloaded exactly once per group. If the word has only one
pronunciation group overall, files are named "{word}_Br.mp3" /
"{word}_Am.mp3"; if there are multiple groups, each is named
"{word}_{part_of_speech}_Br.mp3" / "{word}_{part_of_speech}_Am.mp3", using
the part of speech of the entry that owns that group's phonetics.
"""

from __future__ import annotations

import re

from bs4.element import Tag
from playwright.async_api import Page

from . import head
from ..audio import download_audio, save_audio
from ..schema import Pronunciation

_WHITESPACE = re.compile(r"\s+")


async def resolve_pronunciations(
    entry_els: list[Tag],
    page: Page,
    audio_dir: str,
    word: str,
) -> list[Pronunciation | None]:
    """Return a Pronunciation per entry in `entry_els` (same order, same
    length), downloading each group's audio exactly once.

    Returns all-None if no entry has its own phonetics at all (nothing to
    resolve or download in that case).
    """
    if not entry_els:
        return []

    own_flags = [head.has_own_pronunciation(el) for el in entry_els]

    if not any(own_flags):
        return [None] * len(entry_els)

    first_phonetic_idx = own_flags.index(True)
    group_indices = _assign_group_indices(own_flags, first_phonetic_idx)
    num_groups = max(group_indices) + 1

    resolved: dict[int, Pronunciation] = {}
    for group_idx in range(num_groups):
        owner_idx = next(
            i
            for i in range(first_phonetic_idx, len(entry_els))
            if group_indices[i] == group_idx and own_flags[i]
        )
        resolved[group_idx] = await _build_pronunciation(
            entry_els[owner_idx],
            page,
            audio_dir,
            word,
            is_only_group=num_groups == 1,
        )

    return [resolved[group_indices[i]] for i in range(len(entry_els))]


def _assign_group_indices(own_flags: list[bool], first_phonetic_idx: int) -> list[int]:
    """Entries before `first_phonetic_idx` join group 0 (borrowing forward);
    from `first_phonetic_idx` onward, a new group starts at every entry with
    its own phonetics."""
    # Consider this example: own_flags = [False, False, True, True, False, False]

    group_indices = [0] * len(own_flags)  # group_indices = [0, 0, 0, 0, 0, 0]
    current_group = 0
    for i in range(first_phonetic_idx + 1, len(own_flags)):
        if own_flags[i]:
            current_group += 1
        group_indices[i] = current_group
    return group_indices  # group_indices = [0, 0, 0, 1, 1, 1]


async def _build_pronunciation(
    owner_el: Tag,
    page: Page,
    audio_dir: str,
    word: str,
    *,
    is_only_group: bool,
) -> Pronunciation:
    pronunciation_text = head.parse_pronunciation(owner_el)
    br_url, am_url = head.parse_audio_urls(owner_el)

    if is_only_group:
        base_name = word
    else:
        pos = head.parse_part_of_speech(owner_el)
        base_name = f"{word}_{_sanitize(pos)}" if pos else word

    br_filename = f"{base_name}_Br.mp3" if br_url else None
    am_filename = f"{base_name}_Am.mp3" if am_url else None

    if br_url and br_filename:
        data = await download_audio(page, br_url)
        save_audio(audio_dir, br_filename, data)
    if am_url and am_filename:
        data = await download_audio(page, am_url)
        save_audio(audio_dir, am_filename, data)

    return Pronunciation(
        text=pronunciation_text,
        br_audio=br_filename,
        am_audio=am_filename,
    )


def _sanitize(text: str) -> str:
    """Make a part-of-speech label filename-safe, e.g. "phrasal verb" ->
    "phrasal_verb"."""
    return _WHITESPACE.sub("_", text.strip())
