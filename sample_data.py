"""Generate a synthetic dispute set so the dashboard can be reviewed without credentials.

This exists purely so the layout can be signed off before the Admin API tokens
are in place. Every payload it produces is stamped with sample=True, which makes
the dashboard render a "SAMPLE DATA" banner. Real numbers come from
fetch_chargebacks.py.

    python sample_data.py --out data/chargebacks-sample.json
"""

import argparse
import json
import os
import random
from datetime import datetime, timedelta, timezone

from chargeback_model import build_payload, normalize

STORES = [
    ("MARY", "Mary's Tanks", "ya6ker-ps.myshopify.com", 1.0),
    ("MAGIE", "Maggies Tanks", "4r0jeh-pr.myshopify.com", 1.35),
    ("LYN", "Lyn's Tanks", "lyns-tanks.myshopify.com", 0.7),
    ("MJ", "Mary and James", "mary-and-james.myshopify.com", 0.5),
    ("ELSIE", "Simply Elsie", "simply-elsie.myshopify.com", 0.35),
]

# Weighted to look like a US apparel/subscription mix: delivery and
# expectation disputes dominate, outright fraud is a smaller slice.
REASON_WEIGHTS = [
    ("product_not_received", 26),
    ("fraudulent", 20),
    ("product_unacceptable", 16),
    ("subscription_canceled", 12),
    ("credit_not_processed", 9),
    ("unrecognized", 7),
    ("duplicate", 5),
    ("general", 3),
    ("customer_initiated", 2),
]

FIRST_NAMES = ["Margaret", "Susan", "Deborah", "Linda", "Patricia", "Karen", "Barbara", "Nancy",
               "Carol", "Sandra", "Janet", "Diane", "Ruth", "Sharon", "Donna", "Kathleen"]
LAST_NAMES = ["Foster", "Coleman", "Brown", "Carter", "Hughes", "Bennett", "Price", "Ward",
              "Reed", "Cook", "Morgan", "Bailey", "Rivera", "Cooper", "Richardson", "Wood"]


def _weighted(rng, pairs):
    values, weights = zip(*pairs)
    return rng.choices(values, weights=weights, k=1)[0]


def _status_for(rng, age_days: int) -> str:
    """Older disputes have had time to resolve; recent ones are still open."""
    if age_days < 12:
        return _weighted(rng, [("needs_response", 60), ("warning_needs_response", 15), ("under_review", 25)])
    if age_days < 35:
        return _weighted(
            rng,
            [("under_review", 40), ("needs_response", 18), ("warning_under_review", 8),
             ("won", 16), ("lost", 14), ("prevented", 4)],
        )
    return _weighted(
        rng,
        [("lost", 38), ("won", 28), ("accepted", 10), ("charge_refunded", 9),
         ("prevented", 8), ("warning_closed", 7)],
    )


def generate(days: int = 180, seed: int = 20260814) -> dict:
    rng = random.Random(seed)
    now = datetime.now(timezone.utc)
    rows: list[dict] = []
    dispute_id = 6_100_000_000
    order_id = 5_400_000_000

    for key, label, domain, intensity in STORES:
        for day_offset in range(days):
            date = now - timedelta(days=day_offset)
            # A mild upward drift over the window plus a weekly ripple, so the
            # trend chart has something realistic to show.
            drift = 1.0 + 0.5 * (days - day_offset) / days
            weekly = 1.0 + 0.25 * (1 if date.weekday() in (0, 1) else -1)
            expected = 0.55 * intensity * drift * weekly
            for _ in range(min(_poisson(rng, expected), 6)):
                dispute_id += 1
                order_id += 1
                age_days = day_offset
                status = _status_for(rng, age_days)
                reason = _weighted(rng, REASON_WEIGHTS)
                initiated = date - timedelta(hours=rng.randint(0, 23))
                due = initiated + timedelta(days=rng.choice([7, 10, 14, 21]))
                finalized = (
                    initiated + timedelta(days=rng.randint(18, 70))
                    if status in {"won", "lost", "accepted", "charge_refunded", "warning_closed", "prevented"}
                    else None
                )
                if finalized and finalized > now:
                    finalized = now - timedelta(days=rng.randint(0, 3))

                dispute = {
                    "id": dispute_id,
                    "order_id": order_id,
                    "type": "inquiry" if status.startswith("warning_") else "chargeback",
                    "amount": f"{rng.choice([29.95, 39.9, 49.95, 59.9, 69.95, 79.9, 89.85, 119.8]):.2f}",
                    "currency": "USD",
                    "reason": reason,
                    "network_reason": "",
                    "status": status,
                    "evidence_due_by": due.isoformat().replace("+00:00", "Z"),
                    "evidence_sent_on": (
                        (initiated + timedelta(days=rng.randint(1, 5))).isoformat().replace("+00:00", "Z")
                        if status not in {"needs_response", "warning_needs_response"}
                        else None
                    ),
                    "finalized_on": finalized.isoformat().replace("+00:00", "Z") if finalized else None,
                    "initiated_at": initiated.isoformat().replace("+00:00", "Z"),
                }
                first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
                order = {
                    "id": order_id,
                    "name": f"#{100000 + (order_id % 90000)}",
                    "order_number": 100000 + (order_id % 90000),
                    "email": f"{first.lower()}.{last.lower()}@example.com",
                    "customer": {"first_name": first, "last_name": last,
                                 "email": f"{first.lower()}.{last.lower()}@example.com"},
                }
                rows.append(normalize(dispute, key, label, order, now))

    store_meta = [{"key": k, "label": l, "domain": d, "fetch_error": None} for k, l, d, _ in STORES]
    return build_payload(rows, store_meta, now, meta={"source": "sample_generator", "sample": True, "days": days})


def _poisson(rng: random.Random, lam: float) -> int:
    """Knuth's sampler - random.Random has no poisson of its own."""
    import math

    limit, count, product = math.exp(-lam), 0, 1.0
    while True:
        product *= rng.random()
        if product <= limit:
            return count
        count += 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=os.path.join("data", "chargebacks-sample.json"))
    parser.add_argument("--days", type=int, default=180)
    args = parser.parse_args()

    payload = generate(days=args.days)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as handle:
        json.dump(payload, handle, indent=2)
    print(f"{payload['totals']['total']} sample disputes written to {args.out}")


if __name__ == "__main__":
    main()
