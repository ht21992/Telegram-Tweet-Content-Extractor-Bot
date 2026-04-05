from __future__ import annotations

import time
from typing import Any

import requests

from constants import ALLOWED_CHAT_TYPES, OFFSET_FILE, POLL_INTERVAL
from helpers import (
    chunk_text,
    extract_instagram_shortcodes,
    extract_tweet_ids,
    load_last_update_id,
    normalize_tweet_text,
    save_last_update_id,
)

from instagram_client import cleanup_file, download_instagram_media
from telegram_api import (
    get_me,
    get_updates,
    send_message,
    send_photo,
    send_video,
    send_photo_file,
    send_video_file,
    send_media_group_files,
    edit_message_text,
    send_chat_action,
    delete_message,
    send_media_group_urls,
)
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


def chunk_media_items(
    media_items: list[tuple[str, str]],
    chunk_size: int = 10,
) -> list[list[tuple[str, str]]]:
    return [
        media_items[i : i + chunk_size] for i in range(0, len(media_items), chunk_size)
    ]


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

    # -----------------------------
    # Instagram handling
    # -----------------------------
    instagram_codes = extract_instagram_shortcodes(text)
    seen_instagram_codes: set[str] = set()

    for shortcode in instagram_codes:
        if shortcode in seen_instagram_codes:
            continue
        seen_instagram_codes.add(shortcode)

        status_message_id: int | None = None
        media_items: list[tuple[str, str]] = []
        caption: str | None = None

        try:
            status_response = send_message(
                chat_id=chat_id,
                text="Processing Instagram link...",
                reply_to_message_id=message_id,
            )
            status_message_id = status_response["result"]["message_id"]

            edit_message_text(
                chat_id=chat_id,
                message_id=status_message_id,
                text="Downloading media...",
            )
            send_chat_action(chat_id, "upload_document")

            media_items, caption = download_instagram_media(shortcode)

            if not media_items:
                edit_message_text(
                    chat_id=chat_id,
                    message_id=status_message_id,
                    text="Could not fetch that Instagram media.",
                )
                continue

            edit_message_text(
                chat_id=chat_id,
                message_id=status_message_id,
                text="Preparing media...",
            )

            if len(media_items) == 1:
                media_type, media_path = media_items[0]

                if media_type == "photo":
                    send_chat_action(chat_id, "upload_photo")
                elif media_type == "video":
                    send_chat_action(chat_id, "upload_video")

                edit_message_text(
                    chat_id=chat_id,
                    message_id=status_message_id,
                    text="Sending media...",
                )

                if media_type == "photo":
                    send_photo_file(
                        chat_id=chat_id,
                        file_path=media_path,
                        reply_to_message_id=message_id,
                        caption=caption,
                    )
                elif media_type == "video":
                    send_video_file(
                        chat_id=chat_id,
                        file_path=media_path,
                        reply_to_message_id=message_id,
                        caption=caption,
                    )
                else:
                    edit_message_text(
                        chat_id=chat_id,
                        message_id=status_message_id,
                        text="Unsupported Instagram media type.",
                    )
                    continue

            else:
                edit_message_text(
                    chat_id=chat_id,
                    message_id=status_message_id,
                    text="Preparing album...",
                )

                media_chunks = chunk_media_items(media_items, chunk_size=10)

                for chunk_index, media_chunk in enumerate(media_chunks):
                    send_chat_action(chat_id, "upload_document")

                    send_media_group_files(
                        chat_id=chat_id,
                        media_items=media_chunk,
                        caption=caption if chunk_index == 0 else None,
                        reply_to_message_id=message_id if chunk_index == 0 else None,
                    )

                    if chunk_index < len(media_chunks) - 1:
                        edit_message_text(
                            chat_id=chat_id,
                            message_id=status_message_id,
                            text=f"Sending album part {chunk_index + 2}/{len(media_chunks)}...",
                        )

            try:
                delete_message(chat_id, status_message_id)
            except Exception:
                edit_message_text(
                    chat_id=chat_id,
                    message_id=status_message_id,
                    text="Done.",
                )

        except Exception as exc:
            print(f"Failed to fetch instagram media {shortcode}: {exc}")

            if status_message_id is not None:
                try:
                    edit_message_text(
                        chat_id=chat_id,
                        message_id=status_message_id,
                        text="Instagram media was found, but it could not be sent.",
                    )
                except Exception:
                    pass
            else:
                send_message(
                    chat_id=chat_id,
                    text="Instagram media was found, but it could not be sent.",
                    reply_to_message_id=message_id,
                )

        finally:
            for _, media_path in media_items:
                cleanup_file(media_path)

    # -----------------------------
    # X / Twitter handling
    # -----------------------------
    tweet_ids = extract_tweet_ids(text)
    seen_tweet_ids: set[str] = set()

    for tweet_id in tweet_ids:
        if tweet_id in seen_tweet_ids:
            continue
        seen_tweet_ids.add(tweet_id)

        status_message_id: int | None = None
        tweet = None
        photos: list[str] = []
        videos: list[str] = []

        try:
            status_response = send_message(
                chat_id=chat_id,
                text="Processing X link...",
                reply_to_message_id=message_id,
            )
            status_message_id = status_response["result"]["message_id"]

            edit_message_text(
                chat_id=chat_id,
                message_id=status_message_id,
                text="Fetching post content...",
            )

            send_chat_action(chat_id, "typing")

            result = get_tweet_payload(tweet_id=tweet_id, translate_to="fa")

            if isinstance(result, tuple):
                tweet = result[0]
                photos = result[1] if len(result) > 1 else []
                videos = result[2] if len(result) > 2 else []
            else:
                tweet = result
                photos = []
                videos = []

            if not tweet:
                edit_message_text(
                    chat_id=chat_id,
                    message_id=status_message_id,
                    text="Could not fetch that tweet text.",
                )
                continue

            reply_text = build_reply_text(tweet) or ""
            media_items: list[tuple[str, str]] = [("photo", url) for url in photos] + [
                ("video", url) for url in videos
            ]

            # ---------------------------------
            # No media -> send text only
            # ---------------------------------
            if not media_items:
                if reply_text:
                    edit_message_text(
                        chat_id=chat_id,
                        message_id=status_message_id,
                        text="Sending content...",
                    )

                    parts = chunk_text(reply_text)
                    for index, part in enumerate(parts):
                        send_message(
                            chat_id=chat_id,
                            text=part,
                            reply_to_message_id=message_id if index == 0 else None,
                        )

                    try:
                        delete_message(chat_id, status_message_id)
                    except Exception:
                        edit_message_text(
                            chat_id=chat_id,
                            message_id=status_message_id,
                            text="Done.",
                        )
                else:
                    edit_message_text(
                        chat_id=chat_id,
                        message_id=status_message_id,
                        text="Tweet content was empty.",
                    )
                continue

            # ---------------------------------
            # Exactly 1 media item
            # ---------------------------------
            if len(media_items) == 1:
                media_type, media_url = media_items[0]

                edit_message_text(
                    chat_id=chat_id,
                    message_id=status_message_id,
                    text="Preparing media...",
                )

                # If text fits Telegram caption limit, attach it to the media
                if reply_text and len(reply_text) <= 1024:
                    if media_type == "photo":
                        send_chat_action(chat_id, "upload_photo")
                        send_photo(
                            chat_id=chat_id,
                            photo_url=media_url,
                            reply_to_message_id=message_id,
                            caption=reply_text,
                        )
                    elif media_type == "video":
                        send_chat_action(chat_id, "upload_video")
                        send_video(
                            chat_id=chat_id,
                            video_url=media_url,
                            reply_to_message_id=message_id,
                            caption=reply_text,
                        )

                else:
                    # Send text first, then media
                    if reply_text:
                        edit_message_text(
                            chat_id=chat_id,
                            message_id=status_message_id,
                            text="Sending text...",
                        )

                        parts = chunk_text(reply_text)
                        for index, part in enumerate(parts):
                            send_message(
                                chat_id=chat_id,
                                text=part,
                                reply_to_message_id=message_id if index == 0 else None,
                            )

                    edit_message_text(
                        chat_id=chat_id,
                        message_id=status_message_id,
                        text="Sending media...",
                    )

                    if media_type == "photo":
                        send_chat_action(chat_id, "upload_photo")
                        send_photo(
                            chat_id=chat_id,
                            photo_url=media_url,
                            reply_to_message_id=None if reply_text else message_id,
                        )
                    elif media_type == "video":
                        send_chat_action(chat_id, "upload_video")
                        send_video(
                            chat_id=chat_id,
                            video_url=media_url,
                            reply_to_message_id=None if reply_text else message_id,
                        )

                try:
                    delete_message(chat_id, status_message_id)
                except Exception:
                    edit_message_text(
                        chat_id=chat_id,
                        message_id=status_message_id,
                        text="Done.",
                    )
                continue

            # ---------------------------------
            # 2+ media items -> send media group
            # ---------------------------------
            edit_message_text(
                chat_id=chat_id,
                message_id=status_message_id,
                text="Preparing media...",
            )

            if reply_text and len(reply_text) <= 1024:
                media_chunks = chunk_media_items(media_items, chunk_size=10)

                for chunk_index, media_chunk in enumerate(media_chunks):
                    send_chat_action(chat_id, "upload_document")
                    send_media_group_urls(
                        chat_id=chat_id,
                        media_items=media_chunk,
                        caption=reply_text if chunk_index == 0 else None,
                        reply_to_message_id=message_id if chunk_index == 0 else None,
                    )

            else:
                if reply_text:
                    edit_message_text(
                        chat_id=chat_id,
                        message_id=status_message_id,
                        text="Sending text...",
                    )

                    parts = chunk_text(reply_text)
                    for index, part in enumerate(parts):
                        send_message(
                            chat_id=chat_id,
                            text=part,
                            reply_to_message_id=message_id if index == 0 else None,
                        )

                edit_message_text(
                    chat_id=chat_id,
                    message_id=status_message_id,
                    text="Sending media...",
                )

                media_chunks = chunk_media_items(media_items, chunk_size=10)

                for chunk_index, media_chunk in enumerate(media_chunks):
                    send_chat_action(chat_id, "upload_document")
                    send_media_group_urls(
                        chat_id=chat_id,
                        media_items=media_chunk,
                        caption=None,
                        reply_to_message_id=message_id if chunk_index == 0 and not reply_text else None,
                    )

            try:
                delete_message(chat_id, status_message_id)
            except Exception:
                edit_message_text(
                    chat_id=chat_id,
                    message_id=status_message_id,
                    text="Done.",
                )

        except requests.RequestException as exc:
            print(f"Failed to fetch tweet {tweet_id}: {exc}")

            if status_message_id is not None:
                try:
                    edit_message_text(
                        chat_id=chat_id,
                        message_id=status_message_id,
                        text="Failed to process X link.",
                    )
                except Exception:
                    pass
            else:
                send_message(
                    chat_id=chat_id,
                    text="Failed to process X link.",
                    reply_to_message_id=message_id,
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
