#!/usr/bin/env python3
"""
Stock & Forex Scanner — Main entry point.

Usage:
    python main.py --nse-scan           # NSE combined: Hammer + Wedge + Shooting Star
    python main.py --nse                # NSE Inverted Hammer scan (today)
    python main.py --nse-history 15     # NSE Inverted Hammer last 15 days
    python main.py --ss                 # NSE Shooting Star scan (today)
    python main.py --ss-history 30      # NSE Shooting Star last 30 days
    python main.py --fw                 # Falling Wedge breakout scan (today)
    python main.py --fw-history 30      # Falling Wedge breakouts last 30 days
    python main.py --forex              # Forex scan once (hammer at band)
    python main.py --forex-live         # Forex live monitor — every 15 min
    python main.py --forex-backtest 30  # Forex backtest last 30 days
    python main.py --all                # Run all NSE patterns + Forex
    python main.py                      # Start scheduled daily scanner
"""

import argparse
import logging
import time
from datetime import datetime

import schedule

from config import SCAN_TIME, MARKET
from nse.scanner import run_scan as nse_scan, run_history_scan as nse_history
from nse.notifier import send_nse_alert, send_nse_history
from shooting_star.scanner import run_scan as ss_scan, run_history_scan as ss_history
from shooting_star.notifier import send_shooting_star_alert, send_shooting_star_history
from nse.combined import send_combined_alert
from falling_wedge.scanner import run_scan as fw_scan, run_history_scan as fw_history
from forex.scanner import run_nw_scan
from forex.notifier import send_forex_alert
from forex.backtest import run_backtest, print_backtest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)-14s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")


def job_nse():
    """Run NSE Inverted Hammer scan."""
    logger.info("=" * 50)
    logger.info("NSE Inverted Hammer scan triggered")
    logger.info("=" * 50)
    matches = nse_scan()
    send_nse_alert(matches)
    logger.info("NSE Inverted Hammer: %d match(es)", len(matches))


def job_shooting_star():
    """Run NSE Shooting Star scan."""
    logger.info("=" * 50)
    logger.info("NSE Shooting Star scan triggered")
    logger.info("=" * 50)
    matches = ss_scan()
    send_shooting_star_alert(matches)
    logger.info("NSE Shooting Star: %d match(es)", len(matches))


def job_falling_wedge():
    """Run Falling Wedge breakout scan."""
    logger.info("=" * 50)
    logger.info("NSE Falling Wedge scan triggered")
    logger.info("=" * 50)
    matches = fw_scan()
    logger.info("NSE Falling Wedge: %d match(es)", len(matches))
    return matches


