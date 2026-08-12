import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

API_VERSION = "2024-01"


def _next_page_info(link_header: str) -> str | None:
    for part in link_header.split(","):
        if 'rel="next"' not in part:
            continue
        match = re.search(r"page_info=([^&>]+)", part)
        if match:
            return match.group(1)
    return None


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

    def get(self, path: str, params: dict | None = None) -> dict:
        response = self._session.get(f"{self.base_url}/{path.lstrip('/')}", params=params)
        response.raise_for_status()
        return response.json()

    def shop_info(self) -> dict:
        return self.get("shop.json")["shop"]

    def products(self, limit: int = 50) -> list[dict]:
        return self.get("products.json", params={"limit": limit})["products"]

    def orders(self, limit: int = 50, status: str = "any") -> list[dict]:
        return self.get("orders.json", params={"limit": limit, "status": status})["orders"]

    def orders_all(self, status: str = "any", created_at_min: str | None = None) -> list[dict]:
        """Fetch every order, following cursor pagination."""
        all_orders = []
        params = {"limit": 250, "status": status}
        if created_at_min:
            params["created_at_min"] = created_at_min
        while True:
            response = self._session.get(f"{self.base_url}/orders.json", params=params)
            response.raise_for_status()
            all_orders.extend(response.json()["orders"])
            next_page_info = _next_page_info(response.headers.get("Link", ""))
            if not next_page_info:
                break
            params = {"limit": 250, "page_info": next_page_info}
        return all_orders

    def disputes(self, limit: int = 250) -> list[dict]:
        return self.get("shopify_payments/disputes.json", params={"limit": limit})["disputes"]

    def order(self, order_id: int) -> dict:
        return self.get(f"orders/{order_id}.json")["order"]
