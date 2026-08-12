"""
Compare the live disputes_export.csv against a snapshot exported from the
Google Sheet (markdown pipe-table pasted from Drive's read_file_content) and
produce a diff: brand-new disputes and status changes on ones already there.

Google Drive's tools only support reading and creating new files, not
editing an existing spreadsheet's cells - so this script's output is meant
to be handed to a human (or pasted in) rather than written back automatically.

Usage: python3 diff_report.py path/to/sheet_snapshot.md
Requires disputes_export.csv and disputes_by_date.csv (run disputes_report.py first).

Outputs:
  sheet_new_rows.csv       - new disputes, in the sheet's exact column order, ready to append
  sheet_status_changes.csv - dispute_ids already in the sheet whose status/outcome changed
"""
import csv
import sys

SHEET_COLUMNS = [
    "date_submitted", "disputes_that_day", "store", "order_number", "customer_name",
    "customer_email", "amount", "currency", "concern_reason", "status", "outcome", "dispute_id",
]


def parse_sheet_snapshot(path: str) -> dict[str, dict]:
    """Returns {dispute_id: row_dict} from a markdown pipe-table export of the sheet."""
    rows: dict[str, dict] = {}
    with open(path) as f:
        lines = [line.strip() for line in f if line.strip().startswith("|")]
    # First row is the (blank) header, second is the alignment row, third is the real header.
    data_lines = lines[3:]
    for line in data_lines:
        cells = [c.strip().replace("\\_", "_") for c in line.strip("|").split("|")]
        if len(cells) != len(SHEET_COLUMNS):
            continue
        row = dict(zip(SHEET_COLUMNS, cells))
        rows[row["dispute_id"]] = row
    return rows


def load_csv(path: str) -> list[dict]:
    with open(path) as f:
        return list(csv.DictReader(f))


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: diff_report.py <sheet_snapshot.md>")
        sys.exit(1)

    sheet_rows = parse_sheet_snapshot(sys.argv[1])
    live = load_csv("disputes_export.csv")
    by_date_rows = {r["dispute_id"]: r for r in load_csv("disputes_by_date.csv")}

    new_ids = set()
    changed_rows = []
    for d in live:
        dispute_id = d["dispute_id"]
        if dispute_id not in sheet_rows:
            new_ids.add(dispute_id)
        else:
            old = sheet_rows[dispute_id]
            if old["outcome"] != d["outcome"] or old["status"] != d["status"]:
                changed_rows.append({**d, "previous_status": old["status"], "previous_outcome": old["outcome"]})

    new_rows = sorted(
        (by_date_rows[i] for i in new_ids if i in by_date_rows),
        key=lambda r: (r["date_submitted"], r["store"]),
    )

    with open("sheet_new_rows.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SHEET_COLUMNS)
        writer.writeheader()
        writer.writerows(new_rows)

    with open("sheet_status_changes.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["store", "order_number", "customer_name", "customer_email", "dispute_id",
             "previous_status", "previous_outcome", "new_status", "new_outcome"]
        )
        for d in changed_rows:
            writer.writerow(
                [d["store"], d["order_number"], d["customer_name"], d["customer_email"], d["dispute_id"],
                 d["previous_status"], d["previous_outcome"], d["status"], d["outcome"]]
            )

    print(f"NEW disputes since last sheet update: {len(new_rows)} -> sheet_new_rows.csv")
    print(f"STATUS CHANGES on existing disputes: {len(changed_rows)} -> sheet_status_changes.csv")


if __name__ == "__main__":
    main()
