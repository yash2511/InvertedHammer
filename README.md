# Inverted Hammer Scanner

Daily stock scanner that detects **Inverted Hammer** candlestick patterns and sends alerts via Telegram by 3 PM.

```
    ┃   ← long upper shadow (≥ 2× body)
    ┣┫  ← small real body near the low
    ╹   ← little or no lower shadow
```

The Inverted Hammer appears after a downtrend and signals a potential **bullish reversal**.

---

## Quick Start

### 1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Telegram bot

1. Message **@BotFather** on Telegram → `/newbot` → copy the **bot token**
2. Message **@userinfobot** on Telegram → copy your **chat ID**
3. Create your `.env` file:

```bash
cp .env.example .env
# Edit .env with your token and chat ID
```

### 3. Run

**One-time scan (test immediately):**

```bash
python main.py --now
```

**Scheduled daily scan (runs Mon–Fri at configured time):**

```bash
python main.py
```

---

## Configuration

All settings live in `.env`:

| Variable             | Default | Description                          |
|----------------------|---------|--------------------------------------|
| `TELEGRAM_BOT_TOKEN` | —       | Bot token from @BotFather            |
| `TELEGRAM_CHAT_ID`   | —       | Your Telegram chat ID                |
| `SCAN_TIME`          | `14:45` | When to run the scan (24h format)    |
| `MARKET`             | `NSE`   | `NSE` for Indian stocks, `US` for US |

---

## Project Structure

```
InvertedHammer/
├── main.py          # Entry point — scheduler + CLI
├── scanner.py       # Fetches OHLC data, runs pattern detection
├── patterns.py      # Inverted Hammer detection logic
├── notifier.py      # Telegram message formatting & sending
├── config.py        # Configuration & stock lists
├── requirements.txt
├── .env.example
└── README.md
```

---

## How Detection Works

A candle is flagged as an Inverted Hammer when **all** conditions are met:

1. **Upper shadow ≥ 2× the real body** — long upper wick
2. **Lower shadow ≤ 25% of the body** — nearly no lower wick
3. **Body sits in the lower third** of the full candle range
4. **Prior 3-day trend is bearish** — closes were declining

---

## Extending

- **Add more stocks**: Edit the `NSE_STOCKS` or `US_STOCKS` lists in `config.py`, or load from a CSV.
- **Add more patterns**: Create new detection functions in `patterns.py` and call them from `scanner.py`.
- **Run on a server**: Use `nohup python main.py &`, a systemd service, or deploy to a cloud VM / Raspberry Pi.
