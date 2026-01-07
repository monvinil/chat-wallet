"""
LangChain tools for crypto-native merchant purchases
"""

from langchain_core.tools import tool
from typing import Optional, List
from merchant_adapters import (
    find_merchant,
    list_merchants_by_category,
    get_supported_categories,
    MERCHANT_REGISTRY
)
import json


@tool
def search_crypto_merchants(query: str = "") -> str:
    """
    Search for merchants that accept cryptocurrency directly (no gift cards needed).

    Use this when user wants to:
    - Buy domains (Porkbun, Namecheap)
    - Subscribe to VPN (Mullvad, Proton)
    - Book travel (Travala)
    - Find merchants accepting crypto

    Args:
        query: Search query (e.g., "domain", "vpn", "travel", "porkbun")

    Returns:
        List of merchants and what they accept
    """
    try:
        query_lower = query.lower()

        # If empty query, show all merchants
        if not query:
            result = "**Merchants accepting crypto directly:**\n\n"

            categories = {}
            for merchant_id, info in MERCHANT_REGISTRY.items():
                category = info["category"]
                if category not in categories:
                    categories[category] = []
                categories[category].append(info)

            for category, merchants in categories.items():
                result += f"**{category.title()}:**\n"
                for merchant in merchants:
                    cryptos = ", ".join(merchant["accepts"])
                    result += f"- {merchant['name']}: {cryptos}\n"
                result += "\n"

            result += "To purchase, use `buy_from_crypto_merchant` with the merchant name."
            return result

        # Try exact merchant match
        merchant = find_merchant(query)
        if merchant:
            result = f"**{merchant['name']}** (Category: {merchant['category']})\n\n"
            result += f"**Accepts:** {', '.join(merchant['accepts'])}\n"
            result += f"**Products:** {', '.join(merchant['products'])}\n"
            if merchant.get("note"):
                result += f"\n**Note:** {merchant['note']}\n"
            result += f"\nUse `buy_from_crypto_merchant` to make a purchase."
            return result

        # Try category match
        merchants = []
        for merchant_id, info in MERCHANT_REGISTRY.items():
            if query_lower in info["category"].lower() or query_lower in info["name"].lower():
                merchants.append(info)

        if merchants:
            result = f"Found {len(merchants)} merchant(s):\n\n"
            for merchant in merchants:
                cryptos = ", ".join(merchant["accepts"])
                result += f"**{merchant['name']}** ({merchant['category']})\n"
                result += f"  Accepts: {cryptos}\n"
                result += f"  Products: {', '.join(merchant['products'])}\n\n"
            return result

        return f"No crypto-accepting merchants found for '{query}'. Try 'domain', 'vpn', 'travel', or leave query empty to see all."

    except Exception as e:
        return f"Error searching merchants: {e}"


@tool
def buy_domain_with_crypto(domain: str, years: int = 1, crypto: str = "USDC") -> str:
    """
    Purchase a domain name with cryptocurrency via Porkbun.

    IMPORTANT: Only call this after user explicitly approves the purchase.

    Args:
        domain: Domain name to register (e.g., "example.com")
        years: Number of years (default 1)
        crypto: Cryptocurrency to use (BTC, ETH, USDC, LTC, DOGE)

    Returns:
        Domain availability check and purchase instructions
    """
    try:
        from merchant_adapters import PorkbunAdapter

        # For now, show preview (actual API integration would require Porkbun API keys)
        adapter = PorkbunAdapter(api_key="", api_secret="")
        domain_info = adapter.search_domains(domain)

        if not domain_info.get("available"):
            return f"❌ Domain '{domain}' is not available for registration."

        price = domain_info["price_crypto"].get(crypto, domain_info["price_usd"])

        result = f"**Domain Registration Preview**\n\n"
        result += f"Domain: {domain}\n"
        result += f"Duration: {years} year(s)\n"
        result += f"Price: {price} {crypto}\n"
        result += f"Registrar: Porkbun\n\n"
        result += f"**Next Steps:**\n"
        result += f"1. Confirm you want to register this domain\n"
        result += f"2. You'll receive payment address for {crypto}\n"
        result += f"3. After payment, domain will be registered automatically\n\n"
        result += f"Ready to proceed? Say 'yes' to get payment details."

        return result

    except Exception as e:
        return f"Error checking domain availability: {e}"


