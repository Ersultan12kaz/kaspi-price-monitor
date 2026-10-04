"""SQLite history of snapshots."""

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from monitor.kaspi import Snapshot

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id  TEXT    NOT NULL,
    title       TEXT    NOT NULL,
    taken_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    min_price   INTEGER,
    sellers     INTEGER NOT NULL,
    cheapest    TEXT,
    my_position INTEGER
);
CREATE INDEX IF NOT EXISTS idx_snap_product ON snapshots(product_id, id);
"""


@dataclass(frozen=True)
class StoredSnapshot:
    product_id: str
    title: str
    taken_at: str
    min_price: int | None
    sellers: int
    cheapest: str | None
    my_position: int | None


class Storage:
    def __init__(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    def last(self, product_id: str) -> StoredSnapshot | None:
        row = self.conn.execute(
            "SELECT product_id, title, taken_at, min_price, sellers, cheapest, my_position"
            " FROM snapshots WHERE product_id = ? ORDER BY id DESC LIMIT 1",
            (product_id,),
        ).fetchone()
        return StoredSnapshot(**dict(row)) if row else None

    def save(self, snap: Snapshot, my_position: int | None) -> None:
        self.conn.execute(
            "INSERT INTO snapshots (product_id, title, min_price, sellers, cheapest, my_position)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (snap.product_id, snap.title, snap.min_price, snap.sellers, snap.cheapest_merchant, my_position),
        )
        self.conn.commit()

    def history(self) -> list[StoredSnapshot]:
        rows = self.conn.execute(
            "SELECT product_id, title, taken_at, min_price, sellers, cheapest, my_position"
            " FROM snapshots ORDER BY product_id, id"
        ).fetchall()
        return [StoredSnapshot(**dict(r)) for r in rows]
