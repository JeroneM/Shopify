"""Shared vocabulary for Shopify Payments disputes.

Shopify returns raw enum strings for dispute status and reason. Everything in
this module turns those into the buckets the dashboard reports on, so the
status/reason taxonomy lives in exactly one place.
"""

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

# --- Status taxonomy -------------------------------------------------------
# Shopify uses a parallel set of "warning_*" statuses for inquiries/retrievals,
# which are pre-chargeback notices rather than money actually pulled back.

NEEDS_RESPONSE_STATUSES = {"needs_response", "warning_needs_response"}
UNDER_REVIEW_STATUSES = {"under_review", "warning_under_review"}
OPEN_STATUSES = NEEDS_RESPONSE_STATUSES | UNDER_REVIEW_STATUSES

WON_STATUSES = {"won"}
# "accepted" means we conceded without submitting evidence - the money is gone,
# so it belongs with the losses rather than in a neutral "closed" bucket.
LOST_STATUSES = {"lost", "accepted"}
# Closed without a win/loss verdict: refunded before adjudication, inquiry that
# lapsed, or Shopify blocked it under chargeback protection.
NEUTRAL_CLOSED_STATUSES = {"charge_refunded", "warning_closed", "response_disabled", "prevented"}
CLOSED_STATUSES = WON_STATUSES | LOST_STATUSES | NEUTRAL_CLOSED_STATUSES

STATUS_LABELS = {
    "needs_response": "Needs response",
    "warning_needs_response": "Inquiry - needs response",
    "under_review": "Under review (evidence submitted)",
    "warning_under_review": "Inquiry - under review",
    "won": "Won",
    "lost": "Lost",
    "accepted": "Accepted (conceded)",
    "charge_refunded": "Closed - charge refunded",
    "warning_closed": "Inquiry closed",
    "response_disabled": "Closed - response disabled",
    "prevented": "Prevented by Shopify Protect",
}


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, (status or "unknown").replace("_", " ").capitalize())


def outcome_of(status: str) -> str:
    """Collapse a status into one of open / won / lost / closed_other."""
    if status in OPEN_STATUSES:
        return "open"
    if status in WON_STATUSES:
        return "won"
    if status in LOST_STATUSES:
        return "lost"
    if status in NEUTRAL_CLOSED_STATUSES:
        return "closed_other"
    return "unknown"


def needs_action(status: str) -> bool:
    """True when the team still has to submit evidence before the deadline."""
    return status in NEEDS_RESPONSE_STATUSES


# --- Reason taxonomy -------------------------------------------------------
# Each reason maps to an operational category, so the dashboard can point at
# the part of the business that is generating the disputes.

REASON_LABELS = {
    "product_not_received": "Product not received",
    "product_unacceptable": "Product unacceptable / not as described",
    "fraudulent": "Fraudulent transaction",
    "duplicate": "Duplicate charge",
    "subscription_canceled": "Subscription cancelled",
    "credit_not_processed": "Credit not processed",
    "unrecognized": "Unrecognized transaction",
    "customer_initiated": "Customer initiated",
    "general": "General / unspecified",
    "bank_cannot_process": "Bank cannot process",
    "debit_not_authorized": "Debit not authorized",
    "incorrect_account_details": "Incorrect account details",
    "insufficient_funds": "Insufficient funds",
}

REASON_CATEGORIES = {
    "product_not_received": "Fulfilment & delivery",
    "product_unacceptable": "Product & expectations",
    "fraudulent": "Fraud & card security",
    "unrecognized": "Fraud & card security",
    "duplicate": "Billing & refunds",
    "credit_not_processed": "Billing & refunds",
    "subscription_canceled": "Billing & refunds",
    "customer_initiated": "Billing & refunds",
    "bank_cannot_process": "Bank & payment technical",
    "debit_not_authorized": "Bank & payment technical",
    "incorrect_account_details": "Bank & payment technical",
    "insufficient_funds": "Bank & payment technical",
    "general": "Other / unspecified",
}

