import os
import re
import time

import requests
from dotenv import load_dotenv

load_dotenv()

API_VERSION = "2024-01"

# Shopify REST is leaky-bucket rate limited (40 burst, 2/s leak). On a 429 the
# response carries Retry-After; on 5xx we back off and retry a few times.
MAX_RETRIES = 5
BACKOFF_BASE_SECONDS = 1.0


class ShopifyStore:
    def __init__(self, name: str, domain: str, access_token: str, label: str | None = None):
        self.name = name
        self.label = label or name.replace("_", " ").title()
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
        # Two token spellings are supported so existing environments keep working:
        # the per-store prefix form and the SHOPIFY_TOKEN_<KEY> form.
        token = os.environ.get(f"{key}_SHOPIFY_ACCESS_TOKEN") or os.environ.get(f"SHOPIFY_TOKEN_{key}")
        if not token:
            raise KeyError(f"{key}_SHOPIFY_ACCESS_TOKEN (or SHOPIFY_TOKEN_{key})")
        return cls(
            name=key,
            domain=domain,
            access_token=token,
            label=os.environ.get(f"{key}_SHOPIFY_LABEL"),
        )

    def _request(self, path: str, params: dict | None = None) -> requests.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        for attempt in range(MAX_RETRIES):
            response = self._session.get(url, params=params, timeout=30)
            if response.status_code == 429:
                wait = float(response.headers.get("Retry-After", BACKOFF_BASE_SECONDS * 2))
                time.sleep(wait)
                continue
            if response.status_code >= 500 and attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFF_BASE_SECONDS * (2**attempt))
                continue
            response.raise_for_status()
            return response
        response.raise_for_status()
        return response

    def get(self, path: str, params: dict | None = None) -> dict:
        return self._request(path, params).json()

    def get_paginated(self, path: str, key: str, params: dict | None = None) -> list[dict]:
        """Follow Shopify's Link-header cursor pagination and return every page."""
        items: list[dict] = []
        page_params = dict(params or {})
        while True:
            response = self._request(path, page_params)
            items.extend(response.json().get(key, []))
            next_url = _next_page_url(response.headers.get("Link", ""))
            if not next_url:
                return items
            page_info = _query_value(next_url, "page_info")
            if not page_info:
                return items
            # page_info is exclusive of every other filter except limit.
            page_params = {"limit": page_params.get("limit", 250), "page_info": page_info}

    def shop_info(self) -> dict:
        return self.get("shop.json")["shop"]

    def products(self, limit: int = 50) -> list[dict]:
        return self.get("products.json", params={"limit": limit})["products"]

    def orders(self, limit: int = 50, status: str = "any") -> list[dict]:
        return self.get("orders.json", params={"limit": limit, "status": status})["orders"]

    def disputes(self, limit: int = 250, initiated_at: str | None = None) -> list[dict]:
        """All Shopify Payments disputes, walking since_id until the store is exhausted.

        The disputes endpoint predates cursor pagination, so it pages on since_id
        rather than the Link header used everywhere else.
        """
        collected: list[dict] = []
        since_id = 0
        while True:
            params: dict = {"limit": limit, "since_id": since_id}
            if initiated_at:
                params["initiated_at"] = initiated_at
            page = self.get("shopify_payments/disputes.json", params=params).get("disputes", [])
            if not page:
                return collected
            collected.extend(page)
            if len(page) < limit:
                return collected
            since_id = max(int(d["id"]) for d in page)

    def order(self, order_id: int, fields: str | None = None) -> dict:
        params = {"fields": fields} if fields else None
        return self.get(f"orders/{order_id}.json", params=params)["order"]


def _next_page_url(link_header: str) -> str | None:
    for part in link_header.split(","):
        match = re.search(r'<([^>]+)>;\s*rel="next"', part.strip())
        if match:
            return match.group(1)
    return None


def _query_value(url: str, key: str) -> str | None:
    match = re.search(rf"[?&]{re.escape(key)}=([^&]+)", url)
    return match.group(1) if match else None


def discover_store_keys() -> list[str]:
    """Store keys configured in the environment, e.g. MARY from MARY_SHOPIFY_DOMAIN.

    SHOPIFY_STORES pins an explicit ordered list when you want to override
    auto-discovery.
    """
    pinned = os.environ.get("SHOPIFY_STORES", "").strip()
    if pinned:
        return [key.strip().upper() for key in pinned.split(",") if key.strip()]
    keys = [name[: -len("_SHOPIFY_DOMAIN")] for name in os.environ if name.endswith("_SHOPIFY_DOMAIN")]
    return sorted(keys)


def load_stores(keys: list[str] | None = None) -> list[ShopifyStore]:
    stores = []
    for key in keys or discover_store_keys():
        try:
            stores.append(ShopifyStore.from_env(key))
        except KeyError as exc:
            print(f"[{key}] skipped - missing environment variable {exc}")
    return stores
