"""Client for Kaspi.kz public product-offer data (the same JSON the product page loads)."""

import json
import time
import urllib.request
from dataclasses import dataclass

OFFERS_URL = "https://kaspi.kz/yml/offer-view/offers/{product_id}"
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (price-monitor)",
    "Referer": "https://kaspi.kz/shop/",
}


@dataclass(frozen=True)
class Offer:
    merchant: str
    price: int
    merchant_reviews: int


@dataclass(frozen=True)
class Snapshot:
    product_id: str
    title: str
    offers: list[Offer]

    @property
    def min_price(self) -> int | None:
        return min((o.price for o in self.offers), default=None)

    @property
    def sellers(self) -> int:
        return len(self.offers)

    @property
    def cheapest_merchant(self) -> str | None:
        return min(self.offers, key=lambda o: o.price).merchant if self.offers else None

    def position_of(self, merchant: str) -> int | None:
        """1-based place of `merchant` when offers are sorted by price, or None if absent."""
        ranked = sorted(self.offers, key=lambda o: o.price)
        for i, offer in enumerate(ranked, start=1):
            if offer.merchant.casefold() == merchant.casefold():
                return i
        return None


def parse_offers(product_id: str, payload: dict) -> Snapshot:
    offers = [
        Offer(
            merchant=o.get("merchantName", "?"),
            price=int(o["price"]),
            merchant_reviews=int(o.get("merchantReviewsQuantity") or 0),
        )
        for o in payload.get("offers", [])
        if o.get("price") is not None
    ]
    title = next((o.get("title") for o in payload.get("offers", []) if o.get("title")), product_id)
    return Snapshot(product_id=product_id, title=title, offers=offers)


def fetch_snapshot(product_id: str, city_id: str = "750000000", retries: int = 3) -> Snapshot:
    body = json.dumps(
        {
            "cityId": city_id,
            "id": product_id,
            "merchantUID": [],
            "limit": 64,
            "page": 0,
            "sortOption": "PRICE",
            "installationId": "-1",
        }
    ).encode()
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                OFFERS_URL.format(product_id=product_id), data=body, headers=HEADERS, method="POST"
            )
            with urllib.request.urlopen(req, timeout=25) as resp:
                return parse_offers(product_id, json.loads(resp.read()))
        except Exception as exc:  # network errors, rate limits
            last_error = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Could not fetch product {product_id}: {last_error}")