@tool
def subscribe_vpn_with_crypto(service: str = "mullvad", months: int = 1, crypto: str = "USDC") -> str:
    """
    Subscribe to a privacy-focused VPN with cryptocurrency.

    IMPORTANT: Only call this after user explicitly approves the purchase.

    Args:
        service: VPN service ("mullvad" or "proton")
        months: Subscription duration in months
        crypto: Cryptocurrency to use

    Returns:
        Subscription preview and payment instructions
    """
    try:
        from merchant_adapters import MullvadAdapter, MERCHANT_REGISTRY

        service_lower = service.lower()

        if service_lower == "mullvad":
            adapter = MullvadAdapter()
            account = adapter.create_account()
            payment = adapter.add_time(account["account_number"], months, crypto)

            result = f"**Mullvad VPN Subscription**\n\n"
            result += f"✅ Anonymous account created: `{account['account_number']}`\n"
            result += f"⚠️ **Save this number** - it's your only login credential\n\n"
            result += f"**Subscription Details:**\n"
            result += f"- Duration: {months} month(s)\n"
            result += f"- Price: ${payment['amount_usd']:.2f} ({crypto})\n"
            result += f"- No email required (truly anonymous)\n\n"
            result += f"**Payment Instructions:**\n"
            result += f"Send {crypto} to: `{payment['payment_address']}`\n"
            result += f"After payment confirmation, your VPN will be active.\n\n"
            result += f"Download Mullvad app and login with your account number."

            return result

        elif service_lower == "proton":
            from merchant_adapters import ProtonAdapter
            adapter = ProtonAdapter()
            plans = adapter.get_plans()

            result = f"**Proton VPN Plans**\n\n"
            for plan in plans:
                result += f"**{plan['plan']}** - ${plan['price_usd']}/month\n"
                for feature in plan['features']:
                    result += f"  - {feature}\n"
                result += "\n"

            result += "Choose a plan and confirm to get payment details."
            return result

        else:
            merchant = MERCHANT_REGISTRY.get(service_lower)
            if merchant and merchant["category"] == "vpn":
                return f"{merchant['name']} accepts {', '.join(merchant['accepts'])}. Integration coming soon."
            return f"VPN service '{service}' not supported. Try 'mullvad' or 'proton'."

    except Exception as e:
        return f"Error setting up VPN subscription: {e}"


@tool
def book_travel_with_crypto(
    search_type: str,
    location: str = "",
    check_in: str = "",
    check_out: str = "",
    crypto: str = "USDC"
) -> str:
    """
    Search and book travel (hotels, flights, activities) with cryptocurrency via Travala.

    Args:
        search_type: Type of booking ("hotel", "flight", "activity")
        location: Destination city or country
        check_in: Check-in date (YYYY-MM-DD)
        check_out: Check-out date (YYYY-MM-DD)
        crypto: Cryptocurrency to use (BTC, ETH, USDC, BNB, AVA)

    Returns:
        Available options and booking preview
    """
    try:
        from merchant_adapters import TravalaAdapter

        # Travala integration would require API key
        adapter = TravalaAdapter(api_key="")

        if search_type.lower() == "hotel":
            if not location or not check_in or not check_out:
                return "Please provide location, check-in date, and check-out date for hotel search."

            hotels = adapter.search_hotels(location, check_in, check_out)

            if not hotels:
                return f"No hotels found in {location} for {check_in} to {check_out}"

            result = f"**Hotels in {location}** ({check_in} to {check_out})\n\n"
            for i, hotel in enumerate(hotels[:5], 1):
                usdc_price = hotel["price_crypto"].get("USDC", hotel["price_usd"])
                result += f"{i}. **{hotel['name']}**\n"
                result += f"   Price: ${hotel['price_usd']} ({usdc_price} USDC)\n"
                result += f"   ID: {hotel['id']}\n\n"

            result += "To book, say: 'Book hotel [ID] with USDC'"
            return result

        else:
            return f"Travala supports hotels, flights, and activities. Search type '{search_type}' will be available soon."

    except Exception as e:
        return f"Error searching travel options: {e}"


