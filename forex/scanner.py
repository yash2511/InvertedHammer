"""
Forex / Crypto / Commodities Scanner
NW Envelope + Inverted Hammer on 15-minute charts.
"""

import logging
from datetime import datetime

import yfinance as yf
import pandas as pd

from forex.nw_envelope import compute_envelope, detect_signals

logger = logging.getLogger(__name__)

INSTRUMENTS = {
    # Forex
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CHF": "USDCHF=X",
    "USD/CAD": "USDCAD=X",
    "NZD/USD": "NZDUSD=X",

    # Crypto
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD",
    "USDT/USD": "USDT-USD",

    # Commodities
    "Gold (XAU)": "GC=F",
    "Silver (XAG)": "SI=F",
}

NW_BANDWIDTH = 8.0
NW_MULTIPLIER = 3.0
NW_ATR_PERIOD = 14


def fetch_15min(symbol: str, period: str = "5d") -> pd.DataFrame | None:
    """Download 15-minute OHLC data."""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval="15m")
        if df is None or df.empty:
            logger.warning("No data for %s", symbol)
            return None
        return df
    except Exception as e:
        logger.error("Error fetching %s: %s", symbol, e)
        return None


def run_nw_scan() -> list[dict]:
    """Scan all instruments on 15-min chart with NW Envelope + Hammer detection."""
    all_signals: list[dict] = []

    logger.info(
        "FOREX: Starting NW Envelope scan of %d instruments at %s",
        len(INSTRUMENTS),
        datetime.now().strftime("%H:%M:%S"),
    )

    for name, ticker in INSTRUMENTS.items():
        df = fetch_15min(ticker)
        if df is None or len(df) < 30:
            continue

        envelope_df = compute_envelope(
            df,
            bandwidth=NW_BANDWIDTH,
            multiplier=NW_MULTIPLIER,
            atr_period=NW_ATR_PERIOD,
        )

        signals = detect_signals(envelope_df)

        for sig in signals:
            sig["instrument"] = name
            sig["ticker"] = ticker
            sig["time"] = str(envelope_df.index[-1])
            all_signals.append(sig)
            logger.info("FOREX SIGNAL: %s %s — %s", sig["type"], name, sig["reason"])

    logger.info("FOREX scan complete. %d signal(s) found.", len(all_signals))
    return all_signals
