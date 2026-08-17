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
BRAND_MARKER = "/*__BRANDS__*/null"
DEFAULT_BRAND = "Simply Elsie"


def load_tickets():
    tickets = {}
    patterns = ("tickets_batch*.json", "tickets_lyn.json", "tickets_mary.json", "tickets_maggie.json")
    files = sorted(p for pat in patterns for p in glob.glob(str(ROOT / "data" / pat)))
    if not files:
        sys.exit("No ticket files found in data/")
    for path in files:
        with open(path, encoding="utf-8") as fh:
            for row in json.load(fh):
                row.setdefault("brand", DEFAULT_BRAND)
                key = (row["brand"], row["t"])
                if key in tickets:
                    sys.exit(f"Duplicate ticket {key} in {path}")
                tickets[key] = row
    return [tickets[k] for k in sorted(tickets)]


def main():
    tickets = load_tickets()
    brands = json.loads((ROOT / "data" / "brands.json").read_text(encoding="utf-8"))

    template = (ROOT / "dashboard_template.html").read_text(encoding="utf-8")
    for marker in (MARKER, BRAND_MARKER):
        if marker not in template:
            sys.exit(f"Marker {marker} not found in template")
    out = template.replace(MARKER, json.dumps(tickets, ensure_ascii=False, separators=(",", ":")))
    out = out.replace(BRAND_MARKER, json.dumps(brands, ensure_ascii=False, separators=(",", ":")))
    (ROOT / "customer_issue_dashboard.html").write_text(out, encoding="utf-8")

    print(f"tickets:  {len(tickets)} across {len({t['brand'] for t in tickets})} brands")
    for b in sorted({t["brand"] for t in tickets}):
        rows = [t["t"] for t in tickets if t["brand"] == b]
        gaps = sorted(set(range(min(rows), max(rows) + 1)) - set(rows))
        print(f"  {b:<16} {len(rows):>3} tickets  C-{min(rows)}..C-{max(rows)}  "
              f"{'contiguous' if not gaps else str(len(gaps)) + ' gaps'}")
    print(f"brands:   {len(brands['brands'])} population records "
          f"({brands['window']['from']} to {brands['window']['to']})")
    print(f"dates:    {min(t['created'] for t in tickets)} to {max(t['created'] for t in tickets)}")
    print("written:  customer_issue_dashboard.html")


if __name__ == "__main__":
    main()
