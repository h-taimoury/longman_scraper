"""Playwright browser/page lifecycle helpers.

This module owns all direct interaction with Playwright. Nothing outside this
file should import `playwright` directly, so the rest of the package only
ever deals with HTML strings.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from playwright.async_api import Browser, async_playwright

from .exceptions import PageLoadError
import time


BLOCKED_RESOURCE_TYPES = {"image", "stylesheet", "font", "media"}
DEFAULT_TIMEOUT_MS = 240_000


@asynccontextmanager
async def launch_browser(*, headless: bool = True) -> AsyncIterator[Browser]:
    """Launch a Chromium browser for the lifetime of the `async with` block.

    Example:
        async with launch_browser() as browser:
            html = await fetch_html(browser, "https://example.com")
    """
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headless)
        try:
            yield browser
        finally:
            await browser.close()


async def fetch_html(
    browser: Browser,
    url: str,
    *,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
) -> str:
    """Navigate to `url` in a fresh page and return the rendered HTML.

    Images, stylesheets, fonts, and media are blocked to speed up loading,
    since only the parsed DOM/text content is needed.
    """
    print(f"  [fetch] loading {url}", flush=True)
    start = time.monotonic()
    page = await browser.new_page()
    try:
        await page.route("**/*", _block_unnecessary_resources)
        await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
        html = await page.content()
        print(f"  [fetch] done in {time.monotonic() - start:.2f}s", flush=True)
        return html
    except Exception as error:  # noqa: BLE001 - re-raised as a typed error
        raise PageLoadError(url, error) from error
    finally:
        await page.close()


async def _block_unnecessary_resources(route) -> None:  # type: ignore[no-untyped-def]
    if route.request.resource_type in BLOCKED_RESOURCE_TYPES:
        await route.abort()
    else:
        await route.continue_()
