from __future__ import annotations

import time
from typing import Any

import requests

from constants import ALLOWED_CHAT_TYPES, OFFSET_FILE, POLL_INTERVAL
from helpers import (
    chunk_text,
    extract_tweet_ids,
    load_last_update_id,
    normalize_tweet_text,
    save_last_update_id,
)
from telegram_api import get_me, get_updates, send_message
from x_client import get_tweet_payload


def get_message_text(message: dict[str, Any]) -> str:
    return (message.get("text") or message.get("caption") or "").strip()


def should_process_chat(chat_type: str | None) -> bool:
    return chat_type in ALLOWED_CHAT_TYPES


def build_reply_text(tweet: dict[str, Any]) -> str | None:
    original_text = normalize_tweet_text(tweet.get("text") or "")
    if not original_text:
        return None

    lang = (tweet.get("lang") or "").strip().lower()
    translation = tweet.get("translation") or {}

    translated_text = ""
    if isinstance(translation, dict):
        translated_text = normalize_tweet_text(translation.get("text") or "")

    if lang == "fa" or not translated_text:
        return original_text

    return f"Original:\n\n{original_text}\n\nترجمه فارسی:\n\n{translated_text}"


def process_message(message: dict[str, Any]) -> None:
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    chat_type = chat.get("type")
    message_id = message.get("message_id")

    if not isinstance(chat_id, int):
        return

    if not should_process_chat(chat_type):
        return

    text = get_message_text(message)
    if not text:
        return

    tweet_ids = extract_tweet_ids(text)
    if not tweet_ids:
        return

    seen_ids: set[str] = set()

    for tweet_id in tweet_ids:
        if tweet_id in seen_ids:
            continue
        seen_ids.add(tweet_id)

        try:
            tweet = get_tweet_payload(tweet_id=tweet_id, translate_to="fa")
        except requests.RequestException as exc:
            print(f"Failed to fetch tweet {tweet_id}: {exc}")
            tweet = None

        if not tweet:
            send_message(
                chat_id=chat_id,
                text="Could not fetch that tweet text.",
                reply_to_message_id=message_id,
            )
            continue

        reply_text = build_reply_text(tweet)
        if not reply_text:
            send_message(
                chat_id=chat_id,
                text="Tweet text was empty.",
                reply_to_message_id=message_id,
            )
            continue

        parts = chunk_text(reply_text)

        for index, part in enumerate(parts):
            send_message(
                chat_id=chat_id,
                text=part,
                reply_to_message_id=message_id if index == 0 else None,
            )


def process_update(update: dict[str, Any]) -> None:
    message = update.get("message") or update.get("edited_message")
    if message:
        process_message(message)


def main() -> None:
    me = get_me()
    print(f"Bot is running as @{me.get('username', 'unknown')}")

    last_update_id = load_last_update_id(OFFSET_FILE)

    while True:
        try:
            updates = get_updates(last_update_id)

            for update in updates:
                update_id = update["update_id"]
                print(f"Processing update_id={update_id}")

                process_update(update)

                last_update_id = update_id + 1
                save_last_update_id(OFFSET_FILE, last_update_id)

        except requests.RequestException as exc:
            print(f"Network error: {exc}")
            time.sleep(3)
        except Exception as exc:
            print(f"Unexpected error: {exc}")
            time.sleep(3)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
