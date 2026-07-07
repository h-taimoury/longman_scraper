"""Downloads pronunciation audio files using an already-open Playwright page.

Plain HTTP clients — and even Playwright's own lightweight `page.request`
context — get blocked by ldoceonline.com's bot protection (confirmed: both
return a 403 from nginx, identical to a bare curl request). Only a real
browser page, with a genuine TLS/HTTP fingerprint and an already-established
session, gets through. So audio bytes are fetched by running `fetch()`
inside the JS engine of a page that has already loaded a dictionary entry,
rather than via any separate HTTP request or page navigation.
"""

from __future__ import annotations

import base64
import os

from playwright.async_api import Page

from .exceptions import AudioDownloadError

_FETCH_AND_ENCODE_JS = """async (url) => {
    const res = await fetch(url);
    if (!res.ok) {
        throw new Error('HTTP ' + res.status);
    }
    const buf = await res.arrayBuffer();
    const bytes = new Uint8Array(buf);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
}"""


async def download_audio(page: Page, url: str) -> bytes:
    """Fetch `url`'s bytes from inside `page`'s own JS context.

    Raises AudioDownloadError if the fetch fails or the response isn't ok.
    """
    try:
        encoded: str = await page.evaluate(_FETCH_AND_ENCODE_JS, url)
    except Exception as error:  # noqa: BLE001 - re-raised as a typed error
        raise AudioDownloadError(url, error) from error

    return base64.b64decode(encoded)


def save_audio(directory: str, filename: str, data: bytes) -> str:
    """Write `data` to `directory/filename`, creating the directory if needed.

    Returns the full path written to. Always overwrites (no skip-if-exists).
    """
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, "wb") as f:
        f.write(data)
    return path
