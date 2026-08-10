import csv
from datetime import datetime, timezone

from shopify_client import ShopifyStore

STORE_KEYS = ["MARY", "LYN", "MAGIE"]

NEEDS_RESPONSE_STATUSES = {"needs_response", "warning_needs_response"}
UNDER_REVIEW_STATUSES = {"under_review", "warning_under_review"}
OPEN_STATUSES = NEEDS_RESPONSE_STATUSES | UNDER_REVIEW_STATUSES
CLOSED_STATUSES = {"won", "lost", "accepted", "charge_refunded", "warning_closed", "response_disabled"}
# Auto-blocked by Shopify's chargeback protection before it became a real dispute - no action needed.
PREVENTED_STATUSES = {"prevented"}


def fmt_amount(d: dict) -> str:
    return f"{d.get('amount')} {d.get('currency')}"


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

    print("=" * 70)
    print(
        f"TOTAL DISPUTES: {len(all_disputes)}  |  OPEN: {len(open_disputes)}  |  CLOSED: {len(closed_disputes)}"
        f"  |  PREVENTED (no action needed): {len(prevented_disputes)}"
    )
    if other_disputes:
        print(f"UNRECOGNIZED STATUS: {len(other_disputes)} -> {[d['status'] for d in other_disputes]}")
    print("=" * 70)

    print(f"\n--- OPEN: submitted evidence, awaiting reply ({len(submitted_awaiting_reply)}) ---")
    for d in submitted_awaiting_reply:
        print(
            f"[{d['_store']}] dispute {d['id']} | order_id {d['order_id']} | {fmt_amount(d)} "
            f"| reason: {d.get('reason')} | evidence_sent_on: {d.get('evidence_sent_on')}"
        )

    print(f"\n--- OPEN: still need to submit evidence ({len(needs_our_evidence)}) ---")
    now = datetime.now(timezone.utc)
    for d in sorted(needs_our_evidence, key=lambda x: x.get("evidence_due_by") or ""):
        due = d.get("evidence_due_by")
        overdue_flag = ""
        if due:
            due_dt = datetime.fromisoformat(due.replace("Z", "+00:00"))
            days_left = (due_dt - now).days
            overdue_flag = f" ({'OVERDUE' if days_left < 0 else f'{days_left}d left'})"
        print(
            f"[{d['_store']}] dispute {d['id']} | order_id {d['order_id']} | {fmt_amount(d)} "
            f"| reason: {d.get('reason')} | DEADLINE: {due}{overdue_flag}"
        )

    print(f"\n--- CLOSED ({len(closed_disputes)}) ---")
    for d in closed_disputes:
        print(
            f"[{d['_store']}] dispute {d['id']} | order_id {d['order_id']} | {fmt_amount(d)} "
            f"| status: {d['status']} | finalized_on: {d.get('finalized_on')}"
        )

    out_path = "disputes_export.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["store", "dispute_id", "order_id", "amount", "currency", "reason", "status",
             "evidence_sent_on", "evidence_due_by", "finalized_on"]
        )
        for d in sorted(all_disputes, key=lambda x: x["_store"]):
            writer.writerow(
                [d["_store"], d["id"], d["order_id"], d.get("amount"), d.get("currency"),
                 d.get("reason"), d["status"], d.get("evidence_sent_on"),
                 d.get("evidence_due_by"), d.get("finalized_on")]
            )
    print(f"\nFull export written to {out_path}")


if __name__ == "__main__":
    main()
