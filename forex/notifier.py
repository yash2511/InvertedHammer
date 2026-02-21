"""
Forex Telegram notifications — NW Envelope + Inverted Hammer alerts.
"""

from datetime import datetime
from telegram import send_message


def send_forex_alert(signals: list[dict]) -> bool:
    """Send NW Envelope scan results to Telegram."""
    return send_message(_build_message(signals))


def _build_message(signals: list[dict]) -> str:
    now = datetime.now().strftime("%d %b %Y, %H:%M")

    if not signals:
        return (
            f"*FOREX — NW Envelope Scanner (15min)*\n"
            f"_{now}_\n\n"
            f"No signals right now. All instruments within envelope."
        )

    strong = [s for s in signals if s["type"] == "STRONG BUY"]

    header = (
        f"*FOREX — NW Envelope + Hammer (15min)*\n"
        f"_{now}_\n\n"
        f"*{len(signals)} signal(s) detected:*\n"
    )

    if strong:
        header += f"*({len(strong)} high-confidence with Inverted Hammer)*\n"
    header += f"{'─' * 30}\n"

    lines = []
    for s in signals:
        is_hammer = s.get("hammer", False)
        tag = s["type"]
        if is_hammer:
            tag += " + HAMMER"

        lines.append(
            f"*{tag} — {s['instrument']}*\n"
            f"  Close: `{s['close']}`  |  Envelope: `{s['envelope']}`\n"
            f"  NW Mid: `{s['mid']}`  |  ATR: `{s['atr']}`\n"
            f"  Confluence: `{s.get('confluence', 'N/A')}`\n"
            f"  _{s['reason']}_"
        )

    footer = (
        f"\n{'─' * 30}\n"
        f"_NW Envelope + Inverted Hammer | 15min_\n"
        f"_STRONG BUY = Hammer at envelope boundary_\n"
        f"_Always use stop-loss & risk management._"
    )

    return header + "\n\n".join(lines) + footer
