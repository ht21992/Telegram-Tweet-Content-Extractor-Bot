# Telegram Tweet Text Extractor Bot

A Telegram bot that extracts and translates tweet text from Twitter/X links shared in chats. The bot fetches tweet content, translates non-Persian tweets to Persian, and sends back the text along with any attached media (photos and videos).

## Features

- **Automatic Tweet Extraction**: Detects Twitter/X links in Telegram messages and extracts tweet content
- **Translation Support**: Translates tweets to Persian (Farsi) if the original language is not Persian
- **Media Support**: Downloads and forwards tweet photos and videos
- **Multi-chat Support**: Works in private chats, groups, and supergroups
- **Error Handling**: Graceful handling of network errors and invalid tweets

## Prerequisites

- Python 3.8+
- A Telegram Bot Token (obtained from [@BotFather](https://t.me/botfather))

## Installation

1. Clone or download this repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Create a `.env` file in the project root
2. Add your Telegram bot token:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```
3. Optionally, adjust the polling interval (default is 1 second):
   ```
   POLL_INTERVAL=1
   ```

## Usage

Run the bot:
```bash
python main.py
```

The bot will start polling for updates and process messages containing Twitter/X links.

## How It Works

1. The bot monitors Telegram chats for new messages
2. When a message containing a Twitter/X link is detected, it extracts the tweet ID
3. Fetches tweet data using the fxtwitter API
4. If the tweet is not in Persian, translates it to Persian
5. Sends the tweet text (original + translation if applicable) back to the chat
6. Downloads and forwards any attached photos and videos

## Supported Link Formats

The bot recognizes various Twitter/X URL formats:
- `https://twitter.com/username/status/tweet_id`
- `https://x.com/username/status/tweet_id`
- Shortened URLs and other variations

## Dependencies

- `python-dotenv`: For environment variable management
- `requests`: For HTTP requests (install via pip if not included)

## Project Structure

- `main.py`: Main bot logic and message processing
- `telegram_api.py`: Telegram API wrapper functions
- `x_client.py`: Twitter/X API client using fxtwitter
- `helpers.py`: Utility functions for text processing and tweet ID extraction
- `constants.py`: Configuration constants and environment loading
