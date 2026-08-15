"""Regroup the replacement-order export so fulfilment state reads at a glance.

Reads the export produced by replacement_orders_report.py and rewrites the same
rows and columns ordered by fulfilment state - not-yet-fulfilled first, since
those are the actionable ones - then by store and creation time within each group.

No rows are added, dropped or altered; only their order changes.

Usage:
    python group_by_fulfillment.py
    python group_by_fulfillment.py --split      # also write one file per group
"""

import csv
import sys

IN_PATH = "replacement_orders_export.csv"
OUT_PATH = "replacement_orders_by_fulfillment.csv"

# Unfulfilled first, then partially-handled states, then done.
GROUP_ORDER = ["unfulfilled", "partial", "restocked", "fulfilled"]

SPLIT_PATHS = {
    "unfulfilled": "replacement_orders_not_fulfilled.csv",
    "fulfilled": "replacement_orders_fulfilled.csv",
}


def sort_key(row: dict) -> tuple:
    status = (row.get("fulfillment_status") or "").casefold()
    rank = GROUP_ORDER.index(status) if status in GROUP_ORDER else len(GROUP_ORDER)
    return (rank, status, row.get("store", ""), row.get("created_at", ""))


def write(path: str, header: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    try:
        with open(IN_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames or []
            rows = list(reader)
    except FileNotFoundError:
        sys.exit(f"{IN_PATH} not found - run replacement_orders_report.py first.")

    if "fulfillment_status" not in header:
        sys.exit(f"{IN_PATH} has no fulfillment_status column - re-run replacement_orders_report.py.")

    rows.sort(key=sort_key)
    write(OUT_PATH, header, rows)

    counts: dict[str, int] = {}
    for row in rows:
        status = row["fulfillment_status"] or "unfulfilled"
        counts[status] = counts.get(status, 0) + 1

    print(f"{len(rows)} orders written to {OUT_PATH}")
    for status in sorted(counts, key=lambda s: sort_key({"fulfillment_status": s})):
        print(f"  {status}: {counts[status]}")

    if "--split" in sys.argv:
        for status, path in SPLIT_PATHS.items():
            group = [r for r in rows if (r["fulfillment_status"] or "").casefold() == status]
            write(path, header, group)
            print(f"{len(group)} {status} orders written to {path}")


if __name__ == "__main__":
    main()
