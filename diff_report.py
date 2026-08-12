"""
Compare the live disputes_export.csv against a snapshot exported from the
Google Sheet (markdown pipe-table pasted from Drive's read_file_content) and
produce a diff: brand-new disputes and status changes on ones already there.

Usage: python3 diff_report.py path/to/sheet_snapshot.md
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


def load_live_disputes(path: str) -> list[dict]:
    with open(path) as f:
        return list(csv.DictReader(f))


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: diff_report.py <sheet_snapshot.md>")
        sys.exit(1)

    sheet_rows = parse_sheet_snapshot(sys.argv[1])
    live = load_live_disputes("disputes_export.csv")

    new_rows = []
    changed_rows = []
    for d in live:
        dispute_id = d["dispute_id"]
        outcome = d["outcome"]
        if dispute_id not in sheet_rows:
            new_rows.append(d)
        else:
            old = sheet_rows[dispute_id]
            if old["outcome"] != outcome or old["status"] != d["status"]:
                changed_rows.append({**d, "previous_status": old["status"], "previous_outcome": old["outcome"]})

    print(f"NEW disputes since last sheet update: {len(new_rows)}")
    print(f"STATUS CHANGES on existing disputes: {len(changed_rows)}")

    with open("diff_new_disputes.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["store", "order_number", "customer_name", "customer_email", "amount", "currency",
             "concern_reason", "status", "outcome", "initiated_at", "dispute_id"]
        )
        for d in sorted(new_rows, key=lambda x: x.get("initiated_at") or ""):
            writer.writerow(
                [d["store"], d["order_number"], d["customer_name"], d["customer_email"], d["amount"],
                 d["currency"], d["reason"], d["status"], d["outcome"], d.get("initiated_at"), d["dispute_id"]]
            )

    with open("diff_status_changes.csv", "w", newline="") as f:
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

    print("Wrote diff_new_disputes.csv and diff_status_changes.csv")


if __name__ == "__main__":
    main()
