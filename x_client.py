from __future__ import annotations

from typing import Any

import requests

from constants import FXTWITTER_API_BASE, REQUEST_TIMEOUT


def get_tweet_payload(
    tweet_id: str, translate_to: str | None = None
) -> dict[str, Any] | None:
    # FixTweet docs say screen_name is ignored, so using /i/status/:id is fine
    url = f"{FXTWITTER_API_BASE}/i/status/{tweet_id}"
    if translate_to:
        url = f"{url}/{translate_to}"

    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    data: dict[str, Any] = response.json()
    if data.get("code") != 200:
        return None

    tweet = data.get("tweet")

    if not isinstance(tweet, dict):
        return None

    # print(tweet)
    media = tweet.get("media") or {}

    photos = media.get("photos") or []
    videos = media.get("videos") or []

    photos = [item["url"] for item in photos if item.get("url")]
    videos = [item["url"] for item in videos if item.get("url")]

    return tweet, photos, videos
