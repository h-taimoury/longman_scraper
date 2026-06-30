"""Small text-cleaning utility shared across field parsers."""

from __future__ import annotations

import re

_WHITESPACE_RUN = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """Collapse runs of whitespace/newlines into single spaces and trim."""
    return _WHITESPACE_RUN.sub(" ", text).strip()