# What the team should go fix when a reason starts climbing.
REASON_ACTIONS = {
    "product_not_received": "Check carrier transit times, tracking accuracy and delivery-confirmation evidence.",
    "product_unacceptable": "Review product photos, sizing guides and description accuracy for the affected SKUs.",
    "fraudulent": "Tighten fraud screening and review high-risk orders before fulfilment.",
    "unrecognized": "Make the billing descriptor match the storefront name customers recognise.",
    "duplicate": "Audit checkout and retry logic for double captures.",
    "credit_not_processed": "Shorten refund turnaround and confirm refunds to the customer in writing.",
    "subscription_canceled": "Make cancellation self-service and confirm every cancellation by email.",
    "customer_initiated": "Review support response times - these often start as unanswered tickets.",
    "bank_cannot_process": "Usually issuer-side; monitor for volume rather than per-case action.",
    "debit_not_authorized": "Confirm authorisation flow and stored-payment consent.",
    "incorrect_account_details": "Usually issuer-side; monitor for volume rather than per-case action.",
    "insufficient_funds": "Usually issuer-side; monitor for volume rather than per-case action.",
    "general": "No reason code supplied by the issuer - review the individual cases.",
}


def reason_label(reason: str) -> str:
    if not reason:
        return "Not specified"
    return REASON_LABELS.get(reason, reason.replace("_", " ").capitalize())


def reason_category(reason: str) -> str:
    return REASON_CATEGORIES.get(reason or "", "Other / unspecified")


def reason_action(reason: str) -> str:
    return REASON_ACTIONS.get(reason or "", "Review the individual cases for a common root cause.")


# --- Helpers ---------------------------------------------------------------


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _iso_date(value: datetime | None) -> str | None:
    return value.date().isoformat() if value else None


def normalize(dispute: dict, store_key: str, store_label: str, order: dict | None, now: datetime) -> dict:
    """Flatten one Shopify dispute (+ its order) into the dashboard's row shape."""
    status = dispute.get("status") or "unknown"
    reason = dispute.get("reason") or ""
    initiated = parse_dt(dispute.get("initiated_at"))
    due = parse_dt(dispute.get("evidence_due_by"))
    finalized = parse_dt(dispute.get("finalized_on"))

    customer = (order or {}).get("customer") or {}
    customer_name = " ".join(
        part for part in [customer.get("first_name"), customer.get("last_name")] if part
    ).strip()

    days_to_due = None
    if due and status in NEEDS_RESPONSE_STATUSES:
        days_to_due = (due - now).days

    try:
        amount = round(float(dispute.get("amount") or 0), 2)
    except (TypeError, ValueError):
        amount = 0.0

    outcome = outcome_of(status)
    return {
        "store": store_key,
        "store_label": store_label,
        "dispute_id": str(dispute.get("id")),
        "order_id": dispute.get("order_id"),
        "order_number": (order or {}).get("order_number"),
        "order_name": (order or {}).get("name"),
        "customer": customer_name or (order or {}).get("email") or "",
        "customer_email": customer.get("email") or (order or {}).get("email") or "",
        "type": dispute.get("type") or "chargeback",
        "amount": amount,
        "currency": dispute.get("currency") or "",
        "reason": reason,
        "reason_label": reason_label(reason),
        "reason_category": reason_category(reason),
        "network_reason": dispute.get("network_reason") or "",
        "status": status,
        "status_label": status_label(status),
        "outcome": outcome,
        "needs_action": needs_action(status),
        "chargeback_date": _iso_date(initiated),
        "evidence_due_date": _iso_date(due),
        "evidence_sent_on": dispute.get("evidence_sent_on"),
        "resolution_date": _iso_date(finalized),
        "final_result": {"won": "Won", "lost": "Lost"}.get(outcome, status_label(status) if finalized else ""),
        "days_to_due": days_to_due,
        "overdue": bool(days_to_due is not None and days_to_due < 0),
    }


def _rate(numerator: int, denominator: int) -> float | None:
    return round(100 * numerator / denominator, 1) if denominator else None


