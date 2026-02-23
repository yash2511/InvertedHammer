"""
Forex Backtest — scan last N days of 15-min candles
for every Inverted Hammer that formed at NW Envelope bands.
Also tracks what happened AFTER the signal (profit/loss).
"""

import logging
from datetime import datetime

import yfinance as yf
import pandas as pd
import numpy as np

from forex.nw_envelope import compute_envelope, _is_inverted_hammer

logger = logging.getLogger(__name__)

INSTRUMENTS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CHF": "USDCHF=X",
    "USD/CAD": "USDCAD=X",
    "NZD/USD": "NZDUSD=X",
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD",
    "Gold (XAU)": "GC=F",
    "Silver (XAG)": "SI=F",
}

NW_BANDWIDTH = 8.0
NW_MULTIPLIER = 3.0
NW_ATR_PERIOD = 14


def fetch_data(symbol: str, period: str = "30d") -> pd.DataFrame | None:
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval="15m")
        if df is None or df.empty:
            return None
        return df
    except Exception as e:
        logger.error("Error fetching %s: %s", symbol, e)
        return None


def run_backtest(days: int = 30) -> list[dict]:
    """
    Walk through every 15-min candle over the last N days.
    Find all Inverted Hammers at NW Envelope bands.
    Track outcome: price move after 4, 8, 16 candles (1h, 2h, 4h).
    """
    period = f"{days}d"
    # Yahoo caps intraday at 60 days
    if days > 60:
        days = 60
        period = "60d"

    all_signals: list[dict] = []

    logger.info("BACKTEST: Scanning %d instruments over last %d days", len(INSTRUMENTS), days)

    for name, ticker in INSTRUMENTS.items():
        df = fetch_data(ticker, period=period)
        if df is None or len(df) < 50:
            logger.warning("Skipping %s — not enough data", name)
            continue

        envelope_df = compute_envelope(
            df,
            bandwidth=NW_BANDWIDTH,
            multiplier=NW_MULTIPLIER,
            atr_period=NW_ATR_PERIOD,
        )

        # Walk through every candle (skip first 20 for NW warmup)
        for i in range(20, len(envelope_df)):
            row = envelope_df.iloc[i]

            if pd.isna(row["nw_upper"]) or pd.isna(row["nw_lower"]) or pd.isna(row["atr"]):
                continue

            hammer = _is_inverted_hammer(row["Open"], row["High"], row["Low"], row["Close"])
            if not hammer:
                continue

            atr_val = row["atr"]
            if atr_val == 0:
                continue

            close = row["Close"]
            lower = row["nw_lower"]
            upper = row["nw_upper"]
            mid = row["nw_mid"]
            dist_to_lower = close - lower
            dist_to_upper = upper - close

            signal = None

            if close <= lower or (0 < dist_to_lower <= 0.5 * atr_val):
                signal = {
                    "direction": "BUY",
                    "band": "LOWER",
                }
            elif close >= upper or (0 < dist_to_upper <= 0.5 * atr_val):
                signal = {
                    "direction": "SELL",
                    "band": "UPPER",
                }

            if not signal:
                continue

            # Calculate outcome after signal
            entry_price = close
            outcome = {"after_1h": None, "after_2h": None, "after_4h": None, "result": "PENDING"}

            for label, offset in [("after_1h", 4), ("after_2h", 8), ("after_4h", 16)]:
                if i + offset < len(envelope_df):
                    future_close = envelope_df.iloc[i + offset]["Close"]
                    if signal["direction"] == "BUY":
                        move = future_close - entry_price
                    else:
                        move = entry_price - future_close
                    outcome[label] = round(move, 5)

            # Determine win/loss based on 2h outcome
            if outcome["after_2h"] is not None:
                outcome["result"] = "WIN" if outcome["after_2h"] > 0 else "LOSS"

            timestamp = row.name
            date_str = timestamp.strftime("%Y-%m-%d %H:%M") if hasattr(timestamp, "strftime") else str(timestamp)

            all_signals.append({
                "instrument": name,
                "ticker": ticker,
                "date": date_str,
                "direction": signal["direction"],
                "band": signal["band"],
                "entry": round(entry_price, 5),
                "lower_band": round(lower, 5),
                "upper_band": round(upper, 5),
                "atr": round(atr_val, 5),
                **outcome,
            })

    all_signals.sort(key=lambda x: x["date"], reverse=True)

    # Summary stats
    total = len(all_signals)
    wins = sum(1 for s in all_signals if s["result"] == "WIN")
    losses = sum(1 for s in all_signals if s["result"] == "LOSS")
    win_rate = round(wins / (wins + losses) * 100, 1) if (wins + losses) > 0 else 0

    logger.info("BACKTEST COMPLETE: %d signals, %d wins, %d losses, %.1f%% win rate", total, wins, losses, win_rate)

    return all_signals


def print_backtest(signals: list[dict]):
    """Pretty-print backtest results."""
    if not signals:
        print("\nNo hammer-at-band signals found in the backtest period.")
        return

    total = len(signals)
    wins = sum(1 for s in signals if s["result"] == "WIN")
    losses = sum(1 for s in signals if s["result"] == "LOSS")
    pending = sum(1 for s in signals if s["result"] == "PENDING")
    win_rate = round(wins / (wins + losses) * 100, 1) if (wins + losses) > 0 else 0

    buys = [s for s in signals if s["direction"] == "BUY"]
    sells = [s for s in signals if s["direction"] == "SELL"]

    print(f"\n{'=' * 70}")
    print(f"  FOREX BACKTEST — Hammer at NW Band (15min)")
    print(f"{'=' * 70}")
    print(f"  Total signals : {total}")
    print(f"  BUY signals   : {len(buys)}  (hammer at lower band)")
    print(f"  SELL signals  : {len(sells)}  (hammer at upper band)")
    print(f"  Wins (2h)     : {wins}")
    print(f"  Losses (2h)   : {losses}")
    print(f"  Win Rate      : {win_rate}%")
    print(f"{'=' * 70}\n")

    print(f"  {'Date':<18s} {'Instrument':<14s} {'Dir':<6s} {'Band':<7s} {'Entry':<12s} {'1h':<10s} {'2h':<10s} {'4h':<10s} {'Result'}")
    print(f"  {'─' * 105}")

    for s in signals:
        after_1h = f"{s['after_1h']:+.5f}" if s['after_1h'] is not None else "—"
        after_2h = f"{s['after_2h']:+.5f}" if s['after_2h'] is not None else "—"
        after_4h = f"{s['after_4h']:+.5f}" if s['after_4h'] is not None else "—"
        result_icon = "WIN" if s["result"] == "WIN" else ("LOSS" if s["result"] == "LOSS" else "—")

        print(f"  {s['date']:<18s} {s['instrument']:<14s} {s['direction']:<6s} {s['band']:<7s} {s['entry']:<12} {after_1h:<10s} {after_2h:<10s} {after_4h:<10s} {result_icon}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
    results = run_backtest(30)
    print_backtest(results)
