"""Playwright browser/page lifecycle helpers.

This module owns all direct interaction with Playwright. Nothing outside this
file should import `playwright` directly, so the rest of the package only
ever deals with HTML strings.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from playwright.async_api import Browser, async_playwright, Page

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


async def open_word_page(
    browser: Browser,
    url: str,
    *,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
) -> Page:
    """Navigate to `url` in a fresh page and return the live Page.

    Unlike `fetch_html`, the page is left open — audio downloads (see
    `audio.download_audio`) run `fetch()` inside this same page's JS
    context, and need the exact page/session that loaded the dictionary
    entry rather than a fresh one, to inherit the browser's fingerprint.

    The caller is responsible for closing the returned page.
    """
    print(f"  [fetch] loading {url}", flush=True)
    start = time.monotonic()
    page = await browser.new_page()
    try:
        await page.route("**/*", _block_unnecessary_resources)
        await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
        print(f"  [fetch] done in {time.monotonic() - start:.2f}s", flush=True)
        return page
    except Exception as error:  # noqa: BLE001 - re-raised as a typed error
        await page.close()
        raise PageLoadError(url, error) from error


async def fetch_html(
    browser: Browser,
    url: str,
    *,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
) -> str:
    """Navigate to `url` and return the rendered HTML, closing the page after.

    Used by the cross-reference resolver, which only needs HTML and has no
    further use for the page (no audio to download from a cross-ref target).
    """
    page = await open_word_page(browser, url, timeout_ms=timeout_ms)
    try:
        return await page.content()
    finally:
        await page.close()


async def _block_unnecessary_resources(route) -> None:  # type: ignore[no-untyped-def]
    if route.request.resource_type in BLOCKED_RESOURCE_TYPES:
        await route.abort()
    else:
        await route.continue_()
