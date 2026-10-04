"""Detect meaningful changes between the previous and the current snapshot."""

from dataclasses import dataclass

from monitor.kaspi import Snapshot
from monitor.storage import StoredSnapshot


@dataclass(frozen=True)
class Change:
    kind: str  # price_drop | price_rise | sellers_change | lost_first_place | won_first_place | out_of_stock | back_in_stock
    message: str


def detect_changes(
    prev: StoredSnapshot | None,
    cur: Snapshot,
    my_shop: str | None = None,
    min_price_delta: int = 1,
) -> list[Change]:
    if prev is None:
        return []

    changes: list[Change] = []
    title = cur.title

    if prev.min_price is not None and cur.min_price is None:
        changes.append(Change("out_of_stock", f"{title}: no sellers left"))
        return changes
    if prev.min_price is None and cur.min_price is not None:
        changes.append(Change("back_in_stock", f"{title}: back in stock from {fmt(cur.min_price)}"))
        return changes

    if prev.min_price is not None and cur.min_price is not None:
        delta = cur.min_price - prev.min_price
        if delta <= -min_price_delta:
            changes.append(Change(
                "price_drop",
                f"{title}: lowest price fell {fmt(prev.min_price)} → {fmt(cur.min_price)} ({cur.cheapest_merchant})",
            ))
        elif delta >= min_price_delta:
            changes.append(Change(
                "price_rise",
                f"{title}: lowest price rose {fmt(prev.min_price)} → {fmt(cur.min_price)}",
            ))

    if cur.sellers != prev.sellers:
        changes.append(Change("sellers_change", f"{title}: sellers {prev.sellers} → {cur.sellers}"))

    if my_shop:
        now_pos = cur.position_of(my_shop)
        if prev.my_position == 1 and now_pos != 1:
            changes.append(Change(
                "lost_first_place",
                f"{title}: {my_shop} is no longer the cheapest (now #{now_pos or '—'}), "
                f"leader {cur.cheapest_merchant} at {fmt(cur.min_price)}",
            ))
        elif prev.my_position != 1 and now_pos == 1:
            changes.append(Change("won_first_place", f"{title}: {my_shop} is now the cheapest"))

    return changes


def fmt(price: int | None) -> str:
    return "—" if price is None else f"{price:,} ₸".replace(",", " ")
