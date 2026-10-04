from monitor.changes import detect_changes, fmt
from monitor.kaspi import parse_offers
from monitor.storage import Storage, StoredSnapshot

PAYLOAD = {
    "offers": [
        {"merchantName": "Shop B", "price": 30100.0, "merchantReviewsQuantity": 501, "title": "Steam cleaner"},
        {"merchantName": "Shop A", "price": 30097.0, "merchantReviewsQuantity": 605, "title": "Steam cleaner"},
        {"merchantName": "My Shop", "price": 31500.0, "merchantReviewsQuantity": None, "title": "Steam cleaner"},
    ]
}


def stored(min_price, sellers, my_position=None):
    return StoredSnapshot("1", "Steam cleaner", "2026-10-04 10:00:00", min_price, sellers, "Shop A", my_position)


def test_parse_offers():
    snap = parse_offers("1", PAYLOAD)
    assert snap.title == "Steam cleaner"
    assert snap.min_price == 30097
    assert snap.sellers == 3
    assert snap.cheapest_merchant == "Shop A"
    assert snap.position_of("my shop") == 3
    assert snap.position_of("Nobody") is None


def test_first_snapshot_has_no_changes():
    assert detect_changes(None, parse_offers("1", PAYLOAD)) == []


def test_price_drop_and_seller_change():
    kinds = [c.kind for c in detect_changes(stored(31000, 2), parse_offers("1", PAYLOAD))]
    assert kinds == ["price_drop", "sellers_change"]


def test_small_moves_ignored():
    assert detect_changes(stored(30100, 3), parse_offers("1", PAYLOAD), min_price_delta=50) == []


def test_price_rise():
    kinds = [c.kind for c in detect_changes(stored(29000, 3), parse_offers("1", PAYLOAD))]
    assert kinds == ["price_rise"]


def test_lost_and_won_first_place():
    cur = parse_offers("1", PAYLOAD)
    lost = detect_changes(stored(30097, 3, my_position=1), cur, my_shop="My Shop")
    assert [c.kind for c in lost] == ["lost_first_place"]
    assert "now #3" in lost[0].message

    cheapest = parse_offers("1", {"offers": PAYLOAD["offers"][:2] + [{"merchantName": "My Shop", "price": 29000}]})
    won = detect_changes(stored(30097, 3, my_position=2), cheapest, my_shop="My Shop")
    assert "won_first_place" in [c.kind for c in won]


def test_stock_changes():
    empty = parse_offers("1", {"offers": []})
    assert [c.kind for c in detect_changes(stored(30097, 3), empty)] == ["out_of_stock"]
    assert [c.kind for c in detect_changes(stored(None, 0), parse_offers("1", PAYLOAD))] == ["back_in_stock"]


def test_storage_roundtrip(tmp_path):
    db = Storage(str(tmp_path / "h.db"))
    snap = parse_offers("1", PAYLOAD)
    db.save(snap, my_position=3)
    last = db.last("1")
    assert (last.min_price, last.sellers, last.cheapest, last.my_position) == (30097, 3, "Shop A", 3)
    assert len(db.history()) == 1
    db.close()


def test_fmt():
    assert fmt(30097) == "30 097 ₸"
    assert fmt(None) == "—"
