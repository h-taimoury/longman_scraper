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

    with open("words.json", "w", encoding="utf-8") as f:
        json.dump(
            [asdict(result) for result in results.values()],
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("Saved to words.json", flush=True)


asyncio.run(main())
