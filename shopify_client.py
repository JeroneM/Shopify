import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

API_VERSION = "2024-01"


class ShopifyStore:
    def __init__(self, name: str, domain: str, access_token: str):
        self.name = name
        self.domain = domain
        self.base_url = f"https://{domain}/admin/api/{API_VERSION}"
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-Shopify-Access-Token": access_token,
                "Content-Type": "application/json",
            }
        )

    @classmethod
    def from_env(cls, key: str) -> "ShopifyStore":
        domain = os.environ[f"{key}_SHOPIFY_DOMAIN"]
        token = os.environ[f"{key}_SHOPIFY_ACCESS_TOKEN"]
        return cls(name=key, domain=domain, access_token=token)

    @classmethod
    def configured_in_env(cls, key: str) -> bool:
        return bool(os.environ.get(f"{key}_SHOPIFY_DOMAIN") and os.environ.get(f"{key}_SHOPIFY_ACCESS_TOKEN"))

    def get(self, path: str, params: dict | None = None) -> dict:
        response = self._session.get(f"{self.base_url}/{path.lstrip('/')}", params=params)
        response.raise_for_status()
        return response.json()

    def get_all(self, path: str, root_key: str, params: dict | None = None) -> list[dict]:
        """Follow Shopify's Link-header cursor pagination until every page is read."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        params = dict(params or {})
        items: list[dict] = []
        while url:
            response = self._session.get(url, params=params)
            response.raise_for_status()
            items.extend(response.json().get(root_key, []))
            url = _next_page_url(response.headers.get("Link", ""))
            params = None  # the cursor URL already carries every parameter
        return items

    def shop_info(self) -> dict:
        return self.get("shop.json")["shop"]

    def products(self, limit: int = 50) -> list[dict]:
        return self.get("products.json", params={"limit": limit})["products"]

    def orders(self, limit: int = 50, status: str = "any") -> list[dict]:
        return self.get("orders.json", params={"limit": limit, "status": status})["orders"]

    def disputes(self, limit: int = 250) -> list[dict]:
        """Every Shopify Payments dispute on the shop, across all pages."""
        return self.get_all("shopify_payments/disputes.json", "disputes", params={"limit": limit})

    def order(self, order_id: int) -> dict:
        return self.get(f"orders/{order_id}.json")["order"]


def _next_page_url(link_header: str) -> str | None:
    for part in link_header.split(","):
        match = re.match(r'\s*<([^>]+)>\s*;\s*rel="?next"?', part)
        if match:
            return match.group(1)
    return None
