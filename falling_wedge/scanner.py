"""
Falling Wedge Scanner — NSE weekly charts.
Detects breakout from a falling wedge pattern (bullish signal).
"""

import logging
from datetime import datetime

import yfinance as yf
import pandas as pd

from falling_wedge.patterns import detect_breakout, detect_breakout_history, scan_dataframe
from config import get_stock_list

logger = logging.getLogger(__name__)


def fetch_ohlc(symbol: str, period: str = "1y") -> pd.DataFrame | None:
    """Download weekly OHLC for a symbol.  Default 1y for wedge detection."""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval="1wk")
        if df is None or df.empty:
            logger.warning("No data for %s", symbol)
            return None
        return df
    except Exception as e:
        logger.error("Error fetching %s: %s", symbol, e)
        return None


def run_scan() -> list[dict]:
    """Scan all configured NSE stocks for falling-wedge breakouts on this week's candle."""
    stocks = get_stock_list()
    matches: list[dict] = []

    logger.info("FALLING WEDGE (weekly): Starting scan of %d stocks at %s",
                len(stocks), datetime.now().strftime("%H:%M:%S"))

    for symbol in stocks:
        df = fetch_ohlc(symbol)
        if df is None:
            continue

        if detect_breakout(df):
            info = scan_dataframe(df)
            info["symbol"] = symbol
            matches.append(info)
            logger.info("FALLING WEDGE MATCH: %s — %s", symbol, info)

    logger.info("Falling Wedge scan complete. %d match(es) found.", len(matches))
    return matches


def run_history_scan(weeks: int = 12) -> list[dict]:
    """Scan all configured NSE stocks over the last N weeks for wedge breakouts."""
    stocks = get_stock_list()
    all_matches: list[dict] = []

    logger.info("FALLING WEDGE HISTORY: Scanning %d stocks over last %d weeks",
                len(stocks), weeks)

    for symbol in stocks:
        df = fetch_ohlc(symbol, period="2y")
        if df is None:
            continue

        hits = detect_breakout_history(df, lookback_days=weeks)
        for h in hits:
            h["symbol"] = symbol
            all_matches.append(h)
            logger.info("FALLING WEDGE HISTORY MATCH: %s on %s", symbol, h["date"])

    all_matches.sort(key=lambda x: x["date"], reverse=True)
    logger.info("Falling Wedge history scan complete. %d match(es) found.",
                len(all_matches))
    return all_matches
