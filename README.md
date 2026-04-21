## Binance Futures Testnet Trading Bot (CLI)

Minimal, production-minded Python CLI that places **MARKET**, **LIMIT**, and **STOP (stop-limit)** orders on **Binance USDT‑M Futures Testnet** using signed REST requests.

### Quick Start (Windows / PowerShell)

Clone/open the repo, then from the `trading_bot/` folder:

```bash
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set:

- `BINANCE_FUTURES_TESTNET_API_KEY`
- `BINANCE_FUTURES_TESTNET_API_SECRET`

Then verify the CLI is reachable:

```bash
py -m trading_bot.cli order --help
```

### Environment Variables

The app loads `.env` **deterministically** from the project root (next to `requirements.txt`) if it exists. In production you can omit `.env` and set variables via your environment/secret manager.

Required:

- `BINANCE_FUTURES_TESTNET_API_KEY`
- `BINANCE_FUTURES_TESTNET_API_SECRET`

Optional:

- `BINANCE_FUTURES_TESTNET_BASE_URL` (defaults to `https://testnet.binancefuture.com`)

### CLI Examples

MARKET order (no price allowed):

```bash
py -m trading_bot.cli order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

LIMIT order (price required):

```bash
py -m trading_bot.cli order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 80000
```

STOP (stop-limit) order (both stop price and limit price required):

```bash
py -m trading_bot.cli order --symbol BTCUSDT --side BUY --type STOP --quantity 0.001 --stop-price 70000 --price 70100
```

Dry-run (validates with Binance but does not place an order):

```bash
py -m trading_bot.cli order --dry-run --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Logging

- Logs go to **both** console and `logs/bot.log`.
- Every request attempt and response (success/failure) is logged with timestamps.
- Request signatures are redacted and **API secrets are never logged**.

Tip:

```bash
py -m trading_bot.cli --log-level DEBUG order --help
```

### Project Structure

```text
trading_bot/
  README.md
  requirements.txt
  .env.example
  .gitignore
  logs/                     # created at runtime
    bot.log
  trading_bot/
    __init__.py
    __main__.py             # enables: py -m trading_bot
    cli.py                  # enables: py -m trading_bot.cli
    bot/
      __init__.py
      client.py             # signed REST client (SSL verify enabled)
      env.py                # deterministic .env loader
      exceptions.py
      logging_config.py     # console + rotating file logging
      orders.py
      validators.py         # Decimal-based validation
```

### Notes / Assumptions

- This project targets **USDT‑M Futures testnet** (not Spot).
- Input validation ensures quantity/price/stopPrice are positive numbers (Decimal-based); exchange filters (tickSize/stepSize) are intentionally out of scope for this simplified bot.

