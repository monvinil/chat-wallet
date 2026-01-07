"""
Smart bill payment helper - Maps vendors to gift cards and provides instructions
"""

# Vendor to gift card mapping
BILL_TO_GIFTCARD_MAP = {
    # Cloud/Tech
    "aws": {"card": "amazon", "note": "AWS accepts Amazon gift cards for billing"},
    "amazon web services": {"card": "amazon", "note": "AWS accepts Amazon gift cards"},
    "azure": {"card": "microsoft", "note": "Azure accepts Microsoft gift cards"},
    "microsoft azure": {"card": "microsoft", "note": "Azure accepts Microsoft gift cards"},
    "google cloud": {"card": "google-play", "note": "GCP accepts Google Play gift cards"},
    "gcp": {"card": "google-play", "note": "GCP accepts Google Play gift cards"},
    "digitalocean": {"card": None, "note": "DigitalOcean doesn't accept gift cards directly"},

    # Streaming
    "netflix": {"card": "netflix", "note": "Direct Netflix gift card"},
    "spotify": {"card": "spotify", "note": "Direct Spotify gift card"},
    "disney": {"card": "disney-plus", "note": "Disney+ gift card"},
    "hbo": {"card": "hbo-max", "note": "HBO Max gift card"},
    "youtube premium": {"card": "google-play", "note": "YouTube Premium via Google Play"},

    # Transportation
    "uber": {"card": "uber", "note": "Direct Uber gift card"},
    "lyft": {"card": "lyft", "note": "Direct Lyft gift card"},

    # Food
    "doordash": {"card": "doordash", "note": "Direct DoorDash gift card"},
    "uber eats": {"card": "uber", "note": "Uber Eats via Uber gift card"},
    "grubhub": {"card": "grubhub", "note": "Direct GrubHub gift card"},
    "starbucks": {"card": "starbucks", "note": "Direct Starbucks gift card"},

    # Utilities (indirect via Amazon/general retailers)
    "electric": {"card": "amazon", "note": "Buy utility payment cards from Amazon"},
    "water": {"card": "amazon", "note": "Buy utility payment cards from Amazon"},
    "gas": {"card": "amazon", "note": "Buy gas station cards from Amazon"},
    "internet": {"card": "amazon", "note": "Some ISPs accept Amazon gift cards"},
}


def detect_vendor_from_email(email_subject: str, email_body: str) -> tuple:
    """
    Detect bill vendor from email content
    Returns: (vendor_name, amount, confidence)
    """
    subject_lower = email_subject.lower()
    body_lower = email_body.lower()

    # Common patterns
    if "aws" in subject_lower or "amazon web services" in subject_lower:
        return ("aws", extract_amount(email_body), "high")
    elif "netflix" in subject_lower:
        return ("netflix", extract_amount(email_body), "high")
    elif "spotify" in subject_lower:
        return ("spotify", extract_amount(email_body), "high")
    elif "uber" in subject_lower and "receipt" in subject_lower:
        return ("uber", extract_amount(email_body), "high")
    elif "azure" in subject_lower or "microsoft azure" in subject_lower:
        return ("azure", extract_amount(email_body), "high")

    return (None, None, "none")


def extract_amount(text: str) -> float:
    """Extract dollar amount from text"""
    import re

    # Pattern: $XXX.XX or $XXX,XXX.XX
    patterns = [
        r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $1,234.56
        r'Total:?\s*\$?\s*(\d+(?:\.\d{2})?)',      # Total: $123.45
        r'Amount Due:?\s*\$?\s*(\d+(?:\.\d{2})?)', # Amount Due: $123.45
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            return float(amount_str)

    return None


def suggest_gift_card_amount(bill_amount: float) -> tuple:
    """
    Suggest closest gift card denomination
    Returns: (suggested_amount, explanation)
    """
    # Common gift card denominations
    denominations = [10, 15, 25, 50, 100, 200, 500]

    # Find closest amount >= bill_amount
    for amount in denominations:
        if amount >= bill_amount:
            overage = amount - bill_amount
            if overage < 5:
                explanation = f"${amount} card covers bill exactly" if overage == 0 else f"${amount} card (${overage:.2f} extra becomes account credit)"
            else:
                explanation = f"${amount} card (${overage:.2f} extra for future bills)"
            return (amount, explanation)

    # If bill > $500, round up to nearest $100
    suggested = ((bill_amount // 100) + 1) * 100
    return (suggested, f"${suggested:.0f} to cover full amount")


def get_redemption_instructions(vendor: str) -> str:
    """Get step-by-step redemption instructions for a vendor"""

    instructions = {
        "aws": """
**To apply your Amazon gift card to AWS:**

1. Go to [aws.amazon.com/billing](https://aws.amazon.com/billing)
2. Click **Payment Methods** in the left sidebar
3. Scroll to **Amazon.com Gift Cards**
4. Click **Add a gift card to your account**
5. Enter your gift card code
6. Click **Apply**

Your AWS bill will automatically use the gift card balance.""",

        "netflix": """
**To redeem your Netflix gift card:**

1. Go to [netflix.com/redeem](https://www.netflix.com/redeem)
2. Log in to your account
3. Enter the gift card code
4. Click **Redeem**

Your subscription will be extended automatically.""",

        "spotify": """
**To redeem your Spotify gift card:**

1. Go to [spotify.com/redeem](https://www.spotify.com/redeem)
2. Log in to your account
3. Enter the gift card code
4. Click **Redeem**

Your Premium subscription will be extended.""",

        "uber": """
**To add your Uber gift card:**

1. Open the Uber app
2. Tap **Account** → **Payment**
3. Tap **Add Payment Method** → **Gift Card**
4. Enter the gift card code
5. Tap **Add**

The balance will be applied to your next rides.""",

        "azure": """
**To add your Microsoft gift card to Azure:**

1. Go to [account.microsoft.com/billing](https://account.microsoft.com/billing)
2. Click **Redeem a code**
3. Enter your gift card code
4. Click **Redeem**

The balance will be applied to your Azure subscription.""",
    }

    return instructions.get(vendor, "Check the gift card email for redemption instructions.")


def format_bill_payment_response(vendor: str, bill_amount: float, card_amount: float, card_code: str) -> str:
    """
    Format a complete bill payment response with instructions
    """
    vendor_info = BILL_TO_GIFTCARD_MAP.get(vendor, {})
    card_name = vendor_info.get("card", vendor)

    response = f"""✅ **Bill Payment Complete**

**Purchased:** ${card_amount:.2f} {card_name.title()} gift card
**Bill Amount:** ${bill_amount:.2f}
**Gift Card Code:** `{card_code}`

📧 Code also sent to your email

---

{get_redemption_instructions(vendor)}

Need help? Just ask!"""

    return response
