
# Telegram Tweet & Instagram Content Extractor Bot

A Telegram bot that extracts and translates tweet text from Twitter/X links and downloads media from Instagram posts/reels shared in chats.

## Features

* **Automatic Link Detection**: Detects Twitter/X and Instagram links in messages
* **Tweet Extraction & Translation**: Extracts tweet text and translates non-Persian tweets to Persian
* **X Media Support**: Sends tweet photos and videos (grouped when possible)
* **Instagram Support**: Downloads and sends images/videos from public Instagram posts and reels (including carousels)
* **Album Support**: Sends multiple media as Telegram albums (gallery)
* **Multi-chat Support**: Works in private chats, groups, and supergroups
* **Progress Feedback**: Shows processing status (downloading, preparing, sending)
* **Error Handling**: Graceful handling of invalid links and network issues

## Prerequisites

* Python 3.8+
* A Telegram Bot Token (from [@BotFather](https://t.me/botfather))

## Installation

```bash
git clone <repo>
cd <repo>

python -m venv venv
```

Activate:

* Windows: `venv\Scripts\activate`
* macOS/Linux: `source venv/bin/activate`

Install:

```bash
pip install -r requirements.txt
```

## Configuration

Create `.env`:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
POLL_INTERVAL=1
```

## Usage

```bash
python main.py
```

## How It Works

### Twitter/X

1. Detects X links in messages
2. Extracts tweet ID
3. Fetches tweet content via fxtwitter
4. Translates to Persian if needed
5. Sends:

   * text (or caption)
   * media (single or album)

### Instagram

1. Detects Instagram post/reel links
2. Downloads media using Instaloader
3. Extracts caption (if available)
4. Sends:

   * single media OR
   * full carousel as Telegram album

## Supported Links

### Twitter/X

* `https://twitter.com/.../status/...`
* `https://x.com/.../status/...`

### Instagram

* `https://instagram.com/p/...`
* `https://instagram.com/reel/...`
* `https://instagram.com/reels/...`

## Dependencies

* `requests`
* `python-dotenv`
* `instaloader`

## Limitations

- **Instagram Private Content**: Only public posts and reels are supported. Private accounts cannot be accessed.
- **Instagram Stability**: Media extraction relies on unofficial methods (Instaloader) and may break if Instagram changes its structure.
- **Telegram Album Limits**: Media groups support **2–10 items only**. Larger carousels are split into multiple albums.
- **Caption Length Limit**: Telegram captions are limited to **1024 characters**. Longer text (e.g., translated tweets) is sent as separate messages.
- **Rate Limits**: Heavy usage may trigger rate limits from Telegram, Instagram, or X sources.
- **X API Dependency**: Tweet data relies on third-party services (e.g., fxtwitter), which may occasionally fail or be unavailable.
- **Media Availability**: Some X or Instagram media may be unavailable due to regional restrictions or deletion.
- **Processing Time**: Instagram media downloads (especially videos or large carousels) may take a few seconds.
- **Environment Differences (Windows vs Server)**: Instagram scraping may work on local machines (e.g., Windows with a residential IP) but fail on cloud/VPS servers (e.g., Ubuntu) due to stricter rate limits and IP reputation checks. Using a logged-in Instagram session is recommended for server deployments.