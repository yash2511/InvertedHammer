"""
Combined NSE scan — Inverted Hammer (BUY) + Falling Wedge (BUY)
+ Shooting Star (SHORT) in a single Telegram message.
"""

from datetime import datetime
from telegram import send_message


def send_combined_alert(
    hammer_matches: list[dict],
    star_matches: list[dict],
    wedge_matches: list[dict] | None = None,
) -> bool:
    """Send all patterns in one combined Telegram message."""
    if wedge_matches is None:
        wedge_matches = []
    return send_message(_build_combined_message(hammer_matches, star_matches, wedge_matches))


def _build_combined_message(
    hammer_matches: list[dict],
    star_matches: list[dict],
    wedge_matches: list[dict],
) -> str:
    now = datetime.now().strftime("%d %b %Y")

    lines = [f"📊 *NSE Scan — {now}*\n"]

    # --- Inverted Hammer ---
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

    # --- Falling Wedge Breakout ---
    lines.append("📐 *BUY signals (Falling Wedge Breakout)*")
    if wedge_matches:
        for m in wedge_matches:
            sym = m["symbol"].replace(".NS", "")
            vol_pct = m.get("vol_vs_avg_pct", 0)
            vol_str = f"+{vol_pct}%" if vol_pct >= 0 else f"{vol_pct}%"
            lines.append(
                f"  `{sym}` — ₹{m['close']}\n"
                f"  Wedge: `{m.get('wedge_candles', '—')} weeks`  |  Vol: `{vol_str}`"
            )
    else:
        lines.append("  _None today_")
    lines.append("")

    # --- Shooting Star ---
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
