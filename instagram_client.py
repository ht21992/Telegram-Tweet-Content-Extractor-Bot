from __future__ import annotations

import os
from pathlib import Path

import instaloader


TEMP_DIR = Path("temp_instagram")
TEMP_DIR.mkdir(exist_ok=True)

_loader = instaloader.Instaloader(
    download_pictures=True,
    download_videos=True,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False,
    post_metadata_txt_pattern="",
    dirname_pattern=str(TEMP_DIR),
    filename_pattern="{shortcode}_{date_utc}",
)


def _cleanup_shortcode_files(shortcode: str) -> None:
    for file_path in TEMP_DIR.glob(f"{shortcode}*"):
        try:
            file_path.unlink()
        except FileNotFoundError:
            pass


def download_instagram_media(
    shortcode: str,
) -> tuple[list[tuple[str, str]], str | None]:
    """
    Returns:
        (media_items, caption)
    """
    _cleanup_shortcode_files(shortcode)

    post = instaloader.Post.from_shortcode(_loader.context, shortcode)
    caption = post.caption or ""

    _loader.download_post(post, target="")

    candidates = sorted(TEMP_DIR.glob(f"{shortcode}*"))

    media_items: list[tuple[str, str]] = []
    seen_paths: set[str] = set()

    for path in candidates:
        suffix = path.suffix.lower()
        resolved_path = str(path.resolve())

        if resolved_path in seen_paths:
            continue

        if suffix in {".jpg", ".jpeg", ".png"}:
            media_items.append(("photo", resolved_path))
            seen_paths.add(resolved_path)

        elif suffix == ".mp4":
            media_items.append(("video", resolved_path))
            seen_paths.add(resolved_path)

    return media_items, caption.strip() if caption else None


def cleanup_file(file_path: str) -> None:
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass
