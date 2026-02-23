"""
Shooting Star candlestick pattern detection.

A Shooting Star forms after an uptrend at resistance and signals
a potential bearish reversal (shorting opportunity).

Anatomy (same shape as Inverted Hammer, but context differs):
    ┃  ← long upper shadow (wick) ≥ 2× body
    ┣┫ ← small real body near the low
    ╹  ← little or no lower shadow

Key difference from Inverted Hammer:
    - Inverted Hammer → after DOWNTREND → bullish reversal (BUY)
    - Shooting Star   → after UPTREND  → bearish reversal (SHORT/SELL)

Rules applied:
    1. Upper shadow ≥ 2× the real body
    2. Lower shadow ≤ 25% of the real body (near-zero)
    3. Real body is in the lower third of the full candle range
    4. Prior 3-day trend is BULLISH (closes rising) — at resistance
    5. Price must be ABOVE the 20 EMA with significant distance
       (close > 20 EMA, and gap > 2.0% of price — means overextended)
"""

import pandas as pd
import numpy as np


def is_shooting_star(
    open_: float,
    high: float,
    low: float,
    close: float,
    body_ratio: float = 2.0,
    lower_shadow_tolerance: float = 0.25,
) -> bool:
    """Check if a single candle qualifies as a Shooting Star shape."""
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


def has_prior_uptrend(closes: pd.Series, lookback: int = 3) -> bool:
    """Check that the stock was in a short-term UPTREND before the signal candle."""
    if len(closes) < lookback + 1:
        return False
    recent = closes.iloc[-(lookback + 1):-1]
    return recent.iloc[-1] > recent.iloc[0]


def compute_ema(closes: pd.Series, period: int = 20) -> pd.Series:
    """Compute Exponential Moving Average."""
    return closes.ewm(span=period, adjust=False).mean()


def is_above_ema_with_distance(
    close: float,
    ema_value: float,
    min_distance_pct: float = 2.0,
) -> tuple[bool, float]:
    """
    Check if close is above EMA with significant distance.
    Returns (is_valid, distance_pct).
    min_distance_pct: minimum gap as % of price (default 0.5%).
    """
    if ema_value == 0:
        return False, 0.0
    distance_pct = ((close - ema_value) / ema_value) * 100
    return distance_pct >= min_distance_pct, round(distance_pct, 2)


def detect_shooting_star(df: pd.DataFrame) -> bool:
    """
    Return True if the latest candle is a Shooting Star:
    1. Candle shape matches
    2. Prior 3-day uptrend
    3. Price is above 20 EMA with significant distance (overextended)
    """
    if df is None or len(df) < 21:
        return False

    latest = df.iloc[-1]
    candle_match = is_shooting_star(
        open_=latest["Open"],
        high=latest["High"],
        low=latest["Low"],
        close=latest["Close"],
    )
    if not candle_match:
        return False

    if not has_prior_uptrend(df["Close"]):
        return False

    ema20 = compute_ema(df["Close"], period=20)
    above_ema, _ = is_above_ema_with_distance(latest["Close"], ema20.iloc[-1])

    return above_ema


def detect_shooting_star_history(df: pd.DataFrame, lookback_days: int = 15) -> list[dict]:
    """Scan the last `lookback_days` candles for Shooting Star patterns."""
    if df is None or len(df) < 21:
        return []

    ema20 = compute_ema(df["Close"], period=20)
    matches = []
    start_idx = max(20, len(df) - lookback_days)

    for i in range(start_idx, len(df)):
        row = df.iloc[i]
        candle_match = is_shooting_star(
            open_=row["Open"],
            high=row["High"],
            low=row["Low"],
            close=row["Close"],
        )
        if not candle_match:
            continue

        sub_df = df.iloc[:i + 1]
        if not has_prior_uptrend(sub_df["Close"]):
            continue

        above_ema, dist_pct = is_above_ema_with_distance(row["Close"], ema20.iloc[i])
        if not above_ema:
            continue

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
            "ema20": round(ema20.iloc[i], 2),
            "above_ema_pct": dist_pct,
        })

    return matches


def scan_dataframe(df: pd.DataFrame) -> dict:
    """Return diagnostic info for the latest candle including 20 EMA."""
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

    ema20 = compute_ema(df["Close"], period=20)
    ema_val = ema20.iloc[-1]
    _, dist_pct = is_above_ema_with_distance(c, ema_val)

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
        "ema20": round(ema_val, 2),
        "above_ema_pct": dist_pct,
    }
