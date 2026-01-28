"""
Bitrefill API Client - Buy gift cards with crypto
"""

import os
import requests
from typing import Optional, List, Dict, Any
import streamlit as st


class BitrefillClient:
    """Client for Bitrefill API"""

    BASE_URL = "https://api.bitrefill.com"

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initialize Bitrefill client

        Args:
            api_key: Bitrefill API key (or from env BITREFILL_API_KEY)
            api_secret: Bitrefill API secret (or from env BITREFILL_API_SECRET)
        """
        self.api_key = api_key or os.getenv("BITREFILL_API_KEY")
        self.api_secret = api_secret or os.getenv("BITREFILL_API_SECRET")

        if not self.api_key or not self.api_secret:
            st.warning("⚠️ Bitrefill API credentials not configured. Using mock mode.")
            self.mock_mode = True
        else:
            self.mock_mode = False

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make authenticated request to Bitrefill API"""
        if self.mock_mode:
            return self._mock_response(endpoint, **kwargs)

        url = f"{self.BASE_URL}{endpoint}"

        headers = {
            "X-API-Key": self.api_key,
            "X-API-Secret": self.api_secret,
            "Content-Type": "application/json"
        }

        try:
            response = requests.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Bitrefill API error: {e}")
            return None

    def search_products(self, query: str = "", country: str = "US", limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for gift cards and products

        Args:
            query: Search query (e.g., "amazon", "uber")
            country: Country code (default "US")
            limit: Maximum results

        Returns:
            List of products with name, description, price range
        """
        endpoint = f"/v1/inventory?country={country}"

        response = self._make_request("GET", endpoint)

        if not response:
            return []

        # Filter by query if provided
        products = response.get("products", [])

        if query:
            query_lower = query.lower()
            products = [p for p in products if query_lower in p.get("name", "").lower()]

        # Format results
        results = []
        for product in products[:limit]:
            results.append({
                "id": product.get("id"),
                "name": product.get("name"),
                "description": product.get("description", ""),
                "currency": product.get("currency", "USD"),
                "min_amount": product.get("range", {}).get("min"),
                "max_amount": product.get("range", {}).get("max"),
                "country": product.get("country"),
                "image_url": product.get("logoImage"),
                "category": product.get("category")
            })

        return results

    def get_product_details(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a product

        Args:
            product_id: Product ID from search results

        Returns:
            Product details including pricing, terms, etc.
        """
        endpoint = f"/v1/products/{product_id}"

        response = self._make_request("GET", endpoint)

        if not response:
            return None

        return {
            "id": response.get("id"),
            "name": response.get("name"),
            "description": response.get("description"),
            "terms": response.get("terms"),
            "currency": response.get("currency"),
            "min_amount": response.get("range", {}).get("min"),
            "max_amount": response.get("range", {}).get("max"),
            "delivery_method": response.get("deliveryMethod"),
            "redemption_instructions": response.get("redemptionInstructions")
        }

    def create_order(
        self,
        product_id: str,
        amount: float,
        email: str,
        payment_method: str = "crypto"
    ) -> Optional[Dict[str, Any]]:
        """
        Create an order for a gift card

        Args:
            product_id: Product ID
            amount: Amount in product currency (USD)
            email: Email to send gift card to
            payment_method: Payment method ("crypto" for cryptocurrency)

        Returns:
            Order details with payment address and code (after payment)
        """
        endpoint = "/v1/orders"

        data = {
            "productId": product_id,
            "amount": amount,
            "email": email,
            "paymentMethod": payment_method
        }

        response = self._make_request("POST", endpoint, json=data)

        if not response:
            return None

        return {
            "order_id": response.get("orderId"),
            "status": response.get("status"),
            "payment_address": response.get("paymentAddress"),
            "payment_amount": response.get("paymentAmount"),
            "payment_currency": response.get("paymentCurrency"),
            "expires_at": response.get("expiresAt"),
            "gift_card_code": response.get("giftCardCode"),  # Available after payment
            "pin": response.get("pin")  # If applicable
        }

    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Check order status

        Args:
            order_id: Order ID from create_order

        Returns:
            Order status and gift card details
        """
        endpoint = f"/v1/orders/{order_id}"

        response = self._make_request("GET", endpoint)

        if not response:
            return None

        return {
            "order_id": response.get("orderId"),
            "status": response.get("status"),  # "pending", "paid", "completed", "failed"
            "gift_card_code": response.get("giftCardCode"),
            "pin": response.get("pin"),
            "redemption_url": response.get("redemptionUrl")
        }

    def _mock_response(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Mock responses for testing without API credentials"""

        if "/inventory" in endpoint:
            # Mock product search
            return {
                "products": [
                    {
                        "id": "amazon-us",
                        "name": "Amazon.com Gift Card",
                        "description": "Buy anything on Amazon.com",
                        "currency": "USD",
                        "range": {"min": 10, "max": 500},
                        "country": "US",
                        "logoImage": "https://cdn.bitrefill.com/media/amazon.png",
                        "category": "shopping"
                    },
                    {
                        "id": "uber-us",
                        "name": "Uber Gift Card",
                        "description": "Ride with Uber",
                        "currency": "USD",
                        "range": {"min": 25, "max": 200},
                        "country": "US",
                        "logoImage": "https://cdn.bitrefill.com/media/uber.png",
                        "category": "transportation"
                    },
                    {
                        "id": "netflix-us",
                        "name": "Netflix Gift Card",
                        "description": "Stream movies and shows",
                        "currency": "USD",
                        "range": {"min": 25, "max": 100},
                        "country": "US",
                        "logoImage": "https://cdn.bitrefill.com/media/netflix.png",
                        "category": "entertainment"
                    },
                    {
                        "id": "starbucks-us",
                        "name": "Starbucks Gift Card",
                        "description": "Coffee and more",
                        "currency": "USD",
                        "range": {"min": 10, "max": 100},
                        "country": "US",
                        "logoImage": "https://cdn.bitrefill.com/media/starbucks.png",
                        "category": "food"
                    }
                ]
            }

        elif "/products/" in endpoint:
            # Mock product details
            return {
                "id": "amazon-us",
                "name": "Amazon.com Gift Card",
                "description": "Use this gift card to buy anything on Amazon.com",
                "terms": "Valid only on Amazon.com. No expiration date.",
                "currency": "USD",
                "range": {"min": 10, "max": 500},
                "deliveryMethod": "email",
                "redemptionInstructions": "Enter code at checkout on Amazon.com"
            }

        elif endpoint == "/v1/orders":
            # Mock order creation - return completed immediately for demo
            import uuid
            import random
            import string
            mock_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
            mock_code = f"{mock_code[:4]}-{mock_code[4:8]}-{mock_code[8:12]}-{mock_code[12:]}"
            return {
                "orderId": f"mock-{uuid.uuid4().hex[:8]}",
                "status": "completed",  # Completed immediately for demo
                "paymentAddress": None,
                "paymentAmount": kwargs.get("json", {}).get("amount", 50),
                "paymentCurrency": "USDC",
                "expiresAt": None,
                "giftCardCode": mock_code,  # Code delivered immediately
                "pin": None
            }

        elif "/orders/" in endpoint:
            # Mock order status
            return {
                "orderId": endpoint.split("/")[-1],
                "status": "completed",
                "giftCardCode": "MOCK-XXXX-YYYY-ZZZZ",
                "pin": "1234",
                "redemptionUrl": "https://www.amazon.com/gc/redeem"
            }

        return {}


# Singleton instance
_bitrefill_client = None

def get_bitrefill_client() -> BitrefillClient:
    """Get Bitrefill client singleton"""
    global _bitrefill_client
    if _bitrefill_client is None:
        _bitrefill_client = BitrefillClient()
    return _bitrefill_client
