"""Pull every chargeback/dispute from all stores into one file the dashboard reads.

    python chargebacks_export.py                # -> chargebacks.json + chargebacks.csv

One row per chargeback case. Shopify opens a separate dispute record for each
captured transaction, so a single chargeback on an order with several
transactions arrives as several disputes - the merchant sees one chargeback on
one order, and that is what a row here counts. Disputes are grouped by order,
their amounts summed, and every dispute ID is kept on the row so the case can be
traced back. A dispute with no order is a case on its own.
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
    "case_id", "store", "created_at", "created_date", "order_number", "order_id",
    "customer", "amount", "currency", "reason", "status", "sub_status",
    "dispute_count", "dispute_ids", "status_raw", "outcome_date", "evidence_due_by",
]

# One order can carry several Shopify disputes - one per captured transaction - which
# the merchant sees as a single chargeback on a single order. Disputes are grouped by
# order and the case takes the status of the dispute that still needs the most action.
NEEDS_RESPONSE = {"needs_response", "warning_needs_response"}
UNDER_REVIEW = {"under_review", "warning_under_review", "response_disabled"}
LOST_STATUSES = {"lost", "accepted", "charge_refunded"}


def case_status(disputes: list[dict]) -> tuple[str, str, dict]:
    """(status, sub_status, the dispute that decided it) for one order's disputes."""
    newest = lambda group: sorted(group, key=lambda d: str(d.get("created_at") or ""))[-1]
    for statuses, status, sub in (
        (NEEDS_RESPONSE, "Open", "Needs response"),
        (UNDER_REVIEW, "Open", "Under review"),
        (LOST_STATUSES, "Lost", "Lost"),
    ):
        hits = [d for d in disputes if d.get("status") in statuses]
        if hits:
            return status, sub, newest(hits)
    sub = "Prevented" if all(d.get("status") == "prevented" for d in disputes) else "Defended"
    return "Won", sub, newest(disputes)


def group_into_cases(disputes: list[dict], display_name: str, tz: ZoneInfo, warnings: list[str]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for dispute in disputes:
        key = str(dispute.get("order_id") or ("dispute-" + str(dispute.get("id"))))
        grouped.setdefault(key, []).append(dispute)

    cases = []
    for key, group in grouped.items():
        status, sub_status, primary = case_status(group)
        unknown = [d for d in group if d.get("status") not in STATUS_MAP]
        for d in unknown:
            warnings.append(f"{display_name}: unrecognized status '{d.get('status')}' on dispute {d.get('id')}")
        dates = sorted(to_local_date(d.get("initiated_at") or d.get("created_at"), tz) for d in group)
        finalized = sorted(filter(None, (to_local_date(d.get("finalized_on"), tz) for d in group)))
        due = sorted(filter(None, (to_local_date(d.get("evidence_due_by"), tz) for d in group)))
        cases.append({
            "_group": group,
            "case_id": f"{display_name}:{key}",
            "store": display_name,
            "created_at": min(str(d.get("initiated_at") or d.get("created_at") or "") for d in group),
            "created_date": dates[0],
            "order_id": group[0].get("order_id") or "",
            "amount": round(sum(float(d.get("amount") or 0) for d in group), 2),
            "currency": primary.get("currency") or "",
            "reason": primary.get("reason") or "",
            "status": status,
            "sub_status": sub_status,
            "status_raw": primary.get("status") or "",
            "dispute_count": len(group),
            "dispute_ids": ";".join(str(d.get("id")) for d in sorted(group, key=lambda d: str(d.get("id")))),
            "outcome_date": finalized[-1] if finalized and status != "Open" else "",
            "evidence_due_by": due[0] if due and status == "Open" else "",
        })
    return cases


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

    cases = group_into_cases(list(seen.values()), display_name, tz, warnings)

    order_cache: dict[int, dict] = {}
    for case in cases:
        order_id = case["order_id"]
        order = {}
        if order_id:
            if order_id not in order_cache:
                try:
                    order_cache[order_id] = store.order(order_id)
                except Exception as exc:
                    order_cache[order_id] = {}
                    warnings.append(f"{display_name}: could not read order {order_id} ({exc})")
            order = order_cache[order_id]
        case["order_number"] = order.get("name") or (f"#{order['order_number']}" if order.get("order_number") else "")
        case["customer"] = customer_name(order)
        case["disputes"] = [
            {
                "dispute_id": str(d.get("id")),
                "created_date": to_local_date(d.get("initiated_at") or d.get("created_at"), tz),
                "amount": d.get("amount") or "",
                "currency": d.get("currency") or "",
                "reason": d.get("reason") or "",
                "status_raw": d.get("status") or "",
                "outcome_date": to_local_date(d.get("finalized_on"), tz),
            }
            for d in sorted(case.pop("_group"), key=lambda d: str(d.get("initiated_at") or ""))
        ]

    split = sum(1 for c in cases if c["dispute_count"] > 1)
    if split:
        warnings.append(
            f"{display_name}: {split} order(s) carry more than one Shopify dispute "
            f"(one per transaction) and count as one chargeback each"
        )
    print(f"[{display_name}] {len(disputes)} dispute(s) -> {len(cases)} chargeback case(s)")
    return cases


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
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    disputes = sum(r["dispute_count"] for r in rows)
    print(f"\n{len(rows)} chargeback case(s) from {disputes} Shopify dispute(s)"
          f" written to chargebacks.json and chargebacks.csv")
    for warning in warnings:
        print(f"  warning: {warning}")
    if not rows:
        sys.exit(1 if warnings else 0)


if __name__ == "__main__":
    main()
