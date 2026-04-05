from __future__ import annotations

import re

from constants import MAX_MESSAGE_LENGTH


TWEET_LINK_RE = re.compile(
    r"https?://(?:www\.)?(?:x\.com|twitter\.com)/[A-Za-z0-9_]+/status/(\d+)(?:\?[^\s]*)?",
    re.IGNORECASE,
)

INSTAGRAM_LINK_RE = re.compile(
    r"https?://(?:www\.)?instagram\.com/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)",
    re.IGNORECASE,
)


def extract_instagram_shortcodes(text: str) -> list[str]:
    if not text:
        return []
    return INSTAGRAM_LINK_RE.findall(text)


def extract_tweet_ids(text: str) -> list[str]:
    if not text:
        return []
    return TWEET_LINK_RE.findall(text)


def normalize_tweet_text(text: str) -> str:
    if not text:
        return ""
    return text.strip()


def chunk_text(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> list[str]:
    text = text.strip()
    if not text:
        return []

    if len(text) <= max_length:
        return [text]

    chunks: list[str] = []
    current = ""

    for line in text.splitlines(keepends=True):
        if len(current) + len(line) <= max_length:
            current += line
            continue

        if current:
            chunks.append(current.rstrip())
            current = ""

        while len(line) > max_length:
            chunks.append(line[:max_length].rstrip())
            line = line[max_length:]

        current = line

    if current:
        chunks.append(current.rstrip())

    return chunks


def load_last_update_id(path: str) -> int | None:
    try:
        with open(path, "r", encoding="utf-8") as file:
            value = file.read().strip()
            if not value:
                return None
            return int(value)
    except (FileNotFoundError, ValueError):
        return None


def save_last_update_id(path: str, update_id: int) -> None:
    with open(path, "w", encoding="utf-8") as file:
        file.write(str(update_id))
