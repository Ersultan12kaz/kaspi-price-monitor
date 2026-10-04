# Kaspi Price Monitor

Tracks competitor prices for products on **Kaspi.kz** (Kazakhstan's largest marketplace) and sends a
Telegram alert when something important changes. Built for sellers who are tired of checking prices
by hand.

Pure Python standard library — no third-party runtime dependencies.

## What it detects

- Lowest price dropped or rose (with a configurable threshold, e.g. ignore moves under 50 ₸)
- Number of sellers changed (a new competitor appeared or one left)
- **Your shop lost or won first place** by price
- Product went out of stock / came back

Every check is stored in SQLite, and the full history can be exported to CSV (opens correctly in Excel).

## Example alert

```
📈 Kaspi price monitor

• Тестораскаточная машина DHH-220: lowest price fell 64 324 ₸ → 63 990 ₸ (DAMIR)
• Тестораскаточная машина DHH-220: sellers 20 → 21
• Пароочиститель SE8620: My Shop is no longer the cheapest (now #2), leader CyberMarket at 30 097 ₸
```

## Usage

```bash
cp config.example.toml config.toml     # list product IDs, optionally your shop name
python3 -m monitor check               # one snapshot of every product
python3 -m monitor run --every 30      # keep checking every 30 minutes
python3 -m monitor report report.csv   # export history
```

Telegram alerts (optional): create a bot with @BotFather and set

```bash
export TELEGRAM_BOT_TOKEN=...
export TELEGRAM_CHAT_ID=...
```

Without them, alerts are printed to the console.

## Configuration

```toml
my_shop = "My Shop"        # enables first-place alerts
min_price_delta = 50       # ignore smaller price moves
city_id = "750000000"      # Almaty

[[products]]
id = "114273757"           # number at the end of the product URL
```

## Project structure

```
monitor/kaspi.py     fetch and parse offers for a product
monitor/changes.py   compare snapshots and produce alerts (pure, unit-tested)
monitor/storage.py   SQLite history
monitor/notify.py    Telegram notifications
monitor/__main__.py  CLI: check / run / report
tests/               pytest suite
```

## Tests

```bash
python3 -m venv .venv && .venv/bin/pip install pytest
.venv/bin/python -m pytest
```

## Notes

The tool reads the same public offer data that a product page shows to any visitor, waits between
requests, and retries politely on errors. Please respect Kaspi's terms of use and keep check
intervals reasonable.