def summarize(rows: list[dict]) -> dict:
    """Headline counters for a set of rows (one store, or all of them)."""
    outcomes = Counter(row["outcome"] for row in rows)
    won, lost = outcomes["won"], outcomes["lost"]
    decided = won + lost
    open_rows = [row for row in rows if row["outcome"] == "open"]
    action_rows = [row for row in rows if row["needs_action"]]
    return {
        "total": len(rows),
        "open": len(open_rows),
        "needs_action": len(action_rows),
        "overdue": sum(1 for row in action_rows if row["overdue"]),
        "under_review": sum(1 for row in rows if row["status"] in UNDER_REVIEW_STATUSES),
        "closed": len(rows) - len(open_rows),
        "won": won,
        "lost": lost,
        "closed_other": outcomes["closed_other"],
        "decided": decided,
        "total_amount": round(sum(row["amount"] for row in rows), 2),
        "open_amount": round(sum(row["amount"] for row in open_rows), 2),
        "won_amount": round(sum(row["amount"] for row in rows if row["outcome"] == "won"), 2),
        "lost_amount": round(sum(row["amount"] for row in rows if row["outcome"] == "lost"), 2),
        "win_rate": _rate(won, decided),
        "loss_rate": _rate(lost, decided),
    }


def trend_direction(rows: list[dict], now: datetime, window_days: int = 30) -> dict:
    """Compare the last window against the one before it to call the trend."""
    recent_start = now - timedelta(days=window_days)
    prior_start = now - timedelta(days=2 * window_days)

    recent = prior = 0
    for row in rows:
        initiated = parse_dt(row["chargeback_date"])
        if not initiated:
            continue
        if initiated >= recent_start:
            recent += 1
        elif initiated >= prior_start:
            prior += 1

    if recent + prior < 6:
        direction = "insufficient data"
        change = None
    elif prior == 0:
        direction = "increasing" if recent else "stable"
        change = None
    else:
        change = round(100 * (recent - prior) / prior, 1)
        direction = "increasing" if change > 15 else "decreasing" if change < -15 else "stable"

    return {
        "direction": direction,
        "change_pct": change,
        "recent": recent,
        "prior": prior,
        "window_days": window_days,
    }


def build_payload(rows: list[dict], stores: list[dict], now: datetime, meta: dict | None = None) -> dict:
    """Everything the dashboard needs, precomputed where it is cheap to do so."""
    by_store = defaultdict(list)
    for row in rows:
        by_store[row["store"]].append(row)

    store_summaries = [
        {
            "key": store["key"],
            "label": store["label"],
            "domain": store.get("domain", ""),
            "fetch_error": store.get("fetch_error"),
            **summarize(by_store.get(store["key"], [])),
        }
        for store in stores
    ]

    reason_rollup = []
    total = len(rows) or 1
    for reason, count in Counter(row["reason"] for row in rows).most_common():
        reason_rows = [row for row in rows if row["reason"] == reason]
        decided = [row for row in reason_rows if row["outcome"] in ("won", "lost")]
        wins = sum(1 for row in decided if row["outcome"] == "won")
        reason_rollup.append(
            {
                "reason": reason,
                "label": reason_label(reason),
                "category": reason_category(reason),
                "action": reason_action(reason),
                "count": count,
                "pct": round(100 * count / total, 1),
                "amount": round(sum(row["amount"] for row in reason_rows), 2),
                "win_rate": _rate(wins, len(decided)),
            }
        )

    top_store = max(store_summaries, key=lambda s: s["total"], default=None)
    return {
        "generated_at": now.isoformat(),
        "meta": meta or {},
        "stores": store_summaries,
        "totals": summarize(rows),
        "status_breakdown": [
            {
                "status": status,
                "label": status_label(status),
                "outcome": outcome_of(status),
                "count": count,
                "amount": round(sum(r["amount"] for r in rows if r["status"] == status), 2),
            }
            for status, count in Counter(row["status"] for row in rows).most_common()
        ],
        "reasons": reason_rollup,
        "trend": trend_direction(rows, now),
        "highlights": {
            "top_store": {"label": top_store["label"], "count": top_store["total"]} if top_store else None,
            "top_reason": (
                {"label": reason_rollup[0]["label"], "count": reason_rollup[0]["count"], "pct": reason_rollup[0]["pct"]}
                if reason_rollup
                else None
            ),
        },
        "currencies": sorted({row["currency"] for row in rows if row["currency"]}),
        "disputes": sorted(rows, key=lambda r: (r["chargeback_date"] or ""), reverse=True),
    }
