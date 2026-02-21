"""
Nadaraya-Watson Envelope + Inverted Hammer Strategy

Only triggers alerts when an Inverted Hammer candle forms at the
upper or lower NW Envelope band on 15-minute charts.

Signal types:
    HAMMER AT LOWER BAND → Bullish reversal (potential BUY)
    HAMMER AT UPPER BAND → Rejection wick at resistance (potential SELL)
"""

import numpy as np
import pandas as pd


def gaussian_kernel(x: np.ndarray, bandwidth: float) -> np.ndarray:
    return np.exp(-x ** 2 / (2 * bandwidth ** 2))


def nadaraya_watson(source: np.ndarray, bandwidth: float = 8.0, lookback: int = 500) -> np.ndarray:
    """Compute Nadaraya-Watson kernel regression estimate."""
    n = len(source)
    if n == 0:
        return np.array([])

    window = min(lookback, n)
    smoothed = np.full(n, np.nan)

    for i in range(n):
        start = max(0, i - window + 1)
        indices = np.arange(start, i + 1)
        distances = (i - indices).astype(float)
        weights = gaussian_kernel(distances, bandwidth)
        weight_sum = weights.sum()

        if weight_sum > 0:
            smoothed[i] = np.sum(weights * source[start:i + 1]) / weight_sum

    return smoothed


def compute_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """Average True Range for envelope width calculation."""
    n = len(close)
    tr = np.zeros(n)
    tr[0] = high[0] - low[0]

    for i in range(1, n):
        tr[i] = max(
            high[i] - low[i],
            abs(high[i] - close[i - 1]),
            abs(low[i] - close[i - 1]),
        )

    atr = np.full(n, np.nan)
    if n >= period:
        atr[period - 1] = np.mean(tr[:period])
        for i in range(period, n):
            atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period

    return atr


def compute_envelope(
    df: pd.DataFrame,
    bandwidth: float = 8.0,
    multiplier: float = 3.0,
    atr_period: int = 14,
    lookback: int = 500,
) -> pd.DataFrame:
    """Compute NW Envelope. Adds: nw_mid, nw_upper, nw_lower, atr."""
    source = df["Close"].values.astype(float)
    high = df["High"].values.astype(float)
    low = df["Low"].values.astype(float)

    nw_mid = nadaraya_watson(source, bandwidth=bandwidth, lookback=lookback)
    atr = compute_atr(high, low, source, period=atr_period)

    result = df.copy()
    result["nw_mid"] = nw_mid
    result["nw_upper"] = nw_mid + multiplier * atr
    result["nw_lower"] = nw_mid - multiplier * atr
    result["atr"] = atr

    return result


def _is_inverted_hammer(o: float, h: float, l: float, c: float) -> bool:
    """Check if a single candle is an Inverted Hammer shape."""
    body = abs(c - o)
    full_range = h - l
    if full_range == 0:
        return False

    body_bottom = min(o, c)
    body_top = max(o, c)
    upper_shadow = h - body_top
    lower_shadow = body_bottom - l

    if body == 0:
        body = full_range * 0.01

    if upper_shadow < body * 2.0:
        return False
    if lower_shadow > body * 0.25:
        return False
    if (body_bottom - l) > full_range * 0.33:
        return False

    return True


def detect_hammer_at_bands(df: pd.DataFrame) -> list[dict]:
    """
    ONLY triggers when Inverted Hammer forms at envelope bands.
    No other signals — hammer at band or nothing.

    Returns:
        - HAMMER AT LOWER BAND → potential bullish reversal (BUY)
        - HAMMER AT UPPER BAND → rejection at resistance (SELL)
    """
    if len(df) < 5:
        return []

    curr = df.iloc[-1]

    if pd.isna(curr["nw_upper"]) or pd.isna(curr["nw_lower"]):
        return []

    hammer = _is_inverted_hammer(curr["Open"], curr["High"], curr["Low"], curr["Close"])
    if not hammer:
        return []

    atr_val = curr["atr"] if not pd.isna(curr["atr"]) else 0
    if atr_val == 0:
        return []

    signals = []
    close = curr["Close"]
    lower = curr["nw_lower"]
    upper = curr["nw_upper"]
    mid = curr["nw_mid"]

    dist_to_lower = close - lower
    dist_to_upper = upper - close

    # Hammer at or near lower band (within 0.5× ATR)
    if close <= lower or (0 < dist_to_lower <= 0.5 * atr_val):
        band_label = "AT" if close <= lower else "NEAR"
        signals.append({
            "type": "HAMMER AT LOWER BAND",
            "direction": "BUY",
            "band": "LOWER",
            "band_position": band_label,
            "reason": f"Inverted Hammer {band_label.lower()} lower NW band — bullish reversal",
            "close": round(close, 5),
            "lower_band": round(lower, 5),
            "upper_band": round(upper, 5),
            "mid": round(mid, 5),
            "atr": round(atr_val, 5),
        })

    # Hammer at or near upper band (within 0.5× ATR)
    if close >= upper or (0 < dist_to_upper <= 0.5 * atr_val):
        band_label = "AT" if close >= upper else "NEAR"
        signals.append({
            "type": "HAMMER AT UPPER BAND",
            "direction": "SELL",
            "band": "UPPER",
            "band_position": band_label,
            "reason": f"Inverted Hammer {band_label.lower()} upper NW band — overbought rejection",
            "close": round(close, 5),
            "lower_band": round(lower, 5),
            "upper_band": round(upper, 5),
            "mid": round(mid, 5),
            "atr": round(atr_val, 5),
        })

    return signals
