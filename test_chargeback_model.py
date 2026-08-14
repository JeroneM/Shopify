"""Checks on the dispute taxonomy and the numbers derived from it.

    python test_chargeback_model.py

These guard the judgement calls the dashboard makes - especially that an
"accepted" dispute counts as a loss, and that money is never summed across
currencies.
"""

from datetime import datetime, timedelta, timezone

from chargeback_model import (
    build_payload,
    needs_action,
    normalize,
    outcome_of,
    reason_category,
    reason_label,
    status_label,
    summarize,
    trend_direction,
)

NOW = datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc)


def make(status, reason="fraudulent", amount="50.00", days_ago=5, due_in=7, currency="USD", order=None):
    initiated = NOW - timedelta(days=days_ago)
    dispute = {
        "id": 900 + days_ago,
        "order_id": 500 + days_ago,
        "type": "chargeback",
        "amount": amount,
        "currency": currency,
        "reason": reason,
        "status": status,
        "initiated_at": initiated.isoformat().replace("+00:00", "Z"),
        "evidence_due_by": (initiated + timedelta(days=due_in)).isoformat().replace("+00:00", "Z"),
        "finalized_on": None,
    }
    return normalize(dispute, "MARY", "Mary's Tanks", order, NOW)


def check(label, condition):
    if not condition:
        raise AssertionError(label)
    print(f"  ok  {label}")


def test_outcomes():
    check("needs_response is open", outcome_of("needs_response") == "open")
    check("warning_needs_response is open", outcome_of("warning_needs_response") == "open")
    check("under_review is open", outcome_of("under_review") == "open")
    check("won is a win", outcome_of("won") == "won")
    check("lost is a loss", outcome_of("lost") == "lost")
    check("accepted counts as a loss - the money is gone", outcome_of("accepted") == "lost")
    check("prevented is closed without a verdict", outcome_of("prevented") == "closed_other")
    check("charge_refunded is closed without a verdict", outcome_of("charge_refunded") == "closed_other")
    check("unknown status does not silently become a win", outcome_of("brand_new_status") == "unknown")

    check("only needs_response statuses demand evidence", needs_action("needs_response"))
    check("under_review needs nothing from us", not needs_action("under_review"))
    check("warning_needs_response demands evidence", needs_action("warning_needs_response"))


def test_labels():
    check("known status is humanised", status_label("warning_under_review") == "Inquiry - under review")
    check("unknown status still reads", status_label("some_new_thing") == "Some new thing")
    check("known reason is humanised", reason_label("product_not_received") == "Product not received")
    check("missing reason is explicit", reason_label("") == "Not specified")
    check("unknown reason still reads", reason_label("act_of_god") == "Act of god")
    check("reason maps to an operational area", reason_category("product_not_received") == "Fulfilment & delivery")
    check("unknown reason gets a fallback area", reason_category("act_of_god") == "Other / unspecified")


def test_normalize():
    order = {
        "order_number": 1234,
        "name": "#1234",
        "email": "a@b.com",
        "customer": {"first_name": "Ada", "last_name": "Lovelace", "email": "ada@b.com"},
    }
    row = make("needs_response", days_ago=2, due_in=7, order=order)
    check("customer name is joined", row["customer"] == "Ada Lovelace")
    check("order number carried through", row["order_number"] == 1234)
    check("amount parsed to float", row["amount"] == 50.0)
    check("chargeback date is a plain date", row["chargeback_date"] == "2026-08-12")
    check("days to deadline computed", row["days_to_due"] == 5)
    check("not yet overdue", row["overdue"] is False)

    overdue = make("needs_response", days_ago=20, due_in=7)
    check("overdue flagged", overdue["overdue"] is True and overdue["days_to_due"] < 0)

    # A closed dispute has no live deadline, however old the due date is.
    closed = make("won", days_ago=90, due_in=7)
    check("closed dispute has no countdown", closed["days_to_due"] is None)
    check("closed dispute is not overdue", closed["overdue"] is False)
    check("won dispute reports its result", closed["final_result"] == "Won")

    missing_order = make("lost", order=None)
    check("missing order does not break the row", missing_order["customer"] == "")

    junk = normalize({"id": 1, "amount": "not-a-number", "status": "won"}, "K", "K", None, NOW)
    check("unparseable amount falls back to zero", junk["amount"] == 0.0)
    check("missing dates stay empty", junk["chargeback_date"] is None)


