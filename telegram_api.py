from __future__ import annotations

from typing import Any

import requests
import json
import os

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
) -> dict[str, Any]:
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
    return response.json()


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


def send_photo_file(
    chat_id: int,
    file_path: str,
    reply_to_message_id: int | None = None,
    caption: str | None = None,
) -> None:
    data = {"chat_id": chat_id}
    if reply_to_message_id is not None:
        data["reply_to_message_id"] = reply_to_message_id
    if caption:
        data["caption"] = caption[:1024]

    with open(file_path, "rb") as photo_file:
        response = requests.post(
            f"{TELEGRAM_API_BASE}/sendPhoto",
            data=data,
            files={"photo": photo_file},
            timeout=REQUEST_TIMEOUT,
        )
    response.raise_for_status()


def send_video_file(
    chat_id: int,
    file_path: str,
    reply_to_message_id: int | None = None,
    caption: str | None = None,
) -> None:
    data = {"chat_id": chat_id}
    if reply_to_message_id is not None:
        data["reply_to_message_id"] = reply_to_message_id
    if caption:
        data["caption"] = caption[:1024]

    with open(file_path, "rb") as video_file:
        response = requests.post(
            f"{TELEGRAM_API_BASE}/sendVideo",
            data=data,
            files={"video": video_file},
            timeout=REQUEST_TIMEOUT,
        )
    response.raise_for_status()


def send_media_group_files(
    chat_id: int,
    media_items: list[tuple[str, str]],
    caption: str | None = None,
    reply_to_message_id: int | None = None,
) -> None:
    if len(media_items) < 2:
        raise ValueError("send_media_group_files requires at least 2 media items")

    media_payload: list[dict[str, Any]] = []
    files: dict[str, Any] = {}
    opened_files = []

    try:
        for index, (media_type, file_path) in enumerate(media_items):
            attach_name = f"file{index}"
            file_obj = open(file_path, "rb")
            opened_files.append(file_obj)

            if media_type == "photo":
                files[attach_name] = (
                    os.path.basename(file_path),
                    file_obj,
                    "image/jpeg",
                )
                item = {
                    "type": "photo",
                    "media": f"attach://{attach_name}",
                }
            elif media_type == "video":
                files[attach_name] = (
                    os.path.basename(file_path),
                    file_obj,
                    "video/mp4",
                )
                item = {
                    "type": "video",
                    "media": f"attach://{attach_name}",
                    "supports_streaming": True,
                }
            else:
                raise ValueError(f"Unsupported media type: {media_type}")

            if index == 0 and caption:
                item["caption"] = caption[:1024]

            media_payload.append(item)

        data: dict[str, Any] = {
            "chat_id": chat_id,
            "media": json.dumps(media_payload),
        }

        if reply_to_message_id is not None:
            data["reply_to_message_id"] = reply_to_message_id

        response = requests.post(
            f"{TELEGRAM_API_BASE}/sendMediaGroup",
            data=data,
            files=files,
            timeout=REQUEST_TIMEOUT * 3,
        )
        response.raise_for_status()

    finally:
        for file_obj in opened_files:
            try:
                file_obj.close()
            except Exception:
                pass


def send_chat_action(chat_id: int, action: str) -> None:
    response = requests.post(
        f"{TELEGRAM_API_BASE}/sendChatAction",
        data={
            "chat_id": chat_id,
            "action": action,
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def edit_message_text(chat_id: int, message_id: int, text: str) -> None:
    response = requests.post(
        f"{TELEGRAM_API_BASE}/editMessageText",
        data={
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def delete_message(chat_id: int, message_id: int) -> None:
    response = requests.post(
        f"{TELEGRAM_API_BASE}/deleteMessage",
        data={
            "chat_id": chat_id,
            "message_id": message_id,
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
