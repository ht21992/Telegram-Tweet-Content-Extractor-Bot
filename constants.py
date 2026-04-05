from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "1"))

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is missing in .env")

TELEGRAM_API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

OFFSET_FILE = "offset.txt"

ALLOWED_CHAT_TYPES = {"private", "group", "supergroup"}
FXTWITTER_API_BASE = "https://api.fxtwitter.com"
REQUEST_TIMEOUT = 30
LONG_POLL_TIMEOUT = 30
MAX_MESSAGE_LENGTH = 4000
