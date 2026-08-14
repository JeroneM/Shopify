"""Pull disputes from every configured Shopify store into one JSON payload.

    python fetch_chargebacks.py                 # every store found in .env
    python fetch_chargebacks.py MARY LYN        # only these stores
    python fetch_chargebacks.py --since 2026-01-01
    python fetch_chargebacks.py --no-orders     # skip per-order enrichment

Writes data/chargebacks.json, which build_dashboard.py renders.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from chargeback_model import build_payload, normalize
from shopify_client import load_stores

OUTPUT_PATH = os.path.join("data", "chargebacks.json")
ORDER_FIELDS = "id,name,order_number,email,customer,created_at,total_price,currency"


def fetch_store(store, since: str | None, enrich_orders: bool, now: datetime) -> tuple[list[dict], str | None]:
    try:
        disputes = store.disputes(initiated_at=since)
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}"

    order_cache: dict[int, dict | None] = {}
    rows = []
    for dispute in disputes:
        order = None
        order_id = dispute.get("order_id")
        if enrich_orders and order_id:
            if order_id not in order_cache:
                try:
                    order_cache[order_id] = store.order(order_id, fields=ORDER_FIELDS)
                except Exception:
                    # A dispute can outlive its order (archived/deleted); the row
                    # is still worth reporting without the customer columns.
                    order_cache[order_id] = None
            order = order_cache[order_id]
        rows.append(normalize(dispute, store.name, store.label, order, now))
    return rows, None


def main() -> int:
    parser = argparse.ArgumentParser(description="Consolidate Shopify chargebacks across stores.")
    parser.add_argument("stores", nargs="*", help="Store keys to pull (default: all configured)")
    parser.add_argument("--since", help="Only disputes initiated on/after this date (YYYY-MM-DD)")
    parser.add_argument("--no-orders", action="store_true", help="Skip per-order lookups (faster, no customer names)")
    parser.add_argument("--out", default=OUTPUT_PATH, help=f"Output path (default: {OUTPUT_PATH})")
    args = parser.parse_args()

    stores = load_stores([key.upper() for key in args.stores] or None)
    if not stores:
        print(
            "No stores configured. Add <KEY>_SHOPIFY_DOMAIN and <KEY>_SHOPIFY_ACCESS_TOKEN\n"
            "to .env for each store - see .env.example.",
            file=sys.stderr,
        )
        return 1

    now = datetime.now(timezone.utc)
    all_rows: list[dict] = []
    store_meta: list[dict] = []

    for store in stores:
        rows, error = fetch_store(store, args.since, not args.no_orders, now)
        all_rows.extend(rows)
        store_meta.append(
            {"key": store.name, "label": store.label, "domain": store.domain, "fetch_error": error}
        )
        print(f"[{store.name}] {len(rows)} disputes" + (f" - FAILED: {error}" if error else ""))

    payload = build_payload(
        all_rows,
        store_meta,
        now,
        meta={
            "source": "shopify_admin_api",
            "api_version": "2024-01",
            "since": args.since,
            "orders_enriched": not args.no_orders,
        },
    )

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as handle:
        json.dump(payload, handle, indent=2)
    print(f"\n{len(all_rows)} disputes from {len(stores)} store(s) written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
