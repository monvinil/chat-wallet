# Bitrefill API Setup Guide

Enable real gift card purchases with cryptocurrency through Bitrefill's API.

## What is Bitrefill?

Bitrefill allows users to buy gift cards for 1000+ brands (Amazon, Uber, Netflix, Starbucks, etc.) using cryptocurrency. Perfect for autonomous AI wallet actions.

## Mock Mode vs Real API

### Mock Mode (Default - No Setup Required)
- Works out of the box
- Returns fake gift card data for testing
- No real purchases
- Perfect for development and demos

### Real API Mode (Production)
- Requires Bitrefill Business API account
- Real gift card purchases with crypto
- Production-ready

## Setup for Production (Optional)

### Step 1: Get Bitrefill Business API Access

1. Go to https://www.bitrefill.com/business/
2. Click **"Contact Sales"** or **"Get Started"**
3. Apply for a business account
4. Request API access (mention you're building a crypto wallet with autonomous features)

**Note:** Bitrefill Business API is typically for businesses doing volume. For testing, mock mode works great.

### Step 2: Get API Credentials

Once approved, Bitrefill will provide:
- **API Key** (public identifier)
- **API Secret** (private key)

### Step 3: Add to Railway Environment Variables

1. Go to your Railway project
2. Click on your service
3. Go to **Variables** tab
4. Add these variables:

```
BITREFILL_API_KEY=<your-api-key>
BITREFILL_API_SECRET=<your-api-secret>
```

5. Click **Deploy** to restart

### Step 4: Test

1. Open your app
2. Try: "Search for Amazon gift cards"
3. Try: "Buy a $25 Amazon gift card"

With real API credentials, the system will:
- Show real products and pricing
- Create actual orders
- Process crypto payments
- Deliver real gift card codes

## API Documentation

Bitrefill API docs: https://www.bitrefill.com/api-docs/

Key features:
- 1000+ brands available
- Multiple cryptocurrencies supported (BTC, ETH, USDC, etc.)
- Instant delivery
- Email and webhook notifications

## Pricing

- No monthly fees
- Pay only for what you use
- Typical margin: 2-5% on top of gift card face value
- Volume discounts available

## How It Works in Chat Wallet

### User Flow:
1. User: "Buy me a $50 Amazon gift card"
2. AI searches Bitrefill: `search_gift_cards("amazon")`
3. AI shows options and asks for confirmation
4. User approves
5. AI purchases: `buy_gift_card("amazon-us", 50, user_email)`
6. Bitrefill creates order with crypto payment address
7. Wallet sends USDC to payment address
8. Gift card code sent to user's email
9. AI retrieves code: `check_gift_card_order(order_id)`
10. User receives gift card code

### Example AI Conversation:

**User:** Buy me a Starbucks gift card for $25

**AI:** Let me search for Starbucks gift cards...
*[Calls search_gift_cards("starbucks")]*

Found Starbucks Gift Card:
- Price range: $10 - $100
- Instant delivery via email

Would you like to proceed with a $25 Starbucks gift card? This will be purchased with your USDC.

**User:** Yes

**AI:** Processing your order...
*[Calls buy_gift_card("starbucks-us", 25)]*

✅ Order created! Sending 25 USDC to payment address...
*[Wallet processes payment]*

Your Starbucks gift card has been sent to your email! Code: XXXX-YYYY-ZZZZ

## Alternative: Mock Mode

If you don't have Bitrefill API access, the system automatically uses mock mode:
- Shows realistic gift card data
- Simulates purchases
- Great for demos and development
- No real money or gift cards

Users will see a note: "⚠️ Bitrefill API credentials not configured. Using mock mode."

## Troubleshooting

### "Bitrefill API credentials not configured"
- Expected in development - mock mode works fine
- For production, add API credentials to Railway

### "Invalid API credentials"
- Check that BITREFILL_API_KEY and BITREFILL_API_SECRET are correct
- Make sure there are no extra spaces
- Verify your Bitrefill account is active

### "Product not available in country"
- Some products are region-specific
- Try specifying country: `search_gift_cards("amazon", "US")`
- Check Bitrefill's country availability

## Security Notes

- API credentials stored as environment variables only
- Never committed to Git
- Gift card codes sent directly to user's email
- All purchases logged in database for audit trail
