"""
Merchant adapters for crypto-native purchases
Each adapter handles API integration for merchants that accept crypto
"""

from typing import Dict, Optional, List
import json


class MerchantAdapter:
    """Base class for merchant integrations"""

    def __init__(self):
        self.name = ""
        self.accepts_crypto = []  # List of accepted cryptos
        self.requires_account = False

    def search_products(self, query: str, **kwargs) -> List[Dict]:
        """Search for products/services"""
        raise NotImplementedError

    def get_price(self, product_id: str) -> Dict:
        """Get pricing in crypto"""
        raise NotImplementedError

    def create_order(self, product_id: str, **kwargs) -> Dict:
        """Create order and get payment details"""
        raise NotImplementedError

    def check_payment(self, order_id: str) -> Dict:
        """Check if payment was confirmed"""
        raise NotImplementedError


class PorkbunAdapter(MerchantAdapter):
    """Porkbun domain registrar - accepts crypto directly"""

    def __init__(self, api_key: str, api_secret: str):
        super().__init__()
        self.name = "Porkbun"
        self.accepts_crypto = ["BTC", "ETH", "USDC", "LTC", "DOGE"]
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.porkbun.com/api/json/v3"

    def search_domains(self, domain: str) -> Dict:
        """Check if domain is available"""
        # Porkbun API endpoint
        return {
            "domain": domain,
            "available": True,  # Would check via API
            "price_usd": 9.99,
            "price_crypto": {
                "BTC": 0.0003,
                "ETH": 0.005,
                "USDC": 9.99
            }
        }

    def purchase_domain(self, domain: str, years: int = 1, crypto: str = "USDC") -> Dict:
        """Purchase domain with crypto"""
        # Would integrate with Porkbun's crypto payment API
        return {
            "order_id": "pork_123456",
            "domain": domain,
            "amount": 9.99,
            "crypto": crypto,
            "payment_address": "0x...",  # Payment address from Porkbun
            "expires_at": "2024-01-01T00:00:00Z"
        }


class MullvadAdapter(MerchantAdapter):
    """Mullvad VPN - accepts crypto, no email required"""

    def __init__(self):
        super().__init__()
        self.name = "Mullvad"
        self.accepts_crypto = ["BTC", "ETH", "USDC", "XMR"]
        self.requires_account = False  # Anonymous

    def create_account(self) -> Dict:
        """Create anonymous Mullvad account"""
        # Mullvad generates random account numbers
        return {
            "account_number": "1234567890123456",
            "note": "Save this number - it's your login"
        }

    def add_time(self, account_number: str, months: int = 1, crypto: str = "USDC") -> Dict:
        """Add VPN time with crypto"""
        return {
            "order_id": "mullvad_123",
            "account": account_number,
            "months": months,
            "amount_usd": 5.00 * months,
            "crypto": crypto,
            "payment_address": "0x...",
            "expires_at": "2024-01-01T00:00:00Z"
        }


class TravalaAdapter(MerchantAdapter):
    """Travala travel booking - accepts 90+ cryptocurrencies"""

    def __init__(self, api_key: str):
        super().__init__()
        self.name = "Travala"
        self.accepts_crypto = ["BTC", "ETH", "USDC", "BNB", "AVA", "XRP"]
        self.api_key = api_key
        self.base_url = "https://api.travala.com"

    def search_hotels(self, location: str, check_in: str, check_out: str) -> List[Dict]:
        """Search for hotels"""
        # Would integrate with Travala API
        return [{
            "id": "hotel_123",
            "name": "Sample Hotel",
            "location": location,
            "price_usd": 100,
            "price_crypto": {"USDC": 100, "BTC": 0.003}
        }]

    def book_hotel(self, hotel_id: str, crypto: str = "USDC") -> Dict:
        """Book hotel with crypto"""
        return {
            "booking_id": "travala_123",
            "hotel_id": hotel_id,
            "payment_address": "0x...",
            "amount_crypto": 100,
            "crypto": crypto
        }


class ProtonAdapter(MerchantAdapter):
    """Proton services - mail, VPN, storage (accepts crypto)"""

    def __init__(self):
        super().__init__()
        self.name = "Proton"
        self.accepts_crypto = ["BTC"]  # Proton primarily accepts BTC

    def get_plans(self) -> List[Dict]:
        """Get Proton subscription plans"""
        return [
            {
                "plan": "Mail Plus",
                "price_usd": 4.99,
                "features": ["15GB storage", "Custom domain", "Unlimited messages"]
            },
            {
                "plan": "Proton Unlimited",
                "price_usd": 9.99,
                "features": ["Mail + VPN + Drive + Calendar", "500GB storage"]
            }
        ]

    def subscribe(self, plan: str, crypto: str = "BTC") -> Dict:
        """Subscribe to Proton with crypto"""
        # Proton uses BTCPay Server
        return {
            "invoice_id": "proton_inv_123",
            "plan": plan,
            "payment_url": "https://btcpay.proton.me/...",  # BTCPay invoice
            "amount_btc": 0.0003
        }


# Merchant registry
MERCHANT_REGISTRY = {
    "porkbun": {
        "name": "Porkbun",
        "category": "domains",
        "accepts": ["BTC", "ETH", "USDC", "LTC", "DOGE"],
        "products": ["domain registration", "domain transfer", "SSL certificates"],
        "adapter": PorkbunAdapter
    },
    "mullvad": {
        "name": "Mullvad VPN",
        "category": "vpn",
        "accepts": ["BTC", "ETH", "USDC", "XMR"],
        "products": ["vpn subscription"],
        "adapter": MullvadAdapter
    },
    "travala": {
        "name": "Travala",
        "category": "travel",
        "accepts": ["BTC", "ETH", "USDC", "BNB", "AVA"],
        "products": ["hotels", "flights", "activities"],
        "adapter": TravalaAdapter
    },
    "proton": {
        "name": "Proton",
        "category": "privacy",
        "accepts": ["BTC"],
        "products": ["email", "vpn", "storage", "calendar"],
        "adapter": ProtonAdapter
    },
    "namecheap": {
        "name": "Namecheap",
        "category": "domains",
        "accepts": ["BTC"],
        "products": ["domains", "hosting", "SSL"],
        "note": "Use BitPay for payment"
    }
}


def find_merchant(query: str) -> Optional[Dict]:
    """Find merchant by name or category"""
    query_lower = query.lower()

    # Check exact name match
    if query_lower in MERCHANT_REGISTRY:
        return MERCHANT_REGISTRY[query_lower]

    # Check category match
    for merchant_id, info in MERCHANT_REGISTRY.items():
        if query_lower in info["category"] or query_lower in info["name"].lower():
            return info

    return None


def list_merchants_by_category(category: str) -> List[Dict]:
    """List all merchants in a category"""
    return [
        {"id": k, **v}
        for k, v in MERCHANT_REGISTRY.items()
        if v["category"] == category
    ]


def get_supported_categories() -> List[str]:
    """Get all supported merchant categories"""
    return list(set(m["category"] for m in MERCHANT_REGISTRY.values()))
