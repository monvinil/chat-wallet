# Chat Wallet Setup Guide

## Architecture Overview

This is a **non-custodial** multi-chain crypto wallet with AI chat interface.

- **User controls their own private keys** (encrypted in browser)
- **Multi-chain support:** Base, Arbitrum, Polygon (EVM), Solana (coming soon)
- **AI-powered:** Claude 3.5 Sonnet helps with wallet operations
- **Fee structure:** $0.005 + 0.2% (max $3 per transaction)

---

## Prerequisites

1. **Python 3.11+**
2. **Anthropic API Key** (for Claude)
3. **Supabase Account** (free tier)
4. **CDP API Keys** (optional, for Base blockchain)

---

## Step 1: Clone and Install Dependencies

```bash
cd chat-wallet
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Step 2: Set Up Supabase

### 2.1 Create Project
1. Go to https://supabase.com/
2. Click "New Project"
3. Fill in:
   - **Name:** `chat-wallet`
   - **Database Password:** Generate and save securely
   - **Region:** Choose closest to you
4. Wait for project to spin up (~2 minutes)

### 2.2 Get API Keys
1. Go to **Settings** → **API**
2. Copy:
   - **Project URL**
   - **anon public** key

### 2.3 Create Database Tables
1. Go to **SQL Editor** in Supabase
2. Open `supabase_schema.sql` from this repo
3. Copy entire contents
4. Paste into SQL Editor
5. Click **Run**

### 2.4 Enable Google OAuth
1. Go to **Authentication** → **Providers**
2. Enable **Google**
3. Follow instructions to get Google OAuth credentials:
   - Go to https://console.cloud.google.com/
   - Create new project (or use existing)
   - Enable **Google+ API**
   - Create **OAuth 2.0 Client ID**
   - Add authorized redirect URIs from Supabase
4. Paste Client ID and Secret into Supabase

---

## Step 3: Environment Variables

Create a `.env` file in the project root:

```env
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Supabase (from Step 2.2)
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...

# CDP (Optional - for advanced features)
CDP_API_KEY_NAME=your-cdp-key-name
CDP_API_KEY_PRIVATE_KEY=your-cdp-private-key
```

---

## Step 4: Run the App

### Local Development

```bash
streamlit run app_new.py
```

The app will open at `http://localhost:8501`

### Deploy to Railway

1. Push code to GitHub
2. Go to https://railway.app/
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repo
5. Add environment variables from `.env`
6. Deploy!

---

## Step 5: Create Your Wallet

1. Open the app
2. Choose **"Create New Wallet"**
3. Set a strong password (min 8 characters)
4. **Save your password!** You'll need it to unlock your wallet
5. Your wallet is created and encrypted locally in your browser

---

## How It Works

### Non-Custodial Architecture

```
User's Browser
    ├── Wallet Private Key (encrypted with password)
    └── Stored in session state (browser memory only)

Supabase Database
    ├── User email
    ├── Wallet addresses (public)
    └── Transaction history
    ❌ NO private keys stored!

Blockchain Networks
    └── User's actual funds live here
```

### Security Features

1. **Private keys never leave your browser**
2. **Encrypted with your password** using PBKDF2 + Fernet
3. **You control all transactions** (must approve each one)
4. **No custody risk** for the app operator

---

## Supported Networks

| Network | Type | Status | USDC Address |
|---------|------|--------|--------------|
| Base Sepolia | EVM Testnet | ✅ Live | 0x036Cb... |
| Base Mainnet | EVM Mainnet | ✅ Live | 0x8335... |
| Arbitrum Sepolia | EVM Testnet | ✅ Live | 0x75fa... |
| Polygon Amoy | EVM Testnet | ✅ Live | 0x41E9... |
| Solana Devnet | Solana Testnet | 🔜 Coming | 4zMMC... |

---

## Getting Testnet Funds

### Base Sepolia
1. Go to https://portal.cdp.coinbase.com/products/faucet
2. Enter your wallet address
3. Claim testnet ETH

### Testnet USDC
- Most testnets have USDC faucets
- Or bridge from another testnet using Stargate/deBridge

---

## Usage Examples

### Check Balance
```
You: "What's my balance?"
AI: "You have $0.00 USDC across all chains..."
```

### Get Deposit Address
```
You: "Show me my deposit address for Base"
AI: "Here's your Base Sepolia address: 0x1234..."
```

### Buy Gift Card (Simulated)
```
You: "Search for Amazon gift cards"
AI: "Found 2 results..."
You: "Buy the $10 one"
AI: "Total: $10.025 ($10 + $0.025 fee). Ready for approval."
[You approve the transaction]
```

---

## Troubleshooting

### "CDP SDK not available"
- CDP is optional for basic features
- Install with: `pip install cdp-sdk`

### "Supabase connection failed"
- Check `SUPABASE_URL` and `SUPABASE_ANON_KEY` in `.env`
- Verify Supabase project is running

### "Failed to fetch balances"
- RPC nodes may be slow/rate-limited
- Try refreshing again
- Check network status

### "Wallet creation failed"
- Ensure CDP SDK is installed
- Check Python version (needs 3.11+)

---

## Next Steps

- [ ] Add Solana support
- [ ] Implement real gift card purchases (via Bitrefill API)
- [ ] Add DeFi strategies (swaps, bridging)
- [ ] Smart contract wallet integration
- [ ] Mobile app (React Native)

---

## Security Warning

⚠️ **This is experimental software for educational purposes.**

- Only use with testnet funds or small amounts
- Always back up your password securely
- Not audited for production use

---

## Support

- **Issues:** https://github.com/your-username/chat-wallet/issues
- **Twitter:** @your_handle

---

Built with ❤️ using Claude 3.5 Sonnet, Streamlit, and Coinbase CDP
