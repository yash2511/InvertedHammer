import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
SCAN_TIME = os.getenv("SCAN_TIME", "14:45")
MARKET = os.getenv("MARKET", "NSE").upper()

# Nifty 500 representative subset — expand as needed.
# Full Nifty 500 list can be loaded from a CSV; this covers Nifty 50 + key mid-caps.
NSE_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS", "ITC.NS",
    "LT.NS", "AXISBANK.NS", "BAJFINANCE.NS", "ASIANPAINT.NS", "MARUTI.NS",
    "HCLTECH.NS", "SUNPHARMA.NS", "TITAN.NS", "ULTRACEMCO.NS", "NESTLEIND.NS",
    "WIPRO.NS", "BAJAJFINSV.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS",
    "M&M.NS", "TATAMOTORS.NS", "ADANIENT.NS", "ADANIPORTS.NS", "COALINDIA.NS",
    "JSWSTEEL.NS", "TATASTEEL.NS", "TECHM.NS", "HDFCLIFE.NS", "SBILIFE.NS",
    "BRITANNIA.NS", "GRASIM.NS", "INDUSINDBK.NS", "CIPLA.NS", "DRREDDY.NS",
    "EICHERMOT.NS", "DIVISLAB.NS", "BPCL.NS", "APOLLOHOSP.NS", "TATACONSUM.NS",
    "HEROMOTOCO.NS", "UPL.NS", "DABUR.NS", "PIDILITIND.NS", "HAVELLS.NS",
]

US_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "BRK-B", "JPM", "V",
    "JNJ", "WMT", "PG", "MA", "UNH",
    "HD", "DIS", "BAC", "ADBE", "CRM",
    "NFLX", "CSCO", "PFE", "TMO", "ABT",
    "INTC", "AMD", "QCOM", "TXN", "AVGO",
]

def get_stock_list():
    if MARKET == "US":
        return US_STOCKS
    return NSE_STOCKS
