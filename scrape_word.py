import asyncio
import json
import logging
from dataclasses import asdict

logging.basicConfig(level=logging.DEBUG)

from longman_scraper import scrape_word


async def main():
    print("Starting scrape...", flush=True)
    result = await scrape_word("hello")
    print("Done:", result.word, len(result.entries), "entries", flush=True)

    with open("word.json", "w", encoding="utf-8") as f:
        json.dump(asdict(result), f, indent=2, ensure_ascii=False)

    print("Saved to word.json", flush=True)


asyncio.run(main())
