"""
Bitrefill tools for AI agent - LangChain compatible
"""

from langchain_core.tools import tool
from typing import Optional
from bitrefill_client import get_bitrefill_client
import streamlit as st


@tool
def search_gift_cards(query: str = "", country: str = "US") -> str:
    """
    Search for gift cards available on Bitrefill.

    Use this when user wants to buy gift cards or find what's available.

    Args:
        query: Search query (e.g., "amazon", "uber", "netflix", "starbucks")
        country: Country code (default "US")

    Returns:
        List of available gift cards with pricing
    """
    try:
        client = get_bitrefill_client()
        products = client.search_products(query=query, country=country, limit=10)

        if not products:
            return f"No gift cards found for '{query}' in {country}"

        # Format results
        result = f"Found {len(products)} gift card(s):\n\n"

        for i, product in enumerate(products, 1):
            result += f"{i}. **{product['name']}**\n"
            result += f"   - Description: {product['description']}\n"
            result += f"   - Price range: ${product['min_amount']} - ${product['max_amount']} {product['currency']}\n"
            result += f"   - Category: {product['category']}\n"
            result += f"   - ID: {product['id']}\n\n"

        result += "To buy a gift card, use the buy_gift_card tool with the product ID."

        return result

    except Exception as e:
        return f"Error searching gift cards: {e}"


@tool
def get_gift_card_details(product_id: str) -> str:
    """
    Get detailed information about a specific gift card.

    Use this before purchasing to understand terms and conditions.

    Args:
        product_id: Product ID from search results (e.g., "amazon-us")

    Returns:
        Detailed product information including terms and redemption instructions
    """
    try:
        client = get_bitrefill_client()
        details = client.get_product_details(product_id)

        if not details:
            return f"Product '{product_id}' not found"

        result = f"**{details['name']}**\n\n"
        result += f"**Description:** {details['description']}\n\n"
        result += f"**Price Range:** ${details['min_amount']} - ${details['max_amount']} {details['currency']}\n\n"
        result += f"**Delivery:** {details['delivery_method']}\n\n"
        result += f"**Terms:** {details['terms']}\n\n"
        result += f"**Redemption Instructions:** {details['redemption_instructions']}\n"

        return result

    except Exception as e:
        return f"Error fetching gift card details: {e}"


@tool
def buy_gift_card(product_id: str, amount: float, email: Optional[str] = None) -> str:
    """
    Purchase a gift card with cryptocurrency.

    IMPORTANT: Only call this after user explicitly approves the purchase.
    Check user's spending limits in settings before purchasing.

    Args:
        product_id: Product ID (e.g., "amazon-us")
        amount: Amount in USD (must be within product's min/max range)
        email: Email to send gift card to (uses user's connected email if not provided)

    Returns:
        Order details with payment information or gift card code
    """
    try:
        # Get user's connected email if not provided
        if not email:
            user_id = st.session_state.get("wallet_address")
            if not user_id:
                return "Error: User not logged in"

            from settings_manager import SettingsManager
            connection = SettingsManager.get_oauth_connection(user_id, "email")

            if connection and connection.get("is_active"):
                email = connection.get("provider_user_id")
            else:
                return "Error: No email connected. User must connect email in Settings → Connected Accounts"

        # Create order
        client = get_bitrefill_client()
        order = client.create_order(
            product_id=product_id,
            amount=amount,
            email=email,
            payment_method="crypto"
        )

        if not order:
            return "Error: Failed to create order"

        # Format response
        result = f"✅ Gift card order created!\n\n"
        result += f"**Order ID:** {order['order_id']}\n"
        result += f"**Status:** {order['status']}\n"
        result += f"**Amount:** ${amount} USD\n"
        result += f"**Email:** {email}\n\n"

        if order['status'] == 'pending':
            result += f"**Payment Required:**\n"
            result += f"- Send {order['payment_amount']} {order['payment_currency']}\n"
            result += f"- To address: {order['payment_address']}\n"
            result += f"- Expires: {order['expires_at']}\n\n"
            result += "After payment, the gift card code will be sent to your email."

        elif order['status'] == 'completed':
            result += f"**Gift Card Code:** {order['gift_card_code']}\n"
            if order.get('pin'):
                result += f"**PIN:** {order['pin']}\n"
            result += "\nGift card has been sent to your email!"

        return result

    except Exception as e:
        return f"Error purchasing gift card: {e}"


@tool
def check_gift_card_order(order_id: str) -> str:
    """
    Check the status of a gift card order.

    Use this to see if payment has been processed and retrieve the gift card code.

    Args:
        order_id: Order ID from buy_gift_card

    Returns:
        Order status and gift card details if available
    """
    try:
        client = get_bitrefill_client()
        status = client.get_order_status(order_id)

        if not status:
            return f"Order '{order_id}' not found"

        result = f"**Order Status:** {status['status']}\n\n"

        if status['status'] == 'completed':
            result += f"**Gift Card Code:** {status['gift_card_code']}\n"
            if status.get('pin'):
                result += f"**PIN:** {status['pin']}\n"
            if status.get('redemption_url'):
                result += f"**Redeem at:** {status['redemption_url']}\n"
            result += "\n✅ Order completed! Check your email for the gift card."

        elif status['status'] == 'pending':
            result += "⏳ Waiting for payment to be confirmed..."

        elif status['status'] == 'failed':
            result += "❌ Order failed. Payment may have been rejected or expired."

        return result

    except Exception as e:
        return f"Error checking order status: {e}"


def get_bitrefill_tools():
    """Get list of Bitrefill tools for AI agent"""
    return [
        search_gift_cards,
        get_gift_card_details,
        buy_gift_card,
        check_gift_card_order
    ]
