#!/usr/bin/env python3
"""Merge the Commslayer ticket batches into the dashboard template.

Reads data/tickets_batch*.json, sorts by ticket number, and injects the
combined array into dashboard_template.html at the /*__DATA__*/ marker,
writing customer_issue_dashboard.html.
"""
import glob
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent
MARKER = "/*__DATA__*/[]"


def load_tickets():
    tickets = {}
    files = sorted(glob.glob(str(ROOT / "data" / "tickets_batch*.json")))
    if not files:
        sys.exit("No ticket batch files found in data/")
    for path in files:
        with open(path, encoding="utf-8") as fh:
            for row in json.load(fh):
                if row["t"] in tickets:
                    sys.exit(f"Duplicate ticket {row['t']} in {path}")
                tickets[row["t"]] = row
    return [tickets[k] for k in sorted(tickets)]


def main():
    tickets = load_tickets()
    numbers = [t["t"] for t in tickets]
    gaps = sorted(set(range(min(numbers), max(numbers) + 1)) - set(numbers))
    template = (ROOT / "dashboard_template.html").read_text(encoding="utf-8")
    if MARKER not in template:
        sys.exit("Data marker not found in template")
    payload = json.dumps(tickets, ensure_ascii=False, separators=(",", ":"))
    out = template.replace(MARKER, payload)
    (ROOT / "customer_issue_dashboard.html").write_text(out, encoding="utf-8")

    print(f"tickets:  {len(tickets)}")
    print(f"range:    C-{min(numbers)} to C-{max(numbers)}")
    print(f"gaps:     {gaps if gaps else 'none (fully contiguous)'}")
    print(f"dates:    {min(t['created'] for t in tickets)} to {max(t['created'] for t in tickets)}")
    print("written:  customer_issue_dashboard.html")


if __name__ == "__main__":
    main()
