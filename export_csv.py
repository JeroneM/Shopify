"""Export the consolidated chargeback data to CSV.

    python export_csv.py                       # dist/chargebacks-<date>.csv
    python export_csv.py --summaries           # plus by-store / by-status / by-reason
    python export_csv.py --data data/chargebacks-sample.json --out /tmp/x.csv

Reads the same payload the dashboard renders, so the numbers always agree.
Files are written UTF-8 with a BOM so Excel opens accented names correctly.
"""

import argparse
import csv
import json
import os

DEFAULT_DATA = os.path.join("data", "chargebacks.json")
ENCODING = "utf-8-sig"

# The columns the dashboard's detail table shows, in that order, followed by
# the derived fields that are useful for slicing in a spreadsheet.
DISPUTE_COLUMNS = [
    ("Store", lambda r: r["store_label"]),
    ("Order Number", lambda r: r.get("order_name") or (f"#{r['order_number']}" if r.get("order_number") else "")),
    ("Dispute ID", lambda r: r["dispute_id"]),
    ("Customer", lambda r: r.get("customer", "")),
    ("Customer Email", lambda r: r.get("customer_email", "")),
    ("Chargeback Date", lambda r: r.get("chargeback_date") or ""),
    ("Amount", lambda r: f"{r.get('amount', 0):.2f}"),
    ("Currency", lambda r: r.get("currency", "")),
    ("Reason", lambda r: r.get("reason_label", "")),
    ("Reason Category", lambda r: r.get("reason_category", "")),
    ("Status", lambda r: r.get("status_label", "")),
    ("Evidence Due Date", lambda r: r.get("evidence_due_date") or ""),
    ("Final Result", lambda r: r.get("final_result") or ""),
    ("Resolution Date", lambda r: r.get("resolution_date") or ""),
    ("Outcome", lambda r: r.get("outcome", "")),
    ("Needs Action", lambda r: "yes" if r.get("needs_action") else "no"),
    ("Days To Evidence Due", lambda r: "" if r.get("days_to_due") is None else r["days_to_due"]),
    ("Overdue", lambda r: "yes" if r.get("overdue") else "no"),
    ("Evidence Sent On", lambda r: (r.get("evidence_sent_on") or "")[:10]),
    ("Dispute Type", lambda r: r.get("type", "")),
    ("Network Reason", lambda r: r.get("network_reason", "")),
    ("Shopify Order ID", lambda r: r.get("order_id") or ""),
    ("Store Key", lambda r: r["store"]),
    ("Raw Status", lambda r: r.get("status", "")),
    ("Raw Reason", lambda r: r.get("reason", "")),
]


def write_rows(path, header, rows):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding=ENCODING) as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)
    return path


def write_disputes(payload, path):
    disputes = sorted(payload["disputes"], key=lambda r: (r.get("chargeback_date") or ""), reverse=True)
    rows = [[get(r) for _, get in DISPUTE_COLUMNS] for r in disputes]
    return write_rows(path, [name for name, _ in DISPUTE_COLUMNS], rows), len(rows)


def _money_cells(rows):
    """Per-currency totals as one 'USD 1234.56; NZD 78.90' cell - the amounts
    are never added together, matching how the dashboard reports them."""
    by = {}
    for r in rows:
        by[r.get("currency") or ""] = by.get(r.get("currency") or "", 0) + (r.get("amount") or 0)
    return "; ".join(f"{cur} {amt:.2f}" for cur, amt in sorted(by.items(), key=lambda kv: -kv[1]))


def write_summaries(payload, base):
    disputes = payload["disputes"]
    written = []

    store_rows = []
    for s in payload["stores"]:
        subset = [r for r in disputes if r["store"] == s["key"]]
        store_rows.append([
            s["label"], s.get("domain", ""), s["total"], s["open"], s["needs_action"], s["overdue"],
            s["under_review"], s["won"], s["lost"], s["closed_other"],
            "" if s["win_rate"] is None else s["win_rate"],
            "" if s["loss_rate"] is None else s["loss_rate"],
            _money_cells([r for r in subset if r["outcome"] == "open"]), _money_cells(subset),
            s.get("fetch_error") or "",
        ])
    totals = payload["totals"]
    store_rows.append([
        "ALL STORES", "", totals["total"], totals["open"], totals["needs_action"], totals["overdue"],
        totals["under_review"], totals["won"], totals["lost"], totals["closed_other"],
        "" if totals["win_rate"] is None else totals["win_rate"],
        "" if totals["loss_rate"] is None else totals["loss_rate"],
        _money_cells([r for r in disputes if r["outcome"] == "open"]), _money_cells(disputes), "",
    ])
    written.append(write_rows(f"{base}-by-store.csv", [
        "Store", "Domain", "Total", "Open", "Needs Action", "Overdue", "Under Review",
        "Won", "Lost", "Other Closed", "Win Rate %", "Loss Rate %",
        "Value At Risk", "Total Value", "Fetch Error",
    ], store_rows))

    written.append(write_rows(f"{base}-by-status.csv", [
        "Status", "Outcome", "Count", "% Of All", "Value",
    ], [
        [s["label"], s["outcome"], s["count"],
         round(100 * s["count"] / len(disputes), 1) if disputes else 0,
         _money_cells([r for r in disputes if r["status"] == s["status"]])]
        for s in payload["status_breakdown"]
    ]))

    written.append(write_rows(f"{base}-by-reason.csv", [
        "Reason", "Category", "Count", "% Of All", "Win Rate %", "Value", "Suggested Action",
    ], [
        [r["label"], r["category"], r["count"], r["pct"],
         "" if r["win_rate"] is None else r["win_rate"],
         _money_cells([d for d in disputes if d["reason"] == r["reason"]]), r["action"]]
        for r in payload["reasons"]
    ]))
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default=DEFAULT_DATA)
    parser.add_argument("--out", help="Detail CSV path (default: dist/chargebacks-<generated date>.csv)")
    parser.add_argument("--summaries", action="store_true", help="Also write by-store / by-status / by-reason files")
    args = parser.parse_args()

    if not os.path.exists(args.data):
        print(f"No data at {args.data}. Run  python fetch_chargebacks.py  first.")
        return 1

    with open(args.data) as handle:
        payload = json.load(handle)

    stamp = (payload.get("generated_at") or "")[:10] or "latest"
    out = args.out or os.path.join("dist", f"chargebacks-{stamp}.csv")
    path, count = write_disputes(payload, out)
    print(f"{count} disputes -> {path}")

    if args.summaries:
        base = out[:-4] if out.lower().endswith(".csv") else out
        for extra in write_summaries(payload, base):
            print(f"summary      -> {extra}")

    if payload.get("meta", {}).get("sample"):
        print("\nNOTE: this payload is generated sample data, not real chargebacks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
