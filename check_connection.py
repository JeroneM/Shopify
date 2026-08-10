import sys

from shopify_client import ShopifyStore


def main() -> None:
    key = sys.argv[1] if len(sys.argv) > 1 else "MARY"
    store = ShopifyStore.from_env(key)
    shop = store.shop_info()
    print(f"Connected to {store.name}: {shop['name']} ({shop['domain']})")


if __name__ == "__main__":
    main()
