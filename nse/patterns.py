"""
Inverted Hammer candlestick pattern detection.

An Inverted Hammer forms after a downtrend and signals a potential bullish reversal.

Anatomy:
    ┃  ← long upper shadow (wick) ≥ 2× body
    ┣┫ ← small real body near the low
    ╹  ← little or no lower shadow

Rules applied:
    1. Upper shadow ≥ 2× the real body
    2. Lower shadow ≤ 25% of the real body (near-zero)
    3. Real body is in the lower third of the full candle range
    4. Prior 3-day trend is bearish (closes declining)
"""

import pandas as pd
import numpy as np


def is_inverted_hammer(
    open_: float,
    high: float,
    low: float,
    close: float,
    body_ratio: float = 2.0,
    lower_shadow_tolerance: float = 0.25,
) -> bool:
    """Check if a single candle qualifies as an Inverted Hammer shape."""
    body = abs(close - open_)
    full_range = high - low

    if full_range == 0:
        return False

    body_bottom = min(open_, close)
    body_top = max(open_, close)

    upper_shadow = high - body_top
    lower_shadow = body_bottom - low

    if body == 0:
        body = full_range * 0.01

    if upper_shadow < body * body_ratio:
        return False

    if lower_shadow > body * lower_shadow_tolerance:
        return False

    if (body_bottom - low) > full_range * 0.33:
        return False

    return True


def has_prior_downtrend(closes: pd.Series, lookback: int = 3) -> bool:
    """Check that the stock was in a short-term downtrend before the signal candle."""
    if len(closes) < lookback + 1:
        return False
    recent = closes.iloc[-(lookback + 1):-1]
    return recent.iloc[-1] < recent.iloc[0]


def detect_inverted_hammer(df: pd.DataFrame) -> bool:
    """
    Return True if the latest candle is an Inverted Hammer
    following a short-term downtrend.
    """
    if df is None or len(df) < 5:
        return False

    latest = df.iloc[-1]
    candle_match = is_inverted_hammer(
        open_=latest["Open"],
        high=latest["High"],
        low=latest["Low"],
        close=latest["Close"],
    )
    if not candle_match:
        return False

    return has_prior_downtrend(df["Close"])


def detect_inverted_hammer_history(df: pd.DataFrame, lookback_days: int = 15) -> list[dict]:
    """Scan the last `lookback_days` candles for Inverted Hammer patterns."""
    if df is None or len(df) < 5:
        return []

    matches = []
    start_idx = max(4, len(df) - lookback_days)

    for i in range(start_idx, len(df)):
        row = df.iloc[i]
        candle_match = is_inverted_hammer(
            open_=row["Open"],
            high=row["High"],
            low=row["Low"],
            close=row["Close"],
        )
        if not candle_match:
            continue

        sub_df = df.iloc[:i + 1]
        if has_prior_downtrend(sub_df["Close"]):
            o, h, l, c = row["Open"], row["High"], row["Low"], row["Close"]
            body = abs(c - o)
            body_top = max(o, c)
            upper_shadow = h - body_top

            matches.append({
                "date": str(row.name.date()) if hasattr(row.name, "date") else str(row.name),
                "open": round(o, 2),
                "high": round(h, 2),
                "low": round(l, 2),
                "close": round(c, 2),
                "body": round(body, 2),
                "upper_shadow": round(upper_shadow, 2),
                "upper_shadow_to_body": round(upper_shadow / body, 2) if body > 0 else None,
            })

    return matches


def scan_dataframe(df: pd.DataFrame) -> dict:
    """Return diagnostic info for the latest candle."""
    if df is None or len(df) < 1:
        return {}

    latest = df.iloc[-1]
    o, h, l, c = latest["Open"], latest["High"], latest["Low"], latest["Close"]
    body = abs(c - o)
    body_top = max(o, c)
    body_bottom = min(o, c)
    upper_shadow = h - body_top
    lower_shadow = body_bottom - l
    full_range = h - l

    return {
        "date": str(latest.name.date()) if hasattr(latest.name, "date") else str(latest.name),
        "open": round(o, 2),
        "high": round(h, 2),
        "low": round(l, 2),
        "close": round(c, 2),
        "body": round(body, 2),
        "upper_shadow": round(upper_shadow, 2),
        "lower_shadow": round(lower_shadow, 2),
        "range": round(full_range, 2),
        "upper_shadow_to_body": round(upper_shadow / body, 2) if body > 0 else None,
    }
