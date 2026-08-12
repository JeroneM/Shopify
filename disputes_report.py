import csv
from collections import Counter
from datetime import datetime, timezone

from shopify_client import ShopifyStore

STORE_KEYS = ["MARY", "LYN", "MAGIE"]

NEEDS_RESPONSE_STATUSES = {"needs_response", "warning_needs_response"}
UNDER_REVIEW_STATUSES = {"under_review", "warning_under_review"}
OPEN_STATUSES = NEEDS_RESPONSE_STATUSES | UNDER_REVIEW_STATUSES
CLOSED_STATUSES = {"won", "lost", "accepted", "charge_refunded", "warning_closed", "response_disabled"}
# Auto-blocked by Shopify's chargeback protection before it became a real dispute - no action needed.
PREVENTED_STATUSES = {"prevented"}

# Simplified pending / win / lost bucket for reporting, per Shopify's dispute status enum.
# https://shopify.dev/docs/api/admin-rest/latest/resources/dispute
STATUS_OUTCOME = {
    "needs_response": "Pending",
    "warning_needs_response": "Pending",
    "under_review": "Pending",
    "warning_under_review": "Pending",
    "won": "Win",
    "lost": "Lost",
    "accepted": "Lost",  # merchant accepted the chargeback without contesting it
    "response_disabled": "Lost",  # window to respond closed with no evidence submitted
    "charge_refunded": "Lost",  # order was refunded before the dispute closed
    "warning_closed": "Closed (inquiry, no charge)",  # bank inquiry only, not a real chargeback
    "prevented": "N/A (auto-prevented)",
}


def outcome_for(status: str) -> str:
    return STATUS_OUTCOME.get(status, f"Unknown ({status})")


def fmt_amount(d: dict) -> str:
    return f"{d.get('amount')} {d.get('currency')}"


def initiated_date(d: dict) -> str:
    """Calendar date (store-local) the customer's bank filed the dispute, or '' if missing."""
    initiated_at = d.get("initiated_at")
    return initiated_at[:10] if initiated_at else ""


