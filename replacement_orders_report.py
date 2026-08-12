import csv

from shopify_client import ShopifyStore

STORE_KEYS = ["MARY", "LYN", "MAGIE"]
REPLACEMENT_TAG = "replacement"


def has_tag(order: dict, tag: str) -> bool:
    raw = order.get("tags", "")
    return tag.lower() in {t.strip().lower() for t in raw.split(",") if t.strip()}


def main() -> None:
    all_replacements = []
    for key in STORE_KEYS:
        store = ShopifyStore.from_env(key)
        try:
            orders = store.orders_all()
        except Exception as exc:
            print(f"[{key}] failed to fetch orders: {exc}")
            continue
        for o in orders:
            if has_tag(o, REPLACEMENT_TAG):
                o["_store"] = key
                all_replacements.append(o)

    if not all_replacements:
        print("No replacement orders found on any store.")
        return

    print(f"Found {len(all_replacements)} replacement order(s) across {len(STORE_KEYS)} store(s).")

    out_path = "replacement_orders_export.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["store", "order_id", "order_number", "name", "customer_email", "customer_name",
             "created_at", "total_price", "currency", "financial_status", "fulfillment_status",
             "tags", "note"]
        )
        for o in sorted(all_replacements, key=lambda x: (x["_store"], x["created_at"])):
            customer = o.get("customer") or {}
            customer_name = " ".join(
                filter(None, [customer.get("first_name"), customer.get("last_name")])
            ).strip()
            writer.writerow(
                [o["_store"], o["id"], o.get("order_number"), o.get("name"),
                 o.get("email") or o.get("contact_email"), customer_name, o.get("created_at"),
                 o.get("total_price"), o.get("currency"), o.get("financial_status"),
                 o.get("fulfillment_status"), o.get("tags"), o.get("note")]
            )
    print(f"Full export written to {out_path}")


if __name__ == "__main__":
    main()
