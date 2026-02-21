"""
Stock scanner — fetches daily OHLC data and runs the Inverted Hammer detector.
"""

import logging
from datetime import datetime, timedelta

import yfinance as yf
import pandas as pd

from patterns import detect_inverted_hammer, detect_inverted_hammer_history, scan_dataframe
from config import get_stock_list

logger = logging.getLogger(__name__)


def fetch_ohlc(symbol: str, period: str = "1mo") -> pd.DataFrame | None:
    """Download daily OHLC for a symbol. Returns None on failure."""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval="1d")
        if df is None or df.empty:
            logger.warning("No data for %s", symbol)
            return None
        return df
    except Exception as e:
        logger.error("Error fetching %s: %s", symbol, e)
        return None


def run_scan() -> list[dict]:
    """
    Scan all configured stocks for the Inverted Hammer pattern.
    Returns a list of dicts with matched stock details.
    """
    stocks = get_stock_list()
    matches: list[dict] = []

    logger.info("Starting scan of %d stocks at %s", len(stocks), datetime.now().strftime("%H:%M:%S"))

    for symbol in stocks:
        df = fetch_ohlc(symbol)
        if df is None:
            continue

        if detect_inverted_hammer(df):
            info = scan_dataframe(df)
            info["symbol"] = symbol
            matches.append(info)
            logger.info("MATCH: %s — %s", symbol, info)

    logger.info("Scan complete. %d match(es) found.", len(matches))
    return matches


def run_history_scan(days: int = 15) -> list[dict]:
    """
    Scan all configured stocks over the last N days.
    Returns a list of dicts with symbol, date, and candle details for each match.
    """
    stocks = get_stock_list()
    all_matches: list[dict] = []

    logger.info("Starting HISTORY scan (%d days) of %d stocks at %s",
                days, len(stocks), datetime.now().strftime("%H:%M:%S"))

    for symbol in stocks:
        df = fetch_ohlc(symbol, period="3mo")
        if df is None:
            continue

        hits = detect_inverted_hammer_history(df, lookback_days=days)
        for h in hits:
            h["symbol"] = symbol
            all_matches.append(h)
            logger.info("HISTORY MATCH: %s on %s", symbol, h["date"])

    all_matches.sort(key=lambda x: x["date"], reverse=True)
    logger.info("History scan complete. %d match(es) found.", len(all_matches))
    return all_matches


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
    results = run_scan()
    if results:
        print("\n=== Inverted Hammer Detected ===")
        for r in results:
            print(f"  {r['symbol']:20s}  Date: {r['date']}  Close: {r['close']}")
    else:
        print("\nNo Inverted Hammer patterns found today.")
