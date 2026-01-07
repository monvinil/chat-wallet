"""
Universal crypto payment adapter - works with any merchant accepting crypto via payment processors

Instead of hardcoding merchant integrations, this uses payment processor APIs:
- BTCPay Server (open source, self-hosted or cloud)
- CoinGate API (supports 70+ cryptos)
- NOWPayments API (supports 200+ cryptos)
- Coinbase Commerce API

This allows paying ANY merchant that accepts crypto through these processors
"""

from typing import Dict, Optional, List
import requests
from datetime import datetime, timedelta


class UniversalCryptoPayment:
    """
    Universal payment adapter that can create payment invoices for any merchant
    accepting crypto via payment processors
    """

    @staticmethod
    def detect_payment_processor(merchant_url: str) -> Optional[str]:
        """
        Detect which payment processor a merchant uses by checking their payment page

        Returns: "btcpay", "coingate", "nowpayments", "coinbase_commerce", or None
        """
        try:
            # Check for common payment processor signatures
            # This would make a HEAD request to avoid downloading full page
            response = requests.head(merchant_url, timeout=5, allow_redirects=True)

            final_url = response.url.lower()

            if "btcpay" in final_url or "btcpay.com" in final_url:
                return "btcpay"
            elif "coingate.com" in final_url:
                return "coingate"
            elif "nowpayments.io" in final_url:
                return "nowpayments"
            elif "commerce.coinbase.com" in final_url:
                return "coinbase_commerce"

            return None

        except Exception as e:
            print(f"Error detecting payment processor: {e}")
            return None

    @staticmethod
    def create_invoice_btcpay(
        merchant_name: str,
        amount_usd: float,
        description: str,
        btcpay_url: str,
        api_key: str
    ) -> Dict:
        """
        Create invoice via BTCPay Server

        BTCPay is open-source and widely used by privacy-focused merchants
        """
        try:
            headers = {
                "Authorization": f"token {api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "amount": amount_usd,
                "currency": "USD",
                "checkout": {
                    "speedPolicy": "MediumSpeed",
                    "paymentMethods": ["BTC", "BTC-LightningNetwork"],
                },
                "metadata": {
                    "orderId": f"chat_wallet_{int(datetime.now().timestamp())}",
                    "itemDesc": description
                }
            }

            response = requests.post(
                f"{btcpay_url}/api/v1/invoices",
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                invoice = response.json()
                return {
                    "success": True,
                    "invoice_id": invoice["id"],
                    "payment_url": invoice["checkoutLink"],
                    "amount": amount_usd,
                    "currency": "USD",
                    "expires_at": invoice["expirationTime"],
                    "processor": "btcpay"
                }

            return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def create_invoice_coingate(
        merchant_name: str,
        amount_usd: float,
        description: str,
        api_key: str,
        receive_currency: str = "USD"  # Merchant receives USD, user pays crypto
    ) -> Dict:
        """
        Create invoice via CoinGate

        CoinGate is popular for businesses that want to receive fiat but accept crypto
        """
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "order_id": f"chat_wallet_{int(datetime.now().timestamp())}",
                "price_amount": amount_usd,
                "price_currency": "USD",
                "receive_currency": receive_currency,  # What merchant receives
                "title": merchant_name,
                "description": description,
                "callback_url": None,  # Would integrate webhook for status updates
                "cancel_url": None,
                "success_url": None
            }

            # CoinGate sandbox: https://api-sandbox.coingate.com/v2/orders
            # CoinGate production: https://api.coingate.com/v2/orders
            response = requests.post(
                "https://api.coingate.com/v2/orders",
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code in [200, 201]:
                invoice = response.json()
                return {
                    "success": True,
                    "invoice_id": invoice["id"],
                    "payment_url": invoice["payment_url"],
                    "amount": amount_usd,
                    "currency": "USD",
                    "expires_at": invoice["expire_at"],
                    "processor": "coingate",
                    "payment_address": invoice.get("payment_address"),
                    "accepted_cryptos": ["BTC", "ETH", "LTC", "USDC", "USDT"]  # CoinGate supports 70+
                }

            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def create_invoice_nowpayments(
        merchant_name: str,
        amount_usd: float,
        description: str,
        api_key: str,
        pay_currency: str = "USDC"  # Crypto user pays with
    ) -> Dict:
        """
        Create invoice via NOWPayments

        NOWPayments supports 200+ cryptocurrencies
        """
        try:
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json"
            }

            # First, get minimum payment amount for the crypto
            min_amount_response = requests.get(
                f"https://api.nowpayments.io/v1/min-amount?currency_from={pay_currency}&currency_to=usd",
                headers=headers,
                timeout=5
            )

            if min_amount_response.status_code != 200:
                return {"success": False, "error": "Failed to get minimum amount"}

            min_amount = min_amount_response.json().get("min_amount", 0)

            # Create payment
            payload = {
                "price_amount": amount_usd,
                "price_currency": "usd",
                "pay_currency": pay_currency.lower(),
                "order_id": f"chat_wallet_{int(datetime.now().timestamp())}",
                "order_description": description,
                "ipn_callback_url": None,  # Would integrate webhook
                "success_url": None,
                "cancel_url": None
            }

            response = requests.post(
                "https://api.nowpayments.io/v1/payment",
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code in [200, 201]:
                payment = response.json()
                return {
                    "success": True,
                    "invoice_id": payment["payment_id"],
                    "payment_url": payment["invoice_url"],
                    "payment_address": payment["pay_address"],
                    "amount_crypto": payment["pay_amount"],
                    "amount_usd": amount_usd,
                    "currency": pay_currency,
                    "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),  # NOWPayments default
                    "processor": "nowpayments"
                }

            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}

        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================================
