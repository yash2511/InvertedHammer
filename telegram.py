"""
Shared Telegram messaging utility.
Used by both NSE and Forex scanners.
"""

import logging

import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)


def send_message(text: str) -> bool:
    """Send a Markdown-formatted message to Telegram. Raises on failure so CI turns red."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        msg = (
            "Telegram credentials not configured. "
            "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID as env vars or in .env"
        )
        logger.error(msg)
        raise RuntimeError(msg)

    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    resp = requests.post(
        api_url,
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        },
        timeout=15,
    )

    if resp.status_code == 200:
        logger.info("Telegram message sent successfully.")
        return True

    logger.error("Telegram API error %s: %s", resp.status_code, resp.text)
    raise RuntimeError(f"Telegram API error {resp.status_code}: {resp.text}")
