"""
NSE Stock Scanner — Inverted Hammer detection on daily charts.
"""

import logging
from datetime import datetime

import yfinance as yf
import pandas as pd

from nse.patterns import detect_inverted_hammer, detect_inverted_hammer_history, scan_dataframe
from config import get_stock_list

logger = logging.getLogger(__name__)


def fetch_ohlc(symbol: str, period: str = "1mo") -> pd.DataFrame | None:
    """Download daily OHLC for a symbol."""
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
    """Scan all configured NSE stocks for the Inverted Hammer pattern."""
    stocks = get_stock_list()
    matches: list[dict] = []

    logger.info("NSE: Starting scan of %d stocks at %s", len(stocks), datetime.now().strftime("%H:%M:%S"))

    for symbol in stocks:
        df = fetch_ohlc(symbol)
        if df is None:
            continue

        if detect_inverted_hammer(df):
            info = scan_dataframe(df)
            info["symbol"] = symbol
            matches.append(info)
            logger.info("NSE MATCH: %s — %s", symbol, info)

    logger.info("NSE scan complete. %d match(es) found.", len(matches))
    return matches


def run_history_scan(days: int = 15) -> list[dict]:
    """Scan all configured NSE stocks over the last N days."""
    stocks = get_stock_list()
    all_matches: list[dict] = []

    logger.info("NSE HISTORY: Scanning %d stocks over last %d days", len(stocks), days)

    for symbol in stocks:
        df = fetch_ohlc(symbol, period="3mo")
        if df is None:
            continue

        hits = detect_inverted_hammer_history(df, lookback_days=days)
        for h in hits:
            h["symbol"] = symbol
            all_matches.append(h)
            logger.info("NSE HISTORY MATCH: %s on %s", symbol, h["date"])

    all_matches.sort(key=lambda x: x["date"], reverse=True)
    logger.info("NSE history scan complete. %d match(es) found.", len(all_matches))
    return all_matches
