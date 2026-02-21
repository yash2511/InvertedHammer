#!/usr/bin/env python3
"""
Inverted Hammer Scanner — Main entry point.

Usage:
    python main.py              # Start the scheduled daily scanner
    python main.py --now        # Run a single scan immediately and exit
"""

import argparse
import logging
import time
from datetime import datetime

import schedule

from config import SCAN_TIME, MARKET
from scanner import run_scan, run_history_scan
from notifier import send_telegram, send_telegram_history

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)-12s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")


def job():
    """Run the scan and send results via Telegram."""
    logger.info("=" * 50)
    logger.info("Scheduled scan triggered")
    logger.info("=" * 50)

    matches = run_scan()
    send_telegram(matches)

    if matches:
        logger.info("Sent %d match(es) to Telegram.", len(matches))
    else:
        logger.info("No patterns found. Notification sent.")


def main():
    parser = argparse.ArgumentParser(description="Inverted Hammer Candlestick Scanner")
    parser.add_argument(
        "--now",
        action="store_true",
        help="Run the scan immediately and exit (no scheduling)",
    )
    parser.add_argument(
        "--history",
        type=int,
        nargs="?",
        const=15,
        metavar="DAYS",
        help="Scan last N days for patterns (default: 15) and send to Telegram",
    )
    args = parser.parse_args()

    if args.history:
        days = args.history
        logger.info("Running history scan — last %d days (market: %s)...", days, MARKET)
        matches = run_history_scan(days)
        send_telegram_history(matches, days)
        if matches:
            print(f"\n=== Inverted Hammer — Last {days} Days ===")
            for m in matches:
                symbol = m["symbol"].replace(".NS", "")
                print(f"  {symbol:20s}  Date: {m['date']}  Close: {m['close']}  Wick/Body: {m['upper_shadow_to_body']}")
        else:
            print(f"\nNo Inverted Hammer patterns in the last {days} days.")
        return

    if args.now:
        logger.info("Running immediate scan (market: %s)...", MARKET)
        job()
        return

    logger.info("Inverted Hammer Scanner started")
    logger.info("Market     : %s", MARKET)
    logger.info("Scan time  : %s daily", SCAN_TIME)
    logger.info("Waiting for scheduled run...\n")

    schedule.every().monday.at(SCAN_TIME).do(job)
    schedule.every().tuesday.at(SCAN_TIME).do(job)
    schedule.every().wednesday.at(SCAN_TIME).do(job)
    schedule.every().thursday.at(SCAN_TIME).do(job)
    schedule.every().friday.at(SCAN_TIME).do(job)

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("Scanner stopped by user.")


if __name__ == "__main__":
    main()
