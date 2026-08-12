import csv
import json
import os
from datetime import datetime, timezone

from shopify_client import ShopifyStore

STORE_KEYS = ["MARY", "LYN", "MAGIE"]
REPLACEMENT_TAG = "replacement"
STATE_PATH = "replacement_sync_state.json"
CSV_PATH = "replacement_orders_export.csv"
CSV_HEADER = [
    "store", "order_id", "order_number", "name", "customer_email", "customer_name",
    "created_at", "total_price", "currency", "financial_status", "fulfillment_status",
    "tracking_number", "delivery_status", "tags", "note",
]


def has_tag(order: dict, tag: str) -> bool:
    raw = order.get("tags", "")
    return tag.lower() in {t.strip().lower() for t in raw.split(",") if t.strip()}


def tracking_numbers(order: dict) -> str:
    numbers = []
    for f in order.get("fulfillments") or []:
        numbers.extend(f.get("tracking_numbers") or [])
    return "; ".join(numbers)


def delivery_status(order: dict) -> str:
    statuses = [f.get("shipment_status") for f in order.get("fulfillments") or [] if f.get("shipment_status")]
    return "; ".join(statuses)


def order_row(o: dict) -> list:
    customer = o.get("customer") or {}
    customer_name = " ".join(filter(None, [customer.get("first_name"), customer.get("last_name")])).strip()
    return [
        o["_store"], o["id"], o.get("order_number"), o.get("name"),
        o.get("email") or o.get("contact_email"), customer_name, o.get("created_at"),
        o.get("total_price"), o.get("currency"), o.get("financial_status"),
        o.get("fulfillment_status"), tracking_numbers(o), delivery_status(o),
        o.get("tags"), o.get("note"),
    ]


def load_state() -> dict:
    if not os.path.exists(STATE_PATH):
        return {}
    with open(STATE_PATH) as f:
        return json.load(f)


def save_state(state: dict) -> None:
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def existing_order_ids() -> set[str]:
    if not os.path.exists(CSV_PATH):
        return set()
    with open(CSV_PATH, newline="") as f:
        return {row["order_id"] for row in csv.DictReader(f)}


def main() -> None:
    state = load_state()
    seen_ids = existing_order_ids()
    run_started_at = datetime.now(timezone.utc).isoformat()
    new_replacements = []

    for key in STORE_KEYS:
        store = ShopifyStore.from_env(key)
        since = state.get(key)
        try:
            orders = store.orders_all(created_at_min=since)
        except Exception as exc:
            print(f"[{key}] failed to fetch orders: {exc}")
            continue
        for o in orders:
            if has_tag(o, REPLACEMENT_TAG) and str(o["id"]) not in seen_ids:
                o["_store"] = key
                new_replacements.append(o)
        state[key] = run_started_at

    if new_replacements:
        write_header = not os.path.exists(CSV_PATH)
        with open(CSV_PATH, "a", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(CSV_HEADER)
            for o in sorted(new_replacements, key=lambda x: (x["_store"], x["created_at"])):
                writer.writerow(order_row(o))
        print(f"NEW_REPLACEMENTS={len(new_replacements)}")
    else:
        print("NEW_REPLACEMENTS=0")

    save_state(state)


if __name__ == "__main__":
    main()