@tool
def pay_any_merchant_with_crypto(
    merchant_name: str,
    amount_usd: float,
    description: str,
    crypto: str = "USDC"
) -> str:
    """
    Universal merchant payment - works with ANY merchant accepting crypto.

    Use this when user wants to pay a merchant not in our registry.
    Works by detecting merchant's payment processor or suggesting alternatives.

    Args:
        merchant_name: Name of merchant (e.g., "DoorDash", "Chipotle")
        amount_usd: Amount in USD
        description: What they're buying
        crypto: Cryptocurrency to pay with (default USDC)

    Returns:
        Payment method and next steps
    """
    try:
        from universal_crypto_payment import find_payment_method, create_merchant_payment

        # Find how to pay this merchant
        payment_info = find_payment_method(merchant_name)

        if payment_info.get("payment_method") == "giftcard":
            # Redirect to gift card flow
            card_name = payment_info.get("giftcard_id", merchant_name.lower())
            return f"""**{merchant_name}** accepts payment via gift cards.

**Best approach:**
Use the `search_gift_cards` tool to find {merchant_name} gift cards on Bitrefill.

Example: Search for "{card_name}" gift card, buy with USDC, use code at checkout.

{payment_info.get('note', '')}"""

        elif payment_info.get("payment_method") == "giftcard_search":
            # Unknown merchant - suggest gift card search
            return f"""**{merchant_name}** - Payment method unknown.

**Suggested approaches:**
1. Search for "{merchant_name}" gift cards using `search_gift_cards` tool
2. If merchant has a website, check if they accept crypto directly
3. Check if merchant uses CoinGate, NOWPayments, or BTCPay Server

Would you like me to search for gift cards?"""

        elif payment_info.get("accepts_crypto"):
            processor = payment_info.get("payment_processor")

            if processor == "custom":
                # Has custom adapter
                return f"""**{merchant_name}** accepts crypto directly!

Accepted: {', '.join(payment_info.get('accepted_cryptos', []))}

Use the merchant-specific tool for {merchant_name} to complete purchase.

{payment_info.get('note', '')}"""

            else:
                # Uses payment processor (CoinGate, NOWPayments, etc.)
                payment = create_merchant_payment(
                    merchant_name,
                    amount_usd,
                    description,
                    payment_processor=processor,
                    crypto=crypto
                )

                if payment.get("success"):
                    result = f"""**{merchant_name} Payment Created**

Amount: {payment['amount']}
Method: {payment['payment_method']}
Description: {payment['description']}

**Next Steps:**
"""
                    for step in payment['next_steps']:
                        result += f"{step}\n"

                    result += f"\n**Payment Link:** {payment['payment_url']}\n\n"
                    result += f"Note: {payment['note']}"

                    return result
                else:
                    return f"Error creating payment: {payment.get('error')}"

        return f"Unable to determine payment method for {merchant_name}. Try searching for gift cards instead."

    except Exception as e:
        return f"Error processing merchant payment: {e}"


def get_merchant_tools():
    """Get list of merchant tools for AI agent"""
    return [
        search_crypto_merchants,
        buy_domain_with_crypto,
        subscribe_vpn_with_crypto,
        book_travel_with_crypto,
        pay_any_merchant_with_crypto
    ]
