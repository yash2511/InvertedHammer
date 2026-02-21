"""
NSE Telegram notifications — Inverted Hammer alerts.
"""

from datetime import datetime
from telegram import send_message


def send_nse_alert(matches: list[dict]) -> bool:
    """Send today's Inverted Hammer scan results."""
    return send_message(_build_message(matches))


def send_nse_history(matches: list[dict], days: int) -> bool:
    """Send historical Inverted Hammer scan results."""
    return send_message(_build_history_message(matches, days))


def _build_message(matches: list[dict]) -> str:
    now = datetime.now().strftime("%d %b %Y, %H:%M")

    if not matches:
        return (
            f"*NSE — Inverted Hammer Scanner*\n"
            f"_{now}_\n\n"
            f"No Inverted Hammer patterns detected today."
        )

    header = (
        f"*NSE — Inverted Hammer Scanner*\n"
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
        f"_Scan for potential bullish reversal._\n"
        f"_Always confirm with volume & next-day candle._"
    )

    return header + "\n\n".join(lines) + footer


def _build_history_message(matches: list[dict], days: int) -> str:
    now = datetime.now().strftime("%d %b %Y, %H:%M")

    if not matches:
        return (
            f"*NSE — Inverted Hammer (Last {days} Days)*\n"
            f"_{now}_\n\n"
            f"No patterns found in the last {days} trading days."
        )

    header = (
        f"*NSE — Inverted Hammer (Last {days} Days)*\n"
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
