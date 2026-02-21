"""
Forex Telegram notifications.
Only sends alerts when Inverted Hammer forms at NW Envelope band.
"""

from datetime import datetime
from telegram import send_message


def send_forex_alert(signals: list[dict]) -> bool:
    """Send hammer-at-band alerts. Only sends if signals found."""
    if not signals:
        return True
    return send_message(_build_message(signals))


def _build_message(signals: list[dict]) -> str:
    now = datetime.now().strftime("%d %b %Y, %H:%M")

    buy_count = sum(1 for s in signals if s["direction"] == "BUY")
    sell_count = sum(1 for s in signals if s["direction"] == "SELL")

    header = (
        f"*FOREX — Hammer at NW Band (15min)*\n"
        f"_{now}_\n\n"
        f"*{len(signals)} signal(s):*"
    )
    if buy_count:
        header += f"  {buy_count} BUY"
    if sell_count:
        header += f"  {sell_count} SELL"
    header += f"\n{'─' * 30}\n"

    lines = []
    for s in signals:
        direction = s["direction"]
        band = s["band"]
        pos = s["band_position"]

        lines.append(
            f"*{direction} — {s['instrument']}*\n"
            f"  Hammer `{pos}` `{band}` band\n"
            f"  Close: `{s['close']}`\n"
            f"  Lower Band: `{s['lower_band']}`\n"
            f"  Upper Band: `{s['upper_band']}`\n"
            f"  NW Mid: `{s['mid']}`  |  ATR: `{s['atr']}`\n"
            f"  _{s['reason']}_"
        )

    footer = (
        f"\n{'─' * 30}\n"
        f"_Inverted Hammer + NW Envelope | 15min_\n"
        f"_LOWER band = potential BUY_\n"
        f"_UPPER band = potential SELL_\n"
        f"_Always use stop-loss & risk management._"
    )

    return header + "\n\n".join(lines) + footer
