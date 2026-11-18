"""
Helpers that make long reports fit within the AI provider's
token limits: remove lines repeated on every page and split
the text into chunks of whole pages.
"""

from collections import Counter

# Rough rule for English text: about 4 characters per token.
CHARS_PER_TOKEN = 4

# About 1,500 tokens of report text per chunk.
DEFAULT_CHUNK_CHARS = 6000

# Short repeated lines such as units ("g/dL") or results
# ("Negative") are real data, so only longer lines count
# as page furniture.
MIN_REPEATED_LINE_LENGTH = 20


def estimate_tokens(text: str) -> int:
    """
    Rough token count, good enough for sizing requests.
    """

    return len(text) // CHARS_PER_TOKEN


def strip_repeated_lines(pages: list[str]) -> list[str]:
    """
    Remove headers, footers, addresses and disclaimers that
    appear on at least half of the pages. The first copy of
    each repeated line is kept so its context is not lost.
    Reports with fewer than 3 pages are returned unchanged.
    """

    if len(pages) < 3:
        return pages

    counts = Counter()

    for page in pages:
        counts.update(
            {line.strip() for line in page.splitlines() if line.strip()}
        )

    limit = len(pages) / 2

    repeated = {
        line
        for line, count in counts.items()
        if count >= limit and len(line) >= MIN_REPEATED_LINE_LENGTH
    }

    seen = set()
    cleaned = []

    for page in pages:
        kept = []

        for line in page.splitlines():
            key = line.strip()

            if key in repeated:
                if key in seen:
                    continue
                seen.add(key)

            kept.append(line)

        cleaned.append("\n".join(kept))

    return cleaned


def _pack(pieces: list[str], max_chars: int) -> list[str]:
    """
    Join pieces in order into chunks of at most max_chars.
    A single piece longer than max_chars becomes its own chunk.
    """

    chunks = []
    current = []
    size = 0

    for piece in pieces:
        if current and size + len(piece) > max_chars:
            chunks.append("\n".join(current))
            current = []
            size = 0

        current.append(piece)
        size += len(piece) + 1

    if current:
        chunks.append("\n".join(current))

    return chunks


def split_into_chunks(
    pages: list[str],
    max_chars: int = DEFAULT_CHUNK_CHARS,
) -> list[str]:
    """
    Split the report into chunks of whole pages. A page that
    is too long on its own is split by lines.
    """

    pieces = []

    for page in pages:
        if len(page) > max_chars:
            pieces.extend(_pack(page.splitlines(), max_chars))
        else:
            pieces.append(page)

    return [
        chunk
        for chunk in _pack(pieces, max_chars)
        if chunk.strip()
    ]