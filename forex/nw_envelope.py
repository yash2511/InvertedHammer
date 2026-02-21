"""
Nadaraya-Watson Envelope Strategy

Replicates the TradingView "Nadaraya-Watson Envelope" indicator.

How it works:
    1. Kernel regression smooths price using a Gaussian (RBF) kernel
    2. Upper/lower envelopes are created using ATR-based multiplier
    3. Combined with Inverted Hammer detection at envelope boundaries

Signal hierarchy:
    STRONG BUY  → Inverted Hammer at lower envelope (highest confidence)
    BUY         → Price crossed below lower envelope
    SELL        → Price crossed above upper envelope
    WATCH BUY   → Hammer forming near lower envelope
    NEAR BUY    → Price approaching lower envelope
    NEAR SELL   → Price approaching upper envelope
"""

import numpy as np
import pandas as pd


def gaussian_kernel(x: np.ndarray, bandwidth: float) -> np.ndarray:
    """Gaussian (RBF) kernel: K(u) = exp(-u² / (2h²))"""
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
    """Compute the full Nadaraya-Watson Envelope. Adds: nw_mid, nw_upper, nw_lower, atr."""
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


# --- Inverted Hammer detection (inlined to keep forex/ self-contained) ---

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


def _has_prior_downtrend(closes: pd.Series, lookback: int = 3) -> bool:
    """Check for short-term downtrend before the signal candle."""
    if len(closes) < lookback + 1:
        return False
    recent = closes.iloc[-(lookback + 1):-1]
    return recent.iloc[-1] < recent.iloc[0]


# --- Signal detection combining NW Envelope + Inverted Hammer ---

def detect_signals(df: pd.DataFrame) -> list[dict]:
    """
    Detect signals combining NW Envelope zone + Inverted Hammer candle.

    STRONG BUY fires when an Inverted Hammer forms at the lower envelope —
    this is the highest-confidence bullish reversal signal.
    """
    if len(df) < 5:
        return []

    signals = []
    prev = df.iloc[-2]
    curr = df.iloc[-1]

    if pd.isna(curr["nw_upper"]) or pd.isna(curr["nw_lower"]):
        return []

    atr_val = curr["atr"] if not pd.isna(curr["atr"]) else 0
    hammer = _is_inverted_hammer(curr["Open"], curr["High"], curr["Low"], curr["Close"])
    downtrend = _has_prior_downtrend(df["Close"], lookback=3)

    at_lower = curr["Close"] <= curr["nw_lower"]
    crossed_lower = at_lower and prev["Close"] > prev["nw_lower"]
    near_lower = (
        not at_lower
        and atr_val > 0
        and 0 < (curr["Close"] - curr["nw_lower"]) <= 0.5 * atr_val
    )

    # STRONG BUY: Hammer + envelope boundary
    if hammer and (at_lower or near_lower) and downtrend:
        signals.append({
            "type": "STRONG BUY",
            "reason": "Inverted Hammer at lower envelope + downtrend (high-confidence reversal)",
            "close": round(curr["Close"], 5),
            "envelope": round(curr["nw_lower"], 5),
            "mid": round(curr["nw_mid"], 5),
            "atr": round(atr_val, 5),
            "hammer": True,
            "confluence": "NW Envelope + Inverted Hammer + Downtrend",
        })
    elif hammer and (at_lower or near_lower):
        signals.append({
            "type": "STRONG BUY",
            "reason": "Inverted Hammer at lower envelope (bullish reversal)",
            "close": round(curr["Close"], 5),
            "envelope": round(curr["nw_lower"], 5),
            "mid": round(curr["nw_mid"], 5),
            "atr": round(atr_val, 5),
            "hammer": True,
            "confluence": "NW Envelope + Inverted Hammer",
        })
    elif crossed_lower:
        signals.append({
            "type": "BUY",
            "reason": "Price crossed below lower envelope (oversold)",
            "close": round(curr["Close"], 5),
            "envelope": round(curr["nw_lower"], 5),
            "mid": round(curr["nw_mid"], 5),
            "atr": round(atr_val, 5),
            "hammer": False,
            "confluence": "NW Envelope only",
        })

    # SELL: upper envelope
    at_upper = curr["Close"] >= curr["nw_upper"]
    crossed_upper = at_upper and prev["Close"] < prev["nw_upper"]

    if crossed_upper:
        signals.append({
            "type": "SELL",
            "reason": "Price crossed above upper envelope (overbought)",
            "close": round(curr["Close"], 5),
            "envelope": round(curr["nw_upper"], 5),
            "mid": round(curr["nw_mid"], 5),
            "atr": round(atr_val, 5),
            "hammer": False,
            "confluence": "NW Envelope only",
        })

    # APPROACHING ZONES
    if not signals and atr_val > 0:
        dist_lower = curr["Close"] - curr["nw_lower"]
        dist_upper = curr["nw_upper"] - curr["Close"]

        if near_lower and hammer:
            signals.append({
                "type": "WATCH BUY",
                "reason": "Inverted Hammer forming near lower envelope",
                "close": round(curr["Close"], 5),
                "envelope": round(curr["nw_lower"], 5),
                "mid": round(curr["nw_mid"], 5),
                "atr": round(atr_val, 5),
                "hammer": True,
                "confluence": "NW Envelope + Inverted Hammer (approaching)",
            })
        elif 0 < dist_lower <= 0.3 * atr_val:
            signals.append({
                "type": "NEAR BUY",
                "reason": "Price approaching lower envelope",
                "close": round(curr["Close"], 5),
                "envelope": round(curr["nw_lower"], 5),
                "mid": round(curr["nw_mid"], 5),
                "atr": round(atr_val, 5),
                "hammer": False,
                "confluence": "NW Envelope only",
            })

        if 0 < dist_upper <= 0.3 * atr_val:
            signals.append({
                "type": "NEAR SELL",
                "reason": "Price approaching upper envelope",
                "close": round(curr["Close"], 5),
                "envelope": round(curr["nw_upper"], 5),
                "mid": round(curr["nw_mid"], 5),
                "atr": round(atr_val, 5),
                "hammer": False,
                "confluence": "NW Envelope only",
            })

    return signals
