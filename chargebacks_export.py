"""Pull every chargeback/dispute from all stores into one file the dashboard reads.

    python chargebacks_export.py                # -> chargebacks.json + chargebacks.csv

One row per Shopify dispute. The dispute ID is the unique key, so an order with
several transactions is never counted more than once - only cases Shopify itself
records as separate disputes become separate rows.
"""

import csv
import json
import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from shopify_client import ShopifyStore

# Display name -> env prefix (MARY_SHOPIFY_DOMAIN, MARY_SHOPIFY_ACCESS_TOKEN, ...)
STORES = {
    "Maggie's Tanks": "MAGIE",
    "Mary's Tanks": "MARY",
    "Lyn's Tanks": "LYN",
    "Simply Elsie": "ELSIE",
}

# Shopify dispute status -> the three statuses the dashboard reports.
STATUS_MAP = {
    "needs_response": "Open",
    "under_review": "Open",
    "warning_needs_response": "Open",
    "warning_under_review": "Open",
    "response_disabled": "Open",  # awaiting the network's decision, nothing to submit
    "won": "Won",
    "warning_closed": "Won",  # inquiry closed without becoming a chargeback
    "lost": "Lost",
    "accepted": "Lost",  # liability accepted, funds gone
    "charge_refunded": "Lost",
    "prevented": "Won",  # blocked by Shopify before it became a chargeback
}

FIELDS = [
    "dispute_id", "store", "created_at", "created_date", "order_number", "order_id",
    "customer", "amount", "currency", "reason", "status", "status_raw", "case_type",
    "outcome_date", "evidence_due_by",
]


def to_local_date(iso: str | None, tz: ZoneInfo) -> str:
    if not iso:
        return ""
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(tz).date().isoformat()


def customer_name(order: dict) -> str:
    customer = order.get("customer") or {}
    name = " ".join(filter(None, [customer.get("first_name"), customer.get("last_name")])).strip()
    if name:
        return name
    address = order.get("billing_address") or order.get("shipping_address") or {}
    return (address.get("name") or customer.get("email") or "").strip()


def collect_store(display_name: str, env_key: str, warnings: list[str]) -> list[dict]:
    store = ShopifyStore.from_env(env_key)
    shop = store.shop_info()
    tz = ZoneInfo(shop.get("iana_timezone") or "UTC")
    disputes = store.disputes()

    seen: dict[str, dict] = {}
    duplicates = 0
    for dispute in disputes:
        dispute_id = str(dispute.get("id") or "")
        if not dispute_id:
            warnings.append(f"{display_name}: dispute with no ID was skipped")
            continue
        if dispute_id in seen:
            duplicates += 1
            continue
        seen[dispute_id] = dispute
    if duplicates:
        warnings.append(f"{display_name}: dropped {duplicates} repeated dispute ID(s) returned by the API")

    order_cache: dict[int, dict] = {}
    rows = []
    for dispute_id, dispute in seen.items():
        order_id = dispute.get("order_id")
        order = {}
        if order_id:
            if order_id not in order_cache:
                try:
                    order_cache[order_id] = store.order(order_id)
                except Exception as exc:
                    order_cache[order_id] = {}
                    warnings.append(f"{display_name}: could not read order {order_id} ({exc})")
            order = order_cache[order_id]

        status_raw = dispute.get("status") or ""
        status = STATUS_MAP.get(status_raw)
        if status is None:
            status = "Open"
            warnings.append(f"{display_name}: unrecognized status '{status_raw}' mapped to Open")
        created_at = dispute.get("initiated_at") or dispute.get("created_at") or ""

        rows.append({
            "dispute_id": dispute_id,
            "store": display_name,
            "created_at": created_at,
            "created_date": to_local_date(created_at, tz),
            "order_number": order.get("name") or (f"#{order['order_number']}" if order.get("order_number") else ""),
            "order_id": order_id or "",
            "customer": customer_name(order),
            "amount": dispute.get("amount") or "",
            "currency": dispute.get("currency") or "",
            "reason": dispute.get("reason") or "",
            "status": status,
            "status_raw": status_raw,
            "case_type": dispute.get("type") or "",
            "outcome_date": to_local_date(dispute.get("finalized_on"), tz),
            "evidence_due_by": to_local_date(dispute.get("evidence_due_by"), tz),
        })

    print(f"[{display_name}] {len(rows)} dispute(s)")
    return rows


def main() -> None:
    rows: list[dict] = []
    warnings: list[str] = []

    for display_name, env_key in STORES.items():
        if not ShopifyStore.configured_in_env(env_key):
            warnings.append(f"{display_name}: no {env_key}_SHOPIFY_DOMAIN / {env_key}_SHOPIFY_ACCESS_TOKEN in .env - store skipped")
            print(f"[{display_name}] skipped - credentials missing")
            continue
        try:
            rows.extend(collect_store(display_name, env_key, warnings))
        except Exception as exc:
            warnings.append(f"{display_name}: fetch failed ({exc})")
            print(f"[{display_name}] failed: {exc}")

    rows.sort(key=lambda r: (r["created_date"], r["store"]), reverse=True)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "stores": list(STORES),
        "status_map": STATUS_MAP,
        "warnings": warnings,
        "chargebacks": rows,
    }
    with open("chargebacks.json", "w") as handle:
        json.dump(payload, handle, indent=2)
    with open("chargebacks.csv", "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n{len(rows)} chargeback(s) written to chargebacks.json and chargebacks.csv")
    for warning in warnings:
        print(f"  warning: {warning}")
    if not rows:
        sys.exit(1 if warnings else 0)


if __name__ == "__main__":
    main()
