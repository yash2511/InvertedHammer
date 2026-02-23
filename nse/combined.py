"""
Combined NSE scan — Inverted Hammer (BUY) + Shooting Star (SHORT)
in a single Telegram message.
"""

from datetime import datetime
from telegram import send_message


def send_combined_alert(hammer_matches: list[dict], star_matches: list[dict]) -> bool:
    """Send both patterns in one combined Telegram message."""
    return send_message(_build_combined_message(hammer_matches, star_matches))


def _build_combined_message(hammer_matches: list[dict], star_matches: list[dict]) -> str:
    now = datetime.now().strftime("%d %b %Y")
    total = len(hammer_matches) + len(star_matches)

    lines = [f"📊 *NSE Scan — {now}*\n"]

    lines.append("🟢 *BUY signals (Inverted Hammer)*")
    if hammer_matches:
        for m in hammer_matches:
            sym = m["symbol"].replace(".NS", "")
            lines.append(
                f"  `{sym}` — ₹{m['close']}\n"
                f"  Upper Wick: `{m['upper_shadow']}`  |  Wick/Body: `{m.get('upper_shadow_to_body', '—')}x`"
            )
    else:
        lines.append("  _None today_")
    lines.append("")

    lines.append("🔴 *SHORT signals (Shooting Star)*")
    if star_matches:
        for m in star_matches:
            sym = m["symbol"].replace(".NS", "")
            ema_pct = m.get("above_ema_pct", "—")
            lines.append(
                f"  `{sym}` — ₹{m['close']}\n"
                f"  Upper Wick: `{m['upper_shadow']}`  |  Wick/Body: `{m.get('upper_shadow_to_body', '—')}x`\n"
                f"  Above 20 EMA: `+{ema_pct}%`"
            )
    else:
        lines.append("  _None today_")
    lines.append("")

    lines.append("_Confirm with next candle & volume_")

    return "\n".join(lines)
