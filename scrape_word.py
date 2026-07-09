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
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))


asyncio.run(main())
