import asyncio
import json
import logging
from dataclasses import asdict

logging.basicConfig(level=logging.DEBUG)

from longman_scraper import scrape_words

WORDS = ["book", "separate", "drive"]


async def main():
    print(f"Starting scrape for {len(WORDS)} words...", flush=True)
    results = await scrape_words(WORDS)

    for word, result in results.items():
        print(f"Done: {word} - {len(result.entries)} entries", flush=True)

    print(
        json.dumps(
            {word: asdict(result) for word, result in results.items()},
            indent=2,
            ensure_ascii=False,
        )
    )


asyncio.run(main())
