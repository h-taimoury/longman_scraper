# longman_scraper

A standalone, framework-agnostic Python package that scrapes word entries from
the Longman Dictionary of Contemporary English (ldoceonline.com).

It has **no dependency on Django, Celery, or any web framework** — it only
scrapes a page with Playwright and parses it with BeautifulSoup, returning
plain dataclasses. Business-dictionary entries are always excluded; only the
general (and phrasal-verb) dictionary entries are returned.

## Install

From a sibling project's virtualenv (editable install, so local edits are
picked up immediately):

```bash
pip install -e ../longman_scraper
playwright install chromium
```

## Usage

```python
import asyncio
from longman_scraper import scrape_word, scrape_words

async def main():
    result = await scrape_word("head")
    for entry in result.entries:
        print(entry.word, entry.part_of_speech)
        for sense in entry.senses:
            print(" ", sense.title, "-", sense.definition)

    results = await scrape_words(["book", "freak"])
    print(results["book"].entries[0].word)

asyncio.run(main())
```

## Data shape

`scrape_word` returns a `WordResult`:

```
WordResult
├── word: str
├── source_url: str
└── entries: list[Entry]
    ├── word: str
    ├── part_of_speech: str
    ├── pronunciation: Pronunciation
    ├── frequency: list[FrequencyLabel]  # e.g. ["S1", "W3"]; one of S1/S2/S3/W1/W2/W3
    ├── inflections: str | None
    └── senses: list[Sense]
        ├── sense_number: str | None
        ├── title: str                  # e.g. "head_noun_2"
        ├── lex_unit: str | None
        ├── definition: str
        ├── geo: str | None
        ├── register: str | None
        ├── synonyms: list[str]
        ├── opposites: list[str]
        ├── examples: list[Example]
        ├── is_cross_reference: bool
        └── cross_reference_source_url: str | None
```

See `src/longman_scraper/schema.py` for the full dataclass definitions and
docstrings.

## Notes

- Business-dictionary entries (`bussdictEntry` blocks on the page) are never
  scraped or returned — this is hardcoded into entry detection in `parser.py`,
  not a configurable option.
- Cross-reference senses (e.g. "→ books") are resolved by fetching the target
  page and re-parsing it; the resulting sense is marked
  `is_cross_reference=True` with `cross_reference_source_url` set.
- `scrape_words` runs all words concurrently via `asyncio.gather`, sharing a
  single browser instance (mirrors the original Node scraper's behavior).
