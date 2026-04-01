from __future__ import annotations

from typing import Any

import requests

from constants import LONG_POLL_TIMEOUT, REQUEST_TIMEOUT, TELEGRAM_API_BASE


def get_updates(offset: int | None = None) -> list[dict[str, Any]]:
    params: dict[str, Any] = {
        "timeout": LONG_POLL_TIMEOUT,
    }

    if offset is not None:
        params["offset"] = offset

    response = requests.get(
        f"{TELEGRAM_API_BASE}/getUpdates",
        params=params,
        timeout=LONG_POLL_TIMEOUT + 5,
    )
    response.raise_for_status()

    data = response.json()
    if not data.get("ok"):
        return []

    return data.get("result", [])


def send_message(
    chat_id: int,
    text: str,
    reply_to_message_id: int | None = None,
    disable_web_page_preview: bool = True,
) -> None:
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": disable_web_page_preview,
    }

    if reply_to_message_id is not None:
        payload["reply_to_message_id"] = reply_to_message_id

    response = requests.post(
        f"{TELEGRAM_API_BASE}/sendMessage",
        data=payload,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def get_me() -> dict[str, Any]:
    response = requests.get(
        f"{TELEGRAM_API_BASE}/getMe",
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"getMe failed: {data}")

    return data.get("result", {})


def send_photo(
    chat_id: int,
    photo_url: str,
    caption: str | None = None,
    reply_to_message_id: int | None = None,
) -> None:
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "photo": photo_url,
    }

    if not photo_url:
        print("Skipping: Photo URL is empty")
        return

    if caption:
        payload["caption"] = caption

    if reply_to_message_id is not None:
        payload["reply_to_message_id"] = reply_to_message_id

    response = requests.post(
        f"{TELEGRAM_API_BASE}/sendPhoto",
        data=payload,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def send_video(
    chat_id: int,
    video_url: str,
    caption: str | None = None,
    reply_to_message_id: int | None = None,
) -> None:
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "video": video_url,
    }

    if not video_url:
        print("Skipping: Video URL is empty")
        return

    if caption:
        payload["caption"] = caption

    if reply_to_message_id is not None:
        payload["reply_to_message_id"] = reply_to_message_id

    response = requests.post(
        f"{TELEGRAM_API_BASE}/sendVideo",
        data=payload,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
