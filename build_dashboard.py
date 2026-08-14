"""Render the chargeback dashboard into one self-contained HTML file.

    python build_dashboard.py                                  # data/chargebacks.json
    python build_dashboard.py --data data/chargebacks-sample.json
    python build_dashboard.py --out reports/chargebacks.html

The output embeds its data, so it opens straight from disk and can be published
as an Artifact without any external requests.
"""

import argparse
import json
import os

from chargeback_model import REASON_ACTIONS

TEMPLATE_PATH = os.path.join("templates", "dashboard.html")
DEFAULT_DATA = os.path.join("data", "chargebacks.json")
DEFAULT_OUT = os.path.join("dist", "chargeback-dashboard.html")


def embed(value: object) -> str:
    """JSON for a <script> block: escape the characters that could close it early."""
    return (
        json.dumps(value, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default=DEFAULT_DATA, help=f"Payload to render (default: {DEFAULT_DATA})")
    parser.add_argument("--template", default=TEMPLATE_PATH)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()

    if not os.path.exists(args.data):
        print(
            f"No data at {args.data}.\n"
            "Run  python fetch_chargebacks.py  to pull live disputes, or\n"
            "    python sample_data.py  to render the layout with sample figures.",
        )
        return 1

    with open(args.data) as handle:
        payload = json.load(handle)
    with open(args.template) as handle:
        template = handle.read()

    html = template.replace("__DASHBOARD_DATA__", embed(payload))
    html = html.replace("__REASON_ACTIONS__", embed(REASON_ACTIONS))

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as handle:
        handle.write(html)

    totals = payload.get("totals", {})
    tag = " (SAMPLE DATA)" if payload.get("meta", {}).get("sample") else ""
    print(
        f"Dashboard written to {args.out}{tag}\n"
        f"  {totals.get('total', 0)} disputes · {totals.get('open', 0)} open · "
        f"{totals.get('needs_action', 0)} needing a response · win rate {totals.get('win_rate')}%"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