def main() -> None:
    all_disputes = []
    for key in STORE_KEYS:
        store = ShopifyStore.from_env(key)
        try:
            disputes = store.disputes()
        except Exception as exc:
            print(f"[{key}] failed to fetch disputes: {exc}")
            continue
        for d in disputes:
            d["_store"] = key
        all_disputes.extend(disputes)

    if not all_disputes:
        print("No disputes found on any store.")
        return

    open_disputes = [d for d in all_disputes if d["status"] in OPEN_STATUSES]
    closed_disputes = [d for d in all_disputes if d["status"] in CLOSED_STATUSES]
    prevented_disputes = [d for d in all_disputes if d["status"] in PREVENTED_STATUSES]
    other_disputes = [
        d for d in all_disputes if d["status"] not in OPEN_STATUSES | CLOSED_STATUSES | PREVENTED_STATUSES
    ]

    submitted_awaiting_reply = [d for d in open_disputes if d["status"] in UNDER_REVIEW_STATUSES]
    needs_our_evidence = [d for d in open_disputes if d["status"] in NEEDS_RESPONSE_STATUSES]
    won_disputes = [d for d in all_disputes if d["status"] == "won"]
    lost_disputes = [d for d in all_disputes if outcome_for(d["status"]) == "Lost"]

    stores = {key: ShopifyStore.from_env(key) for key in STORE_KEYS}
    order_cache: dict[tuple[str, int], dict] = {}

    def order_for(d: dict) -> dict:
        cache_key = (d["_store"], d["order_id"])
        if cache_key not in order_cache:
            try:
                order_cache[cache_key] = stores[d["_store"]].order(d["order_id"])
            except Exception:
                order_cache[cache_key] = {}
        return order_cache[cache_key]

    def order_number_for(d: dict) -> str:
        order = order_for(d)
        return str(order["order_number"]) if "order_number" in order else ""

    def customer_name_for(d: dict) -> str:
        customer = order_for(d).get("customer") or {}
        name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
        return name or "(unknown)"

    def customer_email_for(d: dict) -> str:
        order = order_for(d)
        return order.get("email") or (order.get("customer") or {}).get("email") or "(unknown)"

    def order_summary(d: dict) -> str:
        return f"order #{order_number_for(d) or d['order_id']} | {customer_name_for(d)} <{customer_email_for(d)}>"

    print("=" * 70)
    print(
        f"TOTAL DISPUTES: {len(all_disputes)}  |  PENDING: {len(open_disputes)}  |  WIN: {len(won_disputes)}"
        f"  |  LOST: {len(lost_disputes)}  |  PREVENTED (no action needed): {len(prevented_disputes)}"
    )
    if other_disputes:
        print(f"UNRECOGNIZED STATUS: {len(other_disputes)} -> {[d['status'] for d in other_disputes]}")
    print("=" * 70)

    print(f"\n--- PENDING: submitted evidence, awaiting reply ({len(submitted_awaiting_reply)}) ---")
    for d in submitted_awaiting_reply:
        print(
            f"[{d['_store']}] dispute {d['id']} | {order_summary(d)} | {fmt_amount(d)} "
            f"| reason: {d.get('reason')} | evidence_sent_on: {d.get('evidence_sent_on')}"
        )

    print(f"\n--- PENDING: still need to submit evidence ({len(needs_our_evidence)}) ---")
    now = datetime.now(timezone.utc)
    for d in sorted(needs_our_evidence, key=lambda x: x.get("evidence_due_by") or ""):
        due = d.get("evidence_due_by")
        overdue_flag = ""
        if due:
            due_dt = datetime.fromisoformat(due.replace("Z", "+00:00"))
            days_left = (due_dt - now).days
            overdue_flag = f" ({'OVERDUE' if days_left < 0 else f'{days_left}d left'})"
        print(
            f"[{d['_store']}] dispute {d['id']} | {order_summary(d)} | {fmt_amount(d)} "
            f"| reason: {d.get('reason')} | DEADLINE: {due}{overdue_flag}"
        )

    print(f"\n--- CLOSED: win / lost ({len(closed_disputes)}) ---")
    for d in closed_disputes:
        print(
            f"[{d['_store']}] dispute {d['id']} | {order_summary(d)} | {fmt_amount(d)} "
            f"| outcome: {outcome_for(d['status'])} (status: {d['status']}) | finalized_on: {d.get('finalized_on')}"
        )

    by_date = Counter(initiated_date(d) for d in all_disputes)
    print(f"\n--- DISPUTES SUBMITTED BY CUSTOMER, PER DATE ({len(by_date)} distinct dates) ---")
    for date, count in sorted(by_date.items()):
        print(f"{date or '(unknown date)'}: {count}")

    out_path = "disputes_export.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["store", "dispute_id", "order_id", "order_number", "customer_name", "customer_email",
             "amount", "currency", "reason", "status", "outcome", "initiated_at",
             "evidence_sent_on", "evidence_due_by", "finalized_on"]
        )
        for d in sorted(all_disputes, key=lambda x: (x.get("initiated_at") or "", x["_store"])):
            writer.writerow(
                [d["_store"], d["id"], d["order_id"], order_number_for(d), customer_name_for(d),
                 customer_email_for(d), d.get("amount"), d.get("currency"), d.get("reason"), d["status"],
                 outcome_for(d["status"]), d.get("initiated_at"), d.get("evidence_sent_on"),
                 d.get("evidence_due_by"), d.get("finalized_on")]
            )
    print(f"\nFull export written to {out_path}")

    by_date_path = "disputes_by_date.csv"
    with open(by_date_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date_submitted", "dispute_count"])
        for date, count in sorted(by_date.items()):
            writer.writerow([date, count])
    print(f"Per-date submission counts written to {by_date_path}")


if __name__ == "__main__":
    main()
