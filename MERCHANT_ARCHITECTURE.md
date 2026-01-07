# Merchant Payment Architecture

## The Question
**"How can users purchase from DoorDash (or any merchant) without manually adding adapters to source code?"**

## Current Architecture (Hardcoded Adapters)

**How it works:**
- Each merchant has a custom adapter class (e.g., `PorkbunAdapter`, `MullvadAdapter`)
- Adapters hardcoded in `merchant_adapters.py`
- Must deploy new code for each new merchant

**Pros:**
- ✅ Full control over integration
- ✅ Custom logic per merchant
- ✅ Type-safe, tested code

**Cons:**
- ❌ Doesn't scale (need to code every merchant)
- ❌ Can't support unknown merchants
- ❌ Requires code deployment for new merchants

---

## Solution 1: Universal Payment Processor (RECOMMENDED)

**How it works:**
- Instead of integrating merchants, integrate payment processors
- 3 processors cover 95% of crypto-accepting merchants:
  - **CoinGate** (70+ cryptos, merchant receives fiat)
  - **NOWPayments** (200+ cryptos)
  - **BTCPay Server** (open-source, privacy-focused)

**Example Flow:**
```
User: "Order $30 from Restaurant XYZ"

Agent:
1. Checks if Restaurant XYZ in registry → Not found
2. Calls pay_any_merchant_with_crypto("Restaurant XYZ", 30, "food order")
3. Detects: Unknown merchant
4. Suggests: "Check if Restaurant XYZ accepts crypto via CoinGate/NOWPayments"
5. If yes: Creates payment invoice via processor API
6. If no: Falls back to gift card search
```

**Implementation:**
```python
# File: universal_crypto_payment.py

def pay_any_merchant(merchant_name, amount, crypto="USDC"):
    # Try to detect payment processor
    processor = detect_payment_processor(merchant_website)

    if processor == "coingate":
        return create_coingate_invoice(amount, crypto)
    elif processor == "nowpayments":
        return create_nowpayments_invoice(amount, crypto)
    else:
        # Fallback to gift cards
        return search_gift_cards(merchant_name)
```

**Pros:**
- ✅ Works with ANY merchant using these processors
- ✅ No code changes needed for new merchants
- ✅ Scales infinitely
- ✅ Payment processors handle conversion, confirmations, etc.

**Cons:**
- ❌ Requires payment processor API keys
- ❌ Less control over UX
- ❌ Doesn't work for merchants without crypto support

**Status:** ✅ Implemented in `universal_crypto_payment.py` and `merchant_tools.py`

---

## Solution 2: Community Merchant Registry

**How it works:**
- Maintain crowdsourced JSON/database of merchants
- Users can submit new merchants via PR or form
- No code deployment needed - just update JSON

**Example:**
```json
// File: community_merchants.json
{
  "doordash": {
    "name": "DoorDash",
    "payment_method": "giftcard",
    "giftcard_provider": "bitrefill",
    "giftcard_id": "doordash"
  },
  "shopify_store_123": {
    "name": "Cool Shopify Store",
    "payment_method": "coingate",
    "coingate_merchant_id": "abc123"
  }
}
```

**Pros:**
- ✅ Community-driven (users add merchants)
- ✅ No code deployment for new merchants
- ✅ Can scale to thousands of merchants

**Cons:**
- ❌ Still requires manual data entry
- ❌ Data quality depends on community
- ❌ Limited to merchants someone already knows about

**Status:** ⚠️ Partially implemented in `COMMUNITY_MERCHANT_REGISTRY` (in `universal_crypto_payment.py`)

---

## Solution 3: AI-Powered Merchant Discovery (FUTURE)

**How it works:**
- AI agent does web research to find payment method
- Checks merchant website for payment options
- Detects crypto processors automatically

**Example Flow:**
```
User: "Buy $50 from NewMerchant.com"

Agent:
1. Visits NewMerchant.com
2. Finds "Pay with Crypto" button → Links to CoinGate
3. Extracts CoinGate merchant ID
4. Creates invoice automatically
```

**Pros:**
- ✅ Fully automatic - no manual work
- ✅ Works with ANY merchant
- ✅ Always up-to-date

**Cons:**
- ❌ Complex to implement reliably
- ❌ Slower (web scraping)
- ❌ May break if merchant changes website

**Status:** 🔮 Future feature (would require web browsing capability)

---

## Recommended Hybrid Approach

**Layer 1: Custom Adapters (High-Value Merchants)**
- Porkbun, Mullvad, Travala, etc.
- Full API integration for best UX

**Layer 2: Universal Payment Processors**
- CoinGate, NOWPayments, BTCPay
- Works for thousands of merchants automatically

**Layer 3: Gift Card Fallback**
- Bitrefill for merchants without crypto
- Covers DoorDash, Uber Eats, etc.

**Layer 4: Community Registry**
- Users contribute merchant data
- Simple JSON updates, no deployment

**Decision Tree:**
```
User wants to pay Merchant X
  │
  ├─ Is X in custom adapters? → Use custom adapter
  │
  ├─ Does X use CoinGate/NOWPayments? → Use payment processor
  │
  ├─ Is X on Bitrefill? → Buy gift card
  │
  └─ Unknown → Suggest gift card search OR ask user to contribute merchant info
```

---

## Implementation Status

✅ **Done:**
- Custom adapters for Porkbun, Mullvad, Travala, Proton
- Universal payment processor framework
- Gift card integration (Bitrefill)
- `pay_any_merchant_with_crypto` tool (handles unknown merchants)

⚠️ **Needs API Keys:**
- CoinGate API (for production use)
- NOWPayments API (for production use)
- BTCPay Server URL (merchant-specific)

🔮 **Future:**
- User-submitted merchant registry (form or PR)
- AI web research for merchant discovery
- Webhook integration for payment confirmations

---

## Answer to Your Question

**"Can users purchase from DoorDash without adding adapters?"**

**Yes, via 2 paths:**

1. **Gift Card (Works Now):**
   ```
   User: "Order $30 from DoorDash"
   Agent: Searches "doordash" gift card → Buys $30 card → Returns code
   User: Uses code in DoorDash app
   ```

2. **Universal Tool (Works Now):**
   ```
   User: "Pay $30 to DoorDash"
   Agent: Calls pay_any_merchant_with_crypto("DoorDash", 30)
   Agent: Detects → gift card method → Redirects to Bitrefill
   ```

**For merchants accepting crypto directly:**
```
User: "Buy domain from RandomRegistrar.com"
Agent: Calls pay_any_merchant_with_crypto("RandomRegistrar", 15)
Agent: Detects → CoinGate processor → Creates invoice
User: Pays via CoinGate → Domain registered
```

**Recommendation:**
- Keep custom adapters for high-value merchants (better UX)
- Use universal payment processor for long tail
- Gift cards as fallback
- Let community contribute merchant data via JSON updates (no code changes)