def test_summarize():
    rows = [
        make("needs_response", days_ago=1),
        make("needs_response", days_ago=40, due_in=7),   # overdue
        make("under_review", days_ago=10),
        make("won", days_ago=50),
        make("won", days_ago=51),
        make("won", days_ago=52),
        make("lost", days_ago=53),
        make("accepted", days_ago=54),
        make("prevented", days_ago=55),
    ]
    s = summarize(rows)
    check("total counted", s["total"] == 9)
    check("open counted", s["open"] == 3)
    check("needs_action counted", s["needs_action"] == 2)
    check("overdue counted", s["overdue"] == 1)
    check("under_review counted", s["under_review"] == 1)
    check("closed is everything not open", s["closed"] == 6)
    check("wins counted", s["won"] == 3)
    check("accepted rolls into losses", s["lost"] == 2)
    check("prevented sits outside the verdict", s["closed_other"] == 1)
    check("decided excludes prevented", s["decided"] == 5)
    check("win rate is decided-only", s["win_rate"] == 60.0)
    check("loss rate is decided-only", s["loss_rate"] == 40.0)
    check("win and loss rate sum to 100", s["win_rate"] + s["loss_rate"] == 100.0)
    check("at-risk value covers open only", s["open_amount"] == 150.0)

    empty = summarize([])
    check("no disputes means no win rate, not a divide by zero", empty["win_rate"] is None)
    check("no disputes totals to zero", empty["total"] == 0 and empty["total_amount"] == 0)


def test_trend():
    recent = [make("won", days_ago=d) for d in range(1, 21)]
    prior = [make("won", days_ago=d) for d in range(35, 40)]
    up = trend_direction(recent + prior, NOW)
    check("clear rise reads as increasing", up["direction"] == "increasing")

    down = trend_direction(
        [make("won", days_ago=d) for d in range(1, 4)] + [make("won", days_ago=d) for d in range(35, 55)], NOW
    )
    check("clear fall reads as decreasing", down["direction"] == "decreasing")

    flat = trend_direction(
        [make("won", days_ago=d) for d in range(1, 11)] + [make("won", days_ago=d) for d in range(31, 41)], NOW
    )
    check("matched volumes read as stable", flat["direction"] == "stable")

    thin = trend_direction([make("won", days_ago=2)], NOW)
    check("a handful of cases is not a trend", thin["direction"] == "insufficient data")


def test_payload():
    rows = [
        make("needs_response", reason="product_not_received", days_ago=2),
        make("won", reason="product_not_received", days_ago=40),
        make("lost", reason="fraudulent", days_ago=41),
        make("won", reason="fraudulent", days_ago=42, currency="EUR", amount="20.00"),
    ]
    payload = build_payload(rows, [{"key": "MARY", "label": "Mary's Tanks", "domain": "x.myshopify.com"}], NOW)

    check("store summary attached", payload["stores"][0]["total"] == 4)
    check("reasons ranked by volume", payload["reasons"][0]["count"] == 2)
    check("reason percentages computed", payload["reasons"][0]["pct"] == 50.0)
    check("reason carries an operational fix", bool(payload["reasons"][0]["action"]))
    check("top reason surfaced", payload["highlights"]["top_reason"]["count"] == 2)
    check("top store surfaced", payload["highlights"]["top_store"]["count"] == 4)
    check("both currencies listed", payload["currencies"] == ["EUR", "USD"])
    check("status breakdown covers every status", len(payload["status_breakdown"]) == 3)
    check("disputes sorted newest first", payload["disputes"][0]["chargeback_date"] == "2026-08-12")

    fraud = [r for r in payload["reasons"] if r["reason"] == "fraudulent"][0]
    check("per-reason win rate is decided-only", fraud["win_rate"] == 50.0)


def main() -> int:
    tests = [
        ("status taxonomy", test_outcomes),
        ("labels", test_labels),
        ("row normalisation", test_normalize),
        ("summary counters", test_summarize),
        ("trend direction", test_trend),
        ("dashboard payload", test_payload),
    ]
    for name, fn in tests:
        print(f"\n{name}")
        fn()
    print(f"\nAll {len(tests)} groups passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
