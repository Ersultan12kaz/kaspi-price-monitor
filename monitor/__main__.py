"""CLI: python -m monitor check | run --every 30 | report out.csv"""

import argparse
import csv
import logging
import os
import sys
import time
import tomllib
from pathlib import Path

from monitor.changes import detect_changes, fmt
from monitor.kaspi import fetch_snapshot
from monitor.notify import Notifier
from monitor.storage import Storage

log = logging.getLogger("monitor")


def load_config(path: str) -> dict:
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    if not cfg.get("products"):
        raise SystemExit(f"No [[products]] in {path}")
    return cfg


def check(cfg: dict, storage: Storage, notifier: Notifier) -> int:
    """Take one snapshot of every product. Returns the number of alerts sent."""
    my_shop = cfg.get("my_shop") or None
    min_delta = int(cfg.get("min_price_delta", 1))
    city = str(cfg.get("city_id", "750000000"))
    alerts = []
    for product in cfg["products"]:
        pid = str(product["id"])
        try:
            snap = fetch_snapshot(pid, city_id=city)
        except RuntimeError as exc:
            log.error("%s", exc)
            continue
        prev = storage.last(pid)
        alerts += detect_changes(prev, snap, my_shop=my_shop, min_price_delta=min_delta)
        storage.save(snap, snap.position_of(my_shop) if my_shop else None)
        log.info("%-50s min %-12s sellers %d", snap.title[:50], fmt(snap.min_price), snap.sellers)
        time.sleep(1)  # be polite to the site
    if alerts:
        notifier.send("📈 Kaspi price monitor\n\n" + "\n".join(f"• {a.message}" for a in alerts))
    return len(alerts)


def report(storage: Storage, out: str) -> None:
    rows = storage.history()
    with open(out, "w", newline="", encoding="utf-8-sig") as f:  # BOM so Excel opens UTF-8 correctly
        w = csv.writer(f)
        w.writerow(["product_id", "title", "taken_at_utc", "min_price", "sellers", "cheapest", "my_position"])
        for r in rows:
            w.writerow([r.product_id, r.title, r.taken_at, r.min_price, r.sellers, r.cheapest, r.my_position])
    print(f"Wrote {len(rows)} rows to {out}")


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser(prog="monitor", description="Track Kaspi.kz prices and competitors")
    p.add_argument("--config", default="config.toml")
    p.add_argument("--db", default="data/history.db")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="take one snapshot now")
    run = sub.add_parser("run", help="check repeatedly")
    run.add_argument("--every", type=int, default=30, help="minutes between checks")
    rep = sub.add_parser("report", help="export history to CSV")
    rep.add_argument("out", nargs="?", default="report.csv")
    args = p.parse_args(argv)

    storage = Storage(args.db)
    try:
        if args.cmd == "report":
            report(storage, args.out)
            return
        cfg = load_config(args.config)
        notifier = Notifier(os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID"))
        if not notifier.enabled:
            log.info("Telegram is not configured; alerts will be printed")
        if args.cmd == "check":
            check(cfg, storage, notifier)
        else:
            while True:
                check(cfg, storage, notifier)
                time.sleep(args.every * 60)
    except KeyboardInterrupt:
        sys.exit(0)
    finally:
        storage.close()


if __name__ == "__main__":
    main()
