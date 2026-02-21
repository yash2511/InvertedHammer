"""
Telegram notification module.
Sends scan results as a formatted message to a Telegram chat.
"""

import logging
from datetime import datetime

import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


def _build_message(matches: list[dict]) -> str:
    now = datetime.now().strftime("%d %b %Y, %H:%M")

    if not matches:
        return (
            f"*Inverted Hammer Scanner*\n"
            f"_{now}_\n\n"
            f"No Inverted Hammer patterns detected today."
        )

    header = (
        f"*Inverted Hammer Scanner*\n"
        f"_{now}_\n\n"
        f"*{len(matches)} stock(s) detected:*\n"
        f"{'─' * 30}\n"
    )

    lines = []
    for m in matches:
        symbol = m["symbol"].replace(".NS", "")
        lines.append(
            f"*{symbol}*\n"
            f"  Close: `{m['close']}`  |  Date: `{m['date']}`\n"
            f"  Body: `{m['body']}`  |  Upper Wick: `{m['upper_shadow']}`\n"
            f"  Wick/Body Ratio: `{m.get('upper_shadow_to_body', 'N/A')}`"
        )

    footer = (
        f"\n{'─' * 30}\n"
        f"_Scan for potential bullish reversal. "
        f"Always confirm with volume & next-day candle._"
    )

    return header + "\n\n".join(lines) + footer


def send_telegram(matches: list[dict]) -> bool:
    """Send the scan results to Telegram. Returns True on success."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error(
            "Telegram credentials not configured. "
            "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env"
        )
        return False

    message = _build_message(matches)

    try:
        resp = requests.post(
            TELEGRAM_API,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            logger.info("Telegram message sent successfully.")
            return True
        else:
            logger.error("Telegram API error %s: %s", resp.status_code, resp.text)
            return False
    except Exception as e:
        logger.error("Failed to send Telegram message: %s", e)
        return False


def _build_history_message(matches: list[dict], days: int) -> str:
    now = datetime.now().strftime("%d %b %Y, %H:%M")

    if not matches:
        return (
            f"*Inverted Hammer — Last {days} Days*\n"
            f"_{now}_\n\n"
            f"No Inverted Hammer patterns found in the last {days} trading days."
        )

    header = (
        f"*Inverted Hammer — Last {days} Days*\n"
        f"_{now}_\n\n"
        f"*{len(matches)} occurrence(s) found:*\n"
        f"{'─' * 30}\n"
    )

    lines = []
    for m in matches:
        symbol = m["symbol"].replace(".NS", "")
        lines.append(
            f"*{symbol}*  —  `{m['date']}`\n"
            f"  Close: `{m['close']}`  |  Upper Wick: `{m['upper_shadow']}`\n"
            f"  Wick/Body: `{m.get('upper_shadow_to_body', 'N/A')}`"
        )

    footer = (
        f"\n{'─' * 30}\n"
        f"_Historical scan. Verify with volume & follow-through candles._"
    )

    return header + "\n\n".join(lines) + footer


def send_telegram_history(matches: list[dict], days: int) -> bool:
    """Send the history scan results to Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error(
            "Telegram credentials not configured. "
            "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env"
        )
        return False

    message = _build_history_message(matches, days)

    try:
        resp = requests.post(
            TELEGRAM_API,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            logger.info("Telegram history message sent successfully.")
            return True
        else:
            logger.error("Telegram API error %s: %s", resp.status_code, resp.text)
            return False
    except Exception as e:
        logger.error("Failed to send Telegram message: %s", e)
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample = [
        {
            "symbol": "RELIANCE.NS",
            "date": "2026-02-20",
            "close": 2450.50,
            "body": 12.30,
            "upper_shadow": 38.70,
            "lower_shadow": 2.10,
            "upper_shadow_to_body": 3.15,
        }
    ]
    print(_build_message(sample))
    print("\n--- Sending test message ---")
    send_telegram(sample)
