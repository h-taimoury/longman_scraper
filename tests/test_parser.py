"""Tests for parser.py using a local HTML fixture.

These tests never launch Playwright: the cross-reference fetch and audio
download/save are monkeypatched to avoid network/filesystem calls, and
everything else operates on static HTML.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from longman_scraper.parser import parse_word_page

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "book.html"
BASE_URL = "https://www.ldoceonline.com"


def _load_fixture() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


def _parse(html: str):
    return asyncio.run(
        parse_word_page(
            html,
            browser=None,
            page=None,
            base_url=BASE_URL,
            word="book",
            audio_dir="./test_audio_output",
        )
    )


@patch("longman_scraper.parsers.pronunciation.save_audio")
@patch("longman_scraper.parsers.pronunciation.download_audio", new_callable=AsyncMock)
@patch("longman_scraper.parser.fetch_cross_reference_sense", new_callable=AsyncMock)
def test_business_entries_are_excluded(
    mock_fetch_cross_ref, mock_download_audio, mock_save_audio
):
    mock_fetch_cross_ref.return_value = None
    mock_download_audio.return_value = b"fake-audio-bytes"
    html = _load_fixture()

    entries = _parse(html)

    assert len(entries) == 1
    assert entries[0].part_of_speech == "noun"
    assert all("ACCOUNT BOOKS" not in s.synonyms for s in entries[0].senses)


def test_basic_entry_fields(mock_fetch_cross_ref, mock_download_audio, mock_save_audio):
    mock_fetch_cross_ref.return_value = None
    mock_download_audio.return_value = b"fake-audio-bytes"
    html = _load_fixture()

    entries = _parse(html)
    entry = entries[0]

    assert entry.word == "book"
    assert entry.pronunciation.text == "/bʊk/"
    assert set(entry.frequency) == {"S1", "W1"}


def test_audio_files_named_without_pos_when_single_group(
    mock_fetch_cross_ref, mock_download_audio, mock_save_audio
):
    """book.html has one Head/PronCodes block for the only non-business
    dictentry, so there's exactly one pronunciation group -> plain filenames."""
    mock_fetch_cross_ref.return_value = None
    mock_download_audio.return_value = b"fake-audio-bytes"
    html = _load_fixture()

    entries = _parse(html)
    entry = entries[0]

    assert entry.pronunciation.br_audio == "book_Br.mp3"
    assert entry.pronunciation.am_audio == "book_Am.mp3"
    mock_save_audio.assert_any_call(
        "./test_audio_output", "book_Br.mp3", b"fake-audio-bytes"
    )
    mock_save_audio.assert_any_call(
        "./test_audio_output", "book_Am.mp3", b"fake-audio-bytes"
    )


@patch("longman_scraper.parsers.pronunciation.save_audio")
@patch("longman_scraper.parsers.pronunciation.download_audio", new_callable=AsyncMock)
@patch("longman_scraper.parser.fetch_cross_reference_sense", new_callable=AsyncMock)
def test_sense_titles_and_numbers(
    mock_fetch_cross_ref, mock_download_audio, mock_save_audio
):
    mock_fetch_cross_ref.return_value = None
    mock_download_audio.return_value = b"fake-audio-bytes"
    html = _load_fixture()

    entries = _parse(html)
    senses = entries[0].senses

    titles = [s.title for s in senses]
    assert "book_noun_1" in titles
    assert "book_noun_2" in titles
    assert len(senses) == 4  # senses 1, 2, 4, 5 (sense 3 dropped)


@patch("longman_scraper.parsers.pronunciation.save_audio")
@patch("longman_scraper.parsers.pronunciation.download_audio", new_callable=AsyncMock)
@patch("longman_scraper.parser.fetch_cross_reference_sense", new_callable=AsyncMock)
def test_gram_exa_and_collo_exa_examples(
    mock_fetch_cross_ref, mock_download_audio, mock_save_audio
):
    mock_fetch_cross_ref.return_value = None
    mock_download_audio.return_value = b"fake-audio-bytes"
    html = _load_fixture()

    entries = _parse(html)
    senses_by_title = {s.title: s for s in entries[0].senses}

    sense_1 = senses_by_title["book_noun_1"]
    usages = [e.usage for e in sense_1.examples if e.usage]
    assert any("book about/on" in u for u in usages)
    assert any(e.usage is None for e in sense_1.examples)

    sense_4 = senses_by_title["book_noun_4"]
    collocation_examples = [e for e in sense_4.examples if e.usage]
    assert collocation_examples
    assert "book a table" in collocation_examples[0].usage


@patch("longman_scraper.parsers.pronunciation.save_audio")
@patch("longman_scraper.parsers.pronunciation.download_audio", new_callable=AsyncMock)
@patch("longman_scraper.parser.fetch_cross_reference_sense", new_callable=AsyncMock)
def test_subsense_definitions_are_joined(
    mock_fetch_cross_ref, mock_download_audio, mock_save_audio
):
    mock_fetch_cross_ref.return_value = None
    mock_download_audio.return_value = b"fake-audio-bytes"
    html = _load_fixture()

    entries = _parse(html)
    senses_by_title = {s.title: s for s in entries[0].senses}

    sense_5 = senses_by_title["book_noun_5"]
    assert "a" in sense_5.definition
    assert "b" in sense_5.definition
    assert "first meaning" in sense_5.definition
    assert "second meaning" in sense_5.definition
    assert len(sense_5.examples) == 2


@patch("longman_scraper.parsers.pronunciation.save_audio")
@patch("longman_scraper.parsers.pronunciation.download_audio", new_callable=AsyncMock)
@patch("longman_scraper.parser.fetch_cross_reference_sense", new_callable=AsyncMock)
def test_cross_reference_sense_is_marked_when_resolved(
    mock_fetch_cross_ref, mock_download_audio, mock_save_audio
):
    from bs4 import BeautifulSoup

    resolved_html = (
        '<span class="Sense"><span class="DEF"> resolved definition</span>'
        '<span class="EXAMPLE"> resolved example</span></span>'
    )
    resolved_el = BeautifulSoup(resolved_html, "lxml").find("span", class_="Sense")
    mock_fetch_cross_ref.return_value = resolved_el
    mock_download_audio.return_value = b"fake-audio-bytes"

    html = _load_fixture()
    entries = _parse(html)
    senses = entries[0].senses

    assert len(senses) == 5
    cross_ref_senses = [s for s in senses if s.is_cross_reference]
    assert len(cross_ref_senses) == 1
    assert cross_ref_senses[0].definition == "resolved definition"
    assert cross_ref_senses[0].cross_reference_source_url == (
        BASE_URL + "/dictionary/books"
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