def job_nse_combined():
    """Run all NSE patterns and send ONE combined Telegram message."""
    logger.info("=" * 50)
    logger.info("NSE Combined Scan (Inverted Hammer + Falling Wedge + Shooting Star)")
    logger.info("=" * 50)
    hammer_matches = nse_scan()
    wedge_matches = fw_scan()
    star_matches = ss_scan()
    send_combined_alert(hammer_matches, star_matches, wedge_matches)
    logger.info("NSE Combined: %d Inverted Hammer, %d Falling Wedge, %d Shooting Star",
                len(hammer_matches), len(wedge_matches), len(star_matches))


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

    # NSE Combined
    parser.add_argument("--nse-scan", action="store_true",
                        help="NSE combined scan: Inverted Hammer + Shooting Star (single Telegram message)")

    # NSE Inverted Hammer
    parser.add_argument("--nse", action="store_true", help="NSE Inverted Hammer scan (today)")
    parser.add_argument(
        "--nse-history", type=int, nargs="?", const=15, metavar="DAYS",
        help="NSE Inverted Hammer: last N days (default: 15)",
    )

    # Shooting Star
    parser.add_argument("--ss", action="store_true", help="NSE Shooting Star scan (today)")
    parser.add_argument(
        "--ss-history", type=int, nargs="?", const=15, metavar="DAYS",
        help="NSE Shooting Star: last N days (default: 15)",
    )

    # Falling Wedge (weekly candles)
    parser.add_argument("--fw", action="store_true", help="Falling Wedge breakout scan (weekly candle)")
    parser.add_argument(
        "--fw-history", type=int, nargs="?", const=12, metavar="WEEKS",
        help="Falling Wedge breakouts: last N weeks (default: 12)",
    )

    # Forex
    parser.add_argument("--forex", action="store_true", help="Forex scan once (hammer at band)")
    parser.add_argument("--forex-live", action="store_true", help="Forex live monitor — every 15 min")
    parser.add_argument(
        "--forex-backtest", type=int, nargs="?", const=30, metavar="DAYS",
        help="Forex backtest last N days (default: 30)",
    )

    # Combined
    parser.add_argument("--all", action="store_true", help="Run all scans: Inverted Hammer + Shooting Star + Forex")

    args = parser.parse_args()

    # --- All scans ---
    if args.all:
        logger.info("Running ALL scans...")
        job_nse_combined()
        job_forex()
        return

    # --- NSE Combined ---
    if args.nse_scan:
        logger.info("Running NSE combined scan (market: %s)...", MARKET)
        job_nse_combined()
        return

    # --- NSE Inverted Hammer ---
    if args.nse:
        logger.info("Running NSE Inverted Hammer scan (market: %s)...", MARKET)
        job_nse()
        return

    if args.nse_history:
        days = args.nse_history
        logger.info("Running NSE Inverted Hammer history — last %d days...", days)
        matches = nse_history(days)
        send_nse_history(matches, days)
        if matches:
            print(f"\n=== NSE Inverted Hammer — Last {days} Days ===")
            for m in matches:
                symbol = m["symbol"].replace(".NS", "")
                print(f"  {symbol:20s}  Date: {m['date']}  Close: {m['close']}  Wick/Body: {m['upper_shadow_to_body']}")
        else:
            print(f"\nNo Inverted Hammer patterns in the last {days} days.")
        return

    # --- Shooting Star ---
    if args.ss:
        logger.info("Running NSE Shooting Star scan (market: %s)...", MARKET)
        job_shooting_star()
        return

    if args.ss_history:
        days = args.ss_history
        logger.info("Running NSE Shooting Star history — last %d days...", days)
        matches = ss_history(days)
        send_shooting_star_history(matches, days)
        if matches:
            print(f"\n=== NSE Shooting Star — Last {days} Days ===")
            for m in matches:
                symbol = m["symbol"].replace(".NS", "")
                print(f"  {symbol:20s}  Date: {m['date']}  Close: {m['close']}  Wick/Body: {m['upper_shadow_to_body']}")
        else:
            print(f"\nNo Shooting Star patterns in the last {days} days.")
        return

    # --- Falling Wedge (weekly) ---
    if args.fw:
        logger.info("Running Falling Wedge breakout scan — weekly candle (market: %s)...", MARKET)
        matches = fw_scan()
        if matches:
            print(f"\n=== Falling Wedge Breakouts — This Week ===")
            for m in matches:
                symbol = m["symbol"].replace(".NS", "")
                print(f"  {symbol:20s}  Close: {m['close']}  Wedge: {m['wedge_candles']} weeks  Vol: +{m['vol_vs_avg_pct']}%")
        else:
            print("\nNo Falling Wedge breakouts this week.")
        return

    if args.fw_history:
        weeks = args.fw_history
        logger.info("Running Falling Wedge history — last %d weeks...", weeks)
        matches = fw_history(weeks)
        if matches:
            print(f"\n=== Falling Wedge Breakouts — Last {weeks} Weeks ===")
            for m in matches:
                symbol = m["symbol"].replace(".NS", "")
                print(f"  {symbol:20s}  Date: {m['date']}  Close: {m['close']}  Vol: +{m['vol_vs_avg_pct']}%")
        else:
            print(f"\nNo Falling Wedge breakouts in the last {weeks} weeks.")
        return

    # --- Forex ---
    if args.forex:
        logger.info("Running FOREX scan (one-time)...")
        job_forex()
        return

    if args.forex_backtest:
        days = args.forex_backtest
        logger.info("Running FOREX backtest — last %d days...", days)
        results = run_backtest(days)
        print_backtest(results)
        return

    if args.forex_live:
        logger.info("=" * 50)
        logger.info("FOREX LIVE MONITOR STARTED")
        logger.info("Checking every 15 minutes for Hammer at NW Band")
        logger.info("Instruments: Forex, BTC, ETH, Gold, Silver")
        logger.info("Alerts ONLY when Inverted Hammer at band")
        logger.info("=" * 50)
        job_forex()
        schedule.every(15).minutes.do(job_forex)
        try:
            while True:
                schedule.run_pending()
                time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Forex monitor stopped.")
        return

    # --- No flags → scheduled mode (both NSE patterns daily) ---
    logger.info("NSE Scanner started (scheduled mode)")
    logger.info("Inverted Hammer + Falling Wedge + Shooting Star: %s daily (Mon-Fri)", SCAN_TIME)
    logger.info("Waiting...\n")

    schedule.every().monday.at(SCAN_TIME).do(job_nse_combined)
    schedule.every().tuesday.at(SCAN_TIME).do(job_nse_combined)
    schedule.every().wednesday.at(SCAN_TIME).do(job_nse_combined)
    schedule.every().thursday.at(SCAN_TIME).do(job_nse_combined)
    schedule.every().friday.at(SCAN_TIME).do(job_nse_combined)

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("Scanner stopped by user.")


if __name__ == "__main__":
    main()
