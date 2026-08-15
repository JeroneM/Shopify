"""Export orders tagged "replacement" for a date range, across every configured store.

Read-only: this script issues GET requests only. It never modifies, fulfils,
cancels, refunds or edits an order.

Usage:
    python replacement_orders_report.py                      # 2026-08-12 .. 2026-08-14
    python replacement_orders_report.py 2026-08-01 2026-08-31
"""

import csv
import sys
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from shopify_client import ShopifyStore

START_DATE = "2026-08-12"
END_DATE = "2026-08-14"

TAG = "replacement"

COLUMNS = [
    "store",
    "order_id",
    "order_number",
    "name",
    "customer_email",
    "customer_name",
    "created_at",
    "total_price",
    "currency",
    "financial_status",
    "fulfillment_status",
    "tags",
    "note",
]

# Ask Shopify for only the fields we export, so the payload stays small.
ORDER_FIELDS = (
    "id,order_number,name,email,customer,created_at,total_price,currency,"
    "financial_status,fulfillment_status,tags,note"
)

OUT_PATH = "replacement_orders_export.csv"


def split_tags(raw: str | None) -> list[str]:
    return [t.strip() for t in (raw or "").split(",") if t.strip()]


def has_tag(order: dict, tag: str) -> bool:
    """Exact tag match, case-insensitive.

    Deliberately not a substring match: neighbouring tags such as
    "size_replacement" or "ai-replacement" are different tags and must not match.
    """
    return tag.casefold() in {t.casefold() for t in split_tags(order.get("tags"))}


def customer_name(order: dict) -> str:
    customer = order.get("customer") or {}
    parts = [customer.get("first_name"), customer.get("last_name")]
    return " ".join(p.strip() for p in parts if p and p.strip())


def customer_email(order: dict) -> str:
    customer = order.get("customer") or {}
    return order.get("email") or customer.get("email") or ""


def fulfillment_status(order: dict) -> str:
    """Shopify leaves fulfillment_status null for a wholly unfulfilled order.

    Spelled out so the column is never an ambiguous blank. Other values pass
    through as Shopify reports them: fulfilled, partial, restocked.
    """
    return order.get("fulfillment_status") or "unfulfilled"


def day_bounds(store_tz: ZoneInfo, start_date: str, end_date: str) -> tuple[str, str]:
    """Inclusive [start 00:00:00, end 23:59:59] in the store's own timezone."""
    start = datetime.combine(datetime.fromisoformat(start_date).date(), time.min, store_tz)
    end = datetime.combine(datetime.fromisoformat(end_date).date(), time.max, store_tz)
    return start.isoformat(), end.isoformat()


def to_row(order: dict, store_key: str) -> list:
    return [
        store_key,
        order.get("id"),
        order.get("order_number"),
        order.get("name"),
        customer_email(order),
        customer_name(order),
        # Kept exactly as Shopify returns it - no reformatting, no timezone shift.
        order.get("created_at"),
        order.get("total_price"),
        order.get("currency"),
        order.get("financial_status"),
        fulfillment_status(order),
        order.get("tags"),
        order.get("note"),
    ]


def main() -> None:
    start_date = sys.argv[1] if len(sys.argv) > 1 else START_DATE
    end_date = sys.argv[2] if len(sys.argv) > 2 else END_DATE

    store_keys = ShopifyStore.keys_from_env()
    if not store_keys:
        sys.exit(
            "No stores configured. Add <KEY>_SHOPIFY_DOMAIN and <KEY>_SHOPIFY_ACCESS_TOKEN "
            "to .env (see .env.example)."
        )

    rows: list[list] = []
    near_miss_tags: dict[str, int] = {}
    failed: list[str] = []

    for key in store_keys:
        store = ShopifyStore.from_env(key)
        try:
            shop = store.shop_info()
            store_tz = ZoneInfo(shop.get("iana_timezone") or "UTC")
            created_min, created_max = day_bounds(store_tz, start_date, end_date)
            orders = store.orders_in_range(created_min, created_max, fields=ORDER_FIELDS)
        except Exception as exc:
            print(f"[{key}] FAILED to fetch orders: {exc}")
            failed.append(key)
            continue

        matched = [o for o in orders if has_tag(o, TAG)]
        for order in matched:
            rows.append(to_row(order, key))

        # Surface look-alike tags so a naming mismatch is visible rather than silent.
        for order in orders:
            for tag in split_tags(order.get("tags")):
                if TAG in tag.casefold() and tag.casefold() != TAG:
                    near_miss_tags[tag] = near_miss_tags.get(tag, 0) + 1

        print(
            f"[{key}] {shop.get('name')} ({shop.get('iana_timezone')}): "
            f"{len(orders)} orders in range, {len(matched)} tagged '{TAG}'"
        )

    rows.sort(key=lambda r: (r[0], str(r[6])))

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        writer.writerows(rows)

    print(f"\n{len(rows)} orders tagged '{TAG}' from {start_date} to {end_date} (inclusive)")
    print(f"Written to {OUT_PATH}")

    if near_miss_tags:
        summary = ", ".join(f"{t} ({n})" for t, n in sorted(near_miss_tags.items()))
        print(f"\nNot included - similar but different tags seen in range: {summary}")
    if failed:
        print(f"\nWARNING: incomplete export, these stores failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
