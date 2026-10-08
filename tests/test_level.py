from bs4 import BeautifulSoup
from longman_scraper.parsers.head import parse_level
from longman_scraper.schema import Entry
from dataclasses import asdict


def test_level_is_scoped_to_each_entry_header():
    soup = BeautifulSoup("""
      <span class="dictentry"><span class="Head">
        <span class="tooltip LEVEL" title=" Core vocabulary: High-frequency "> ●●● </span>
      </span></span>
      <span class="dictentry"><span class="Head">
        <span class="tooltip LEVEL" title="Core vocabulary: Medium-frequency">●●○</span>
      </span></span>
      <span class="dictentry"><span class="Head"></span>
        <span class="Sense"><span class="tooltip LEVEL" title="wrong">●○○</span></span>
      </span>
    """, "html.parser")
    entries = soup.select(".dictentry")
    assert parse_level(entries[0]) == {"tooltip": "Core vocabulary: High-frequency", "indicator": "●●●"}
    assert parse_level(entries[1]) == {"tooltip": "Core vocabulary: Medium-frequency", "indicator": "●●○"}
    assert parse_level(entries[2]) is None


def test_missing_or_incomplete_level_is_none():
    for html in ('<span class="Head"></span>', '<span class="Head"><span class="tooltip LEVEL">●○○</span></span>'):
        assert parse_level(BeautifulSoup(html, "html.parser")) is None


def test_level_serializes_as_dictionary():
    level = {"tooltip": "Core vocabulary: Low-frequency", "indicator": "●○○"}
    entry = Entry(word="test", part_of_speech="noun", pronunciation=None, level=level)
    assert asdict(entry)["level"] == level
    assert Entry(word="test", part_of_speech="noun", pronunciation=None).level is None