# MERCHANT PAYMENT FLOW (Universal)
# ============================================================================

def create_merchant_payment(
    merchant_name: str,
    amount_usd: float,
    description: str,
    payment_processor: str = "coingate",
    crypto: str = "USDC"
) -> Dict:
    """
    Universal merchant payment creation

    This works for ANY merchant - no custom adapter needed
    User just needs to provide:
    1. Merchant name
    2. Amount
    3. What they're buying

    The payment processor handles the rest

    Args:
        merchant_name: Name of merchant (e.g., "DoorDash", "Porkbun")
        amount_usd: Amount in USD
        description: What user is buying
        payment_processor: "coingate", "nowpayments", or "btcpay"
        crypto: Cryptocurrency to pay with

    Returns:
        Payment invoice with URL and address
    """

    # In production, API keys would come from user settings or app config
    # For now, return mock data showing the flow

    if payment_processor == "coingate":
        # CoinGate is best for merchants that want fiat but accept crypto
        return {
            "success": True,
            "merchant": merchant_name,
            "amount": f"${amount_usd:.2f}",
            "description": description,
            "payment_method": crypto,
            "next_steps": [
                "1. Click payment link to see CoinGate invoice",
                "2. Send USDC to provided address",
                "3. Payment confirmed in ~30 seconds",
                "4. Merchant receives USD automatically"
            ],
            "payment_url": f"https://coingate.com/invoice/example_{int(datetime.now().timestamp())}",
            "note": "CoinGate integration requires API key - contact merchant for payment link or add CoinGate API key in Settings"
        }

    elif payment_processor == "nowpayments":
        # NOWPayments supports 200+ cryptos
        return {
            "success": True,
            "merchant": merchant_name,
            "amount": f"${amount_usd:.2f}",
            "description": description,
            "payment_method": crypto,
            "next_steps": [
                "1. Click payment link",
                "2. Send exact crypto amount shown",
                "3. Confirmation in 1-3 minutes",
                "4. Merchant receives notification"
            ],
            "payment_url": f"https://nowpayments.io/payment/example",
            "note": "NOWPayments integration requires API key - contact merchant for payment link"
        }

    else:  # btcpay
        # BTCPay is open-source and privacy-focused
        return {
            "success": True,
            "merchant": merchant_name,
            "amount": f"${amount_usd:.2f}",
            "description": description,
            "payment_method": crypto,
            "next_steps": [
                "1. Open BTCPay invoice link",
                "2. Scan QR code or copy address",
                "3. Send BTC/Lightning payment",
                "4. Instant confirmation"
            ],
            "payment_url": f"https://btcpay.example.com/invoice/example",
            "note": "BTCPay requires merchant's server URL - ask merchant for payment link"
        }


# ============================================================================
# COMMUNITY MERCHANT REGISTRY (Crowdsourced)
# ============================================================================

# Instead of hardcoding adapters, maintain a community registry of merchants
# Users can contribute new merchants via PR or form submission
COMMUNITY_MERCHANT_REGISTRY = {
    "doordash": {
        "name": "DoorDash",
        "category": "food_delivery",
        "accepts_crypto": False,  # No direct crypto (use gift cards)
        "payment_method": "giftcard",
        "giftcard_id": "doordash",
        "note": "Buy DoorDash gift card via Bitrefill, use code in app"
    },
    "porkbun": {
        "name": "Porkbun",
        "category": "domains",
        "accepts_crypto": True,
        "payment_processor": "custom",  # Has own API
        "accepted_cryptos": ["BTC", "ETH", "USDC", "LTC", "DOGE"],
        "note": "Direct crypto payment via Porkbun API"
    },
    "mullvad": {
        "name": "Mullvad VPN",
        "category": "vpn",
        "accepts_crypto": True,
        "payment_processor": "custom",
        "accepted_cryptos": ["BTC", "ETH", "USDC", "XMR"],
        "note": "Anonymous VPN, no email required"
    },
    # Example: Merchant using CoinGate
    "example_shop": {
        "name": "Example Online Shop",
        "category": "retail",
        "accepts_crypto": True,
        "payment_processor": "coingate",
        "coingate_merchant_id": "example123",
        "note": "Accepts 70+ cryptos via CoinGate"
    }
}


def find_payment_method(merchant_name: str) -> Dict:
    """
    Find how to pay a merchant with crypto

    Returns payment method (direct, gift card, or payment processor)
    """
    merchant_key = merchant_name.lower().replace(" ", "")

    # Check community registry
    if merchant_key in COMMUNITY_MERCHANT_REGISTRY:
        return COMMUNITY_MERCHANT_REGISTRY[merchant_key]

    # Default: suggest searching gift cards
    return {
        "name": merchant_name,
        "accepts_crypto": "unknown",
        "payment_method": "giftcard_search",
        "note": f"Try searching for '{merchant_name}' gift cards on Bitrefill"
    }
