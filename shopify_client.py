import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_VERSION = "2024-01"


def _next_page_url(link_header: str) -> str | None:
    for part in link_header.split(","):
        section = part.split(";")
        if len(section) < 2 or 'rel="next"' not in section[1]:
            continue
        return section[0].strip().strip("<>")
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

    @staticmethod
    def keys_from_env() -> list[str]:
        suffix = "_SHOPIFY_DOMAIN"
        keys = [name[: -len(suffix)] for name in os.environ if name.endswith(suffix)]
        return sorted(k for k in keys if os.environ.get(f"{k}_SHOPIFY_ACCESS_TOKEN"))

    def get(self, path: str, params: dict | None = None) -> dict:
        response = self._session.get(f"{self.base_url}/{path.lstrip('/')}", params=params)
        response.raise_for_status()
        return response.json()

    def get_paginated(self, path: str, key: str, params: dict | None = None) -> list[dict]:
        """Follow Shopify's Link-header cursor pagination and return every record."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        records: list[dict] = []
        while url:
            response = self._session.get(url, params=params)
            response.raise_for_status()
            records.extend(response.json().get(key, []))
            url = _next_page_url(response.headers.get("Link", ""))
            # page_info is a complete cursor - it cannot be combined with the original filters.
            params = None
        return records

    def shop_info(self) -> dict:
        return self.get("shop.json")["shop"]

    def products(self, limit: int = 50) -> list[dict]:
        return self.get("products.json", params={"limit": limit})["products"]

    def orders(self, limit: int = 50, status: str = "any") -> list[dict]:
        return self.get("orders.json", params={"limit": limit, "status": status})["orders"]

    def orders_in_range(
        self,
        created_at_min: str,
        created_at_max: str,
        fields: str | None = None,
        status: str = "any",
    ) -> list[dict]:
        """Every order created in [created_at_min, created_at_max], across all pages.

        Both bounds are ISO 8601 with an explicit UTC offset and are inclusive.
        status="any" so cancelled, archived and unpaid orders are not silently dropped.
        """
        params = {
            "status": status,
            "limit": 250,
            "created_at_min": created_at_min,
            "created_at_max": created_at_max,
        }
        if fields:
            params["fields"] = fields
        return self.get_paginated("orders.json", "orders", params=params)

    def disputes(self, limit: int = 250) -> list[dict]:
        return self.get("shopify_payments/disputes.json", params={"limit": limit})["disputes"]

    def order(self, order_id: int) -> dict:
        return self.get(f"orders/{order_id}.json")["order"]
