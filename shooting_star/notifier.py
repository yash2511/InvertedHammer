"""
Shooting Star Telegram notifications — bearish reversal / shorting alerts.
"""

from datetime import datetime
from telegram import send_message


def send_shooting_star_alert(matches: list[dict]) -> bool:
    """Send today's Shooting Star scan results."""
    return send_message(_build_message(matches))


def send_shooting_star_history(matches: list[dict], days: int) -> bool:
    """Send historical Shooting Star scan results."""
    return send_message(_build_history_message(matches, days))


def _build_message(matches: list[dict]) -> str:
    now = datetime.now().strftime("%d %b %Y, %H:%M")

    if not matches:
        return (
            f"*NSE — Shooting Star Scanner*\n"
            f"_{now}_\n\n"
            f"No Shooting Star patterns detected today."
        )

    header = (
        f"*NSE — Shooting Star (Short at Resistance)*\n"
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
            f"  Wick/Body: `{m.get('upper_shadow_to_body', 'N/A')}`\n"
            f"  20 EMA: `{m.get('ema20', 'N/A')}`  |  Above EMA: `{m.get('above_ema_pct', 'N/A')}%`\n"
            f"  _Bearish reversal — potential SHORT_"
        )

    footer = (
        f"\n{'─' * 30}\n"
        f"_Shooting Star above 20 EMA at resistance._\n"
        f"_Higher distance from EMA = stronger signal._\n"
        f"_Confirm with next-day bearish candle & volume._"
    )

    return header + "\n\n".join(lines) + footer


def _build_history_message(matches: list[dict], days: int) -> str:
    now = datetime.now().strftime("%d %b %Y, %H:%M")

    if not matches:
        return (
            f"*NSE — Shooting Star (Last {days} Days)*\n"
            f"_{now}_\n\n"
            f"No patterns found in the last {days} trading days."
        )

    header = (
        f"*NSE — Shooting Star (Last {days} Days)*\n"
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
            f"  Wick/Body: `{m.get('upper_shadow_to_body', 'N/A')}`\n"
            f"  20 EMA: `{m.get('ema20', 'N/A')}`  |  Above EMA: `{m.get('above_ema_pct', 'N/A')}%`"
        )

    footer = (
        f"\n{'─' * 30}\n"
        f"_Shooting Star above 20 EMA at resistance._\n"
        f"_Higher distance = stronger SHORT signal._"
    )

    return header + "\n\n".join(lines) + footer
