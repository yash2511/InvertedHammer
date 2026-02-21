#!/usr/bin/env python3
"""
Stock & Forex Scanner — Main entry point.

Usage:
    python main.py --nse              # NSE Inverted Hammer scan (today)
    python main.py --nse-history 15   # NSE scan over last 15 days
    python main.py --forex            # Forex scan once (hammer at band)
    python main.py --forex-live       # Forex live monitor — checks every 15 min
    python main.py --all              # Run both NSE + Forex once
    python main.py                    # Start scheduled daily NSE scanner
"""

import argparse
import logging
import time
from datetime import datetime

import schedule

from config import SCAN_TIME, MARKET
from nse.scanner import run_scan as nse_scan, run_history_scan as nse_history
from nse.notifier import send_nse_alert, send_nse_history
from forex.scanner import run_nw_scan
from forex.notifier import send_forex_alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)-14s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")


def job_nse():
    """Run NSE Inverted Hammer scan."""
    logger.info("=" * 50)
    logger.info("NSE scan triggered")
    logger.info("=" * 50)
    matches = nse_scan()
    send_nse_alert(matches)
    logger.info("NSE: %d match(es)", len(matches))


def job_forex():
    """Run Forex scan — only alerts when hammer forms at band."""
    logger.info("─" * 50)
    logger.info("FOREX scan at %s", datetime.now().strftime("%H:%M:%S"))
    logger.info("─" * 50)
    signals = run_nw_scan()
    if signals:
        send_forex_alert(signals)
        for s in signals:
            print(f"  {s['direction']:5s}  {s['instrument']:12s}  Hammer {s['band_position']} {s['band']} band  Close: {s['close']}")
    else:
        logger.info("No hammer at band right now.")


def main():
    parser = argparse.ArgumentParser(description="Stock & Forex Scanner")
    parser.add_argument("--nse", action="store_true", help="Run NSE Inverted Hammer scan now")
    parser.add_argument("--forex", action="store_true", help="Run Forex scan once (hammer at band)")
    parser.add_argument(
        "--forex-live", action="store_true",
        help="Forex live monitor — scans every 15 min, alerts only on hammer at band",
    )
    parser.add_argument("--all", action="store_true", help="Run both NSE + Forex once")
    parser.add_argument(
        "--nse-history", type=int, nargs="?", const=15, metavar="DAYS",
        help="NSE: scan last N days for Inverted Hammer (default: 15)",
    )
    args = parser.parse_args()

    if args.all:
        logger.info("Running ALL scans...")
        job_nse()
        job_forex()
        return

    if args.nse:
        logger.info("Running NSE scan (market: %s)...", MARKET)
        job_nse()
        return

    if args.forex:
        logger.info("Running FOREX scan (one-time)...")
        job_forex()
        return

    if args.forex_live:
        logger.info("=" * 50)
        logger.info("FOREX LIVE MONITOR STARTED")
        logger.info("Checking every 15 minutes for Hammer at NW Band")
        logger.info("Instruments: Forex, BTC, ETH, Gold, Silver")
        logger.info("Alerts ONLY when Inverted Hammer at band")
        logger.info("=" * 50)

        job_forex()  # run immediately on start
        schedule.every(15).minutes.do(job_forex)

        try:
            while True:
                schedule.run_pending()
                time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Forex monitor stopped.")
        return

    if args.nse_history:
        days = args.nse_history
        logger.info("Running NSE history scan — last %d days...", days)
        matches = nse_history(days)
        send_nse_history(matches, days)
        if matches:
            print(f"\n=== NSE Inverted Hammer — Last {days} Days ===")
            for m in matches:
                symbol = m["symbol"].replace(".NS", "")
                print(f"  {symbol:20s}  Date: {m['date']}  Close: {m['close']}  Wick/Body: {m['upper_shadow_to_body']}")
        else:
            print(f"\nNo patterns in the last {days} days.")
        return

    # No flags → scheduled NSE only
    logger.info("NSE Scanner started (scheduled mode)")
    logger.info("Scan time: %s daily (Mon-Fri)", SCAN_TIME)
    logger.info("Waiting...\n")

    schedule.every().monday.at(SCAN_TIME).do(job_nse)
    schedule.every().tuesday.at(SCAN_TIME).do(job_nse)
    schedule.every().wednesday.at(SCAN_TIME).do(job_nse)
    schedule.every().thursday.at(SCAN_TIME).do(job_nse)
    schedule.every().friday.at(SCAN_TIME).do(job_nse)

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("Scanner stopped by user.")


if __name__ == "__main__":
    main()
