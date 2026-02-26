"""
Falling Wedge breakout pattern detection.

A Falling Wedge is a multi-candle chart pattern where price makes
converging lower highs and lower lows.  A breakout above the upper
trendline is a bullish signal.

Detection steps:
    1. Identify swing highs and swing lows over a lookback window.
    2. Fit linear-regression trendlines through each set.
    3. Validate: both trendlines slope downward and converge
       (resistance slope is steeper negative than support slope).
    4. Breakout: the latest candle closes above the projected
       upper trendline value.
"""

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Swing-point helpers
# ---------------------------------------------------------------------------

def find_swing_highs(highs: pd.Series, order: int = 3) -> list[tuple[int, float]]:
    """Return (index_position, value) pairs for local maxima.

    A swing high at position i means highs[i] >= all neighbours
    within ``order`` bars on each side.
    """
    pts = []
    arr = highs.values
    for i in range(order, len(arr) - order):
        window = arr[i - order: i + order + 1]
        if arr[i] == window.max():
            pts.append((i, float(arr[i])))
    return pts


def find_swing_lows(lows: pd.Series, order: int = 3) -> list[tuple[int, float]]:
    """Return (index_position, value) pairs for local minima."""
    pts = []
    arr = lows.values
    for i in range(order, len(arr) - order):
        window = arr[i - order: i + order + 1]
        if arr[i] == window.min():
            pts.append((i, float(arr[i])))
    return pts


# ---------------------------------------------------------------------------
# Trendline fitting
# ---------------------------------------------------------------------------

def fit_trendline(points: list[tuple[int, float]]) -> dict | None:
    """Ordinary least-squares line through ``(x, y)`` pairs.

    Returns dict with keys: slope, intercept, r_squared.
    Returns None when fewer than 2 points.
    """
    if len(points) < 2:
        return None

    xs = np.array([p[0] for p in points], dtype=float)
    ys = np.array([p[1] for p in points], dtype=float)

    coeffs = np.polyfit(xs, ys, 1)
    slope, intercept = coeffs

    y_pred = np.polyval(coeffs, xs)
    ss_res = np.sum((ys - y_pred) ** 2)
    ss_tot = np.sum((ys - ys.mean()) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot != 0 else 0.0

    return {"slope": slope, "intercept": intercept, "r_squared": r_squared}


def _trendline_value_at(tl: dict, x: int) -> float:
    """Project trendline value at bar index ``x``."""
    return tl["slope"] * x + tl["intercept"]


# ---------------------------------------------------------------------------
# Wedge validation
# ---------------------------------------------------------------------------

def _is_valid_wedge(
    resistance: dict,
    support: dict,
    min_r2: float = 0.60,
) -> bool:
    """Check if two trendlines form a valid falling wedge.

    Conditions:
        - Both slopes are negative (falling).
        - Resistance slope is more negative than support slope (convergence).
        - Both trendlines have reasonable R² fit.
    """
    if resistance["slope"] >= 0 or support["slope"] >= 0:
        return False
    if resistance["slope"] >= support["slope"]:
        return False
    if resistance["r_squared"] < min_r2 or support["r_squared"] < min_r2:
        return False
    return True


# ---------------------------------------------------------------------------
# Public detection API
# ---------------------------------------------------------------------------

def detect_breakout(
    df: pd.DataFrame,
    lookback: int = 40,
    swing_order: int = 3,
    min_r2: float = 0.60,
) -> bool:
    """Return True if the latest candle breaks out of a falling wedge."""
    if df is None or len(df) < lookback:
        return False

    window = df.iloc[-lookback:]
    sh = find_swing_highs(window["High"], order=swing_order)
    sl = find_swing_lows(window["Low"], order=swing_order)

    if len(sh) < 2 or len(sl) < 2:
        return False

    resistance = fit_trendline(sh)
    support = fit_trendline(sl)

    if resistance is None or support is None:
        return False
    if not _is_valid_wedge(resistance, support, min_r2):
        return False

    last_idx = lookback - 1
    projected_resistance = _trendline_value_at(resistance, last_idx)
    latest_close = float(window.iloc[-1]["Close"])

    return latest_close > projected_resistance


def detect_breakout_history(
    df: pd.DataFrame,
    lookback_days: int = 30,
    wedge_lookback: int = 40,
    swing_order: int = 3,
    min_r2: float = 0.60,
) -> list[dict]:
    """Scan the last ``lookback_days`` candles for falling-wedge breakouts."""
    if df is None or len(df) < wedge_lookback + lookback_days:
        needed = wedge_lookback
        if df is not None and len(df) >= needed:
            start_idx = needed
        else:
            return []
    else:
        start_idx = len(df) - lookback_days

    matches: list[dict] = []
    for i in range(start_idx, len(df)):
        sub = df.iloc[max(0, i - wedge_lookback + 1): i + 1]
        if len(sub) < wedge_lookback:
            continue

        sh = find_swing_highs(sub["High"], order=swing_order)
        sl = find_swing_lows(sub["Low"], order=swing_order)
        if len(sh) < 2 or len(sl) < 2:
            continue

        resistance = fit_trendline(sh)
        support = fit_trendline(sl)
        if resistance is None or support is None:
            continue
        if not _is_valid_wedge(resistance, support, min_r2):
            continue

        last_idx = len(sub) - 1
        projected_resistance = _trendline_value_at(resistance, last_idx)
        row = sub.iloc[-1]
        close = float(row["Close"])

        if close <= projected_resistance:
            continue

        vol = float(row["Volume"]) if "Volume" in row.index else 0
        avg_vol = float(sub["Volume"].rolling(20).mean().iloc[-1]) if "Volume" in sub.columns and len(sub) >= 20 else 0
        vol_pct = round((vol / avg_vol - 1) * 100, 1) if avg_vol > 0 else 0.0

        matches.append({
            "date": str(row.name.date()) if hasattr(row.name, "date") else str(row.name),
            "close": round(close, 2),
            "volume": int(vol),
            "vol_vs_avg_pct": vol_pct,
            "wedge_candles": wedge_lookback,
            "resistance_slope": round(resistance["slope"], 4),
            "support_slope": round(support["slope"], 4),
        })

    return matches


def scan_dataframe(df: pd.DataFrame, wedge_lookback: int = 40, swing_order: int = 3) -> dict:
    """Return diagnostic info for the latest falling-wedge breakout."""
    if df is None or len(df) < wedge_lookback:
        return {}

    window = df.iloc[-wedge_lookback:]
    row = window.iloc[-1]
    close = float(row["Close"])

    sh = find_swing_highs(window["High"], order=swing_order)
    sl = find_swing_lows(window["Low"], order=swing_order)

    resistance = fit_trendline(sh) if len(sh) >= 2 else None
    support = fit_trendline(sl) if len(sl) >= 2 else None

    vol = float(row["Volume"]) if "Volume" in row.index else 0
    avg_vol = float(window["Volume"].rolling(20).mean().iloc[-1]) if "Volume" in window.columns and len(window) >= 20 else 0
    vol_pct = round((vol / avg_vol - 1) * 100, 1) if avg_vol > 0 else 0.0

    return {
        "date": str(row.name.date()) if hasattr(row.name, "date") else str(row.name),
        "close": round(close, 2),
        "volume": int(vol),
        "vol_vs_avg_pct": vol_pct,
        "wedge_candles": wedge_lookback,
        "resistance_slope": round(resistance["slope"], 4) if resistance else None,
        "support_slope": round(support["slope"], 4) if support else None,
    }
