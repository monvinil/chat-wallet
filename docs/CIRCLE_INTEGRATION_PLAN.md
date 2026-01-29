# Circle SDK Integration Plan
**Document Version:** 1.0
**Created:** January 2026
**Status:** Planning

---

## Executive Summary

This document outlines the technical strategy for integrating Circle's product suite into USDChat. The goal is to leverage Circle's infrastructure for smoother onboarding, cross-chain transfers, and future AI-to-AI payments while maintaining our self-custody model.

---

## Circle Product Matrix

| Product | What It Does | Our Use Case | Priority |
|---------|--------------|--------------|----------|
| **Programmable Wallets** | Embedded wallet SDK with MPC custody | Optional hosted wallet for new users | P1 |
| **CCTP** | Cross-Chain Transfer Protocol | USDC bridging (Base ↔ Arbitrum ↔ Solana) | P1 |
| **x402** | HTTP 402 micropayments | AI agent payments (Horizon 3) | P2 |
| **Payments API** | Fiat on/off ramp | Buy USDC with card (future) | P3 |
| **Smart Contract Platform** | USDC infrastructure | Already using (native USDC) | ✅ |

---

## Integration Architecture

### Current Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        USER                                     │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    USDChat Application                          │
│                                                                 │
│   ┌─────────────────┐    ┌─────────────────┐                   │
│   │  WalletManager  │    │   BalanceService │                   │
│   │  (Self-Custody) │    │  (Internal Ledger)│                   │
│   │                 │    │                   │                   │
│   │  • BIP39/BIP44  │    │  • Double-spend   │                   │
│   │  • Fernet enc   │    │  • Audit trail    │                   │
│   │  • User keys    │    │  • Pending tx     │                   │
│   └────────┬────────┘    └────────┬──────────┘                   │
│            │                      │                             │
│            ▼                      ▼                             │
│   ┌─────────────────────────────────────────────────────┐      │
│   │              Direct Transaction Executor             │      │
│   │              (direct_tx.py, aave_client.py)         │      │
│   └─────────────────────────────────────────────────────┘      │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BLOCKCHAIN NETWORKS                          │
│                                                                 │
│   Base        Arbitrum      Ethereum      Solana                │
│   (Primary)   (DeFi)        (Fallback)    (Multi-chain)         │
└─────────────────────────────────────────────────────────────────┘
```

### Target Architecture (with Circle)
```
┌─────────────────────────────────────────────────────────────────┐
│                        USER                                     │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                   ┌──────────────┴──────────────┐
                   ▼                              ▼
┌────────────────────────────┐    ┌────────────────────────────┐
│   SELF-CUSTODY PATH        │    │   HOSTED WALLET PATH       │
│   (Power Users)            │    │   (Easy Onboarding)        │
│                            │    │                            │
│   • Own mnemonic           │    │   • Circle Programmable    │
│   • Full control           │    │     Wallets SDK            │
│   • Export anytime         │    │   • MPC custody            │
│                            │    │   • Social recovery        │
└────────────┬───────────────┘    └────────────┬───────────────┘
             │                                  │
             └────────────┬─────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    USDChat Application                          │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │              Unified Balance Service                     │  │
│   │              (Works with both wallet types)              │  │
│   └─────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │              Transaction Router                          │  │
│   │                                                          │  │
│   │  • Same-chain sends → Direct execution                  │  │
│   │  • Cross-chain sends → CCTP bridge                      │  │
│   │  • AI payments → x402 protocol                          │  │
│   └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   DIRECT RPC     │  │   CIRCLE CCTP    │  │   CIRCLE x402    │
│                  │  │                  │  │                  │
│   Base           │  │   Cross-chain    │  │   Micropayments  │
│   Arbitrum       │  │   USDC bridge    │  │   AI agents      │
│   Solana         │  │   Multi-network  │  │   HTTP 402       │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

---

## Phase 1: CCTP Integration (Cross-Chain Bridging)

### What CCTP Does
Circle's Cross-Chain Transfer Protocol enables native USDC transfers between chains without wrapped tokens or liquidity pools.

**Flow:**
1. User burns USDC on source chain
2. Circle attestation service validates
3. USDC is minted on destination chain

### Implementation Plan

#### 1.1 Create CCTP Client Module

```python
# cctp_client.py (to create)

class CCTPClient:
    """
    Circle Cross-Chain Transfer Protocol client.
    Handles USDC bridging between supported chains.
    """

    SUPPORTED_ROUTES = {
        ("base-mainnet", "arbitrum-mainnet"): True,
        ("base-mainnet", "eth-mainnet"): True,
        ("arbitrum-mainnet", "base-mainnet"): True,
        ("arbitrum-mainnet", "eth-mainnet"): True,
        # Solana support coming in Phase 2
    }

    DOMAIN_IDS = {
        "eth-mainnet": 0,
        "base-mainnet": 6,
        "arbitrum-mainnet": 3,
    }

    TOKEN_MESSENGER_ADDRESSES = {
        "base-mainnet": "0x...",
        "arbitrum-mainnet": "0x...",
        "eth-mainnet": "0x...",
    }

    def estimate_bridge_time(source: str, dest: str) -> int:
        """Returns estimated bridge time in seconds."""
        # CCTP typically takes 10-20 minutes
        return 900  # 15 minutes

    def initiate_bridge(
        private_key: str,
        source_chain: str,
        dest_chain: str,
        amount: Decimal,
        dest_address: str
    ) -> Dict[str, Any]:
        """
        Initiate a cross-chain USDC transfer.

        Steps:
        1. Approve TokenMessenger to spend USDC
        2. Call depositForBurn on source chain
        3. Wait for attestation
        4. Call receiveMessage on destination chain
        """
        pass

    def check_attestation(message_hash: str) -> Optional[str]:
        """Check if attestation is ready from Circle's API."""
        pass

    def complete_bridge(
        dest_chain: str,
        attestation: str,
        message: bytes
    ) -> Dict[str, Any]:
        """Complete the bridge on destination chain."""
        pass
```

#### 1.2 Integration Points

**In `direct_tx.py`:**
```python
def execute_transfer(...):
    # Detect cross-chain
    if source_chain != dest_chain:
        return CCTPClient.initiate_bridge(...)
```

**In `components/chat.py`:**
- Add cross-chain option in send flow
- Show bridge progress indicator
- Display estimated completion time

#### 1.3 API Endpoints Needed

| Endpoint | Purpose |
|----------|---------|
| `POST /cctp/bridge` | Initiate bridge |
| `GET /cctp/status/{message_hash}` | Check attestation status |
| `POST /cctp/complete` | Complete on destination |

#### 1.4 Dependencies
- Circle API key (for attestation API)
- TokenMessenger contract ABIs
- MessageTransmitter contract ABIs

---

## Phase 2: Programmable Wallets (Optional Hosted Path)

### Why Offer This?
- Lower friction onboarding (no seed phrase management)
- Social recovery options
- Regulatory clarity (MPC custody model)
- Future: Fiat on-ramp integration

### Implementation Strategy

We'll offer **both** wallet types:
1. **Self-custody** (current) - User manages their own keys
2. **Hosted** (new) - Circle manages keys via MPC

Users can choose at signup or migrate later.

#### 2.1 Circle Programmable Wallets Setup

```python
# circle_wallet.py (to create)

from circle.web3_sdk import Web3Service

class CircleWalletManager:
    """
    Manages Circle Programmable Wallets.
    Alternative to self-custody for easier onboarding.
    """

    def __init__(self, api_key: str, entity_secret: str):
        self.web3 = Web3Service(api_key=api_key)
        self.entity_secret = entity_secret

    def create_user_wallet(user_id: str) -> Dict[str, Any]:
        """
        Create a new Circle wallet for a user.
        Returns wallet ID and addresses.
        """
        # Create wallet set for user
        wallet_set = self.web3.create_wallet_set(
            name=f"usdchat-{user_id}",
            wallet_type="DEVELOPER_CONTROLLED"
        )

        # Create wallets on each chain
        wallets = self.web3.create_wallet(
            wallet_set_id=wallet_set.id,
            blockchains=["ETH-BASE", "ETH-ARBITRUM", "SOL"]
        )

        return {
            "wallet_set_id": wallet_set.id,
            "wallets": wallets
        }

    def execute_transfer(
        wallet_id: str,
        to_address: str,
        amount: Decimal,
        chain: str
    ) -> Dict[str, Any]:
        """
        Execute a transfer from Circle-managed wallet.
        Uses Circle's transaction API instead of direct signing.
        """
        pass
```

#### 2.2 Unified Interface

```python
# wallet_interface.py (to create)

class WalletInterface(ABC):
    """Abstract interface for wallet operations."""

    @abstractmethod
    def get_address(self, chain: str) -> str:
        pass

    @abstractmethod
    def get_balance(self, chain: str, token: str) -> Decimal:
        pass

    @abstractmethod
    def sign_transaction(self, tx: Dict) -> bytes:
        pass

    @abstractmethod
    def execute_transfer(
        self,
        to: str,
        amount: Decimal,
        chain: str
    ) -> Dict[str, Any]:
        pass


class SelfCustodyWallet(WalletInterface):
    """Current implementation - user manages keys."""
    pass


class CircleHostedWallet(WalletInterface):
    """Circle Programmable Wallet - Circle manages keys via MPC."""
    pass
```

#### 2.3 User Choice Flow

```
Onboarding:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│    How would you like to secure your wallet?                │
│                                                             │
│    ┌─────────────────────┐    ┌─────────────────────┐      │
│    │                     │    │                     │      │
│    │   🔐 I'll manage    │    │   ☁️ Easy setup     │      │
│    │   my own keys       │    │   (hosted)          │      │
│    │                     │    │                     │      │
│    │   • Full control    │    │   • No seed phrase  │      │
│    │   • Export anytime  │    │   • Social recovery │      │
│    │   • You're the bank │    │   • Circle custody  │      │
│    │                     │    │                     │      │
│    └─────────────────────┘    └─────────────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 3: x402 Micropayments (Horizon 3)

### What x402 Does
HTTP 402 Payment Required + USDC = instant micropayments for AI agents.

**Use Cases:**
- AI character tips
- Per-query API payments
- Agent-to-agent payments
- Pay-per-use services

### Implementation Sketch

```python
# x402_handler.py (to create)

class X402PaymentHandler:
    """
    Handle HTTP 402 payments for AI agents.

    Flow:
    1. Client requests protected resource
    2. Server returns 402 with payment details
    3. Client signs payment
    4. Server verifies and grants access
    """

    def create_payment_request(
        amount: Decimal,
        recipient: str,
        description: str,
        ttl_seconds: int = 300
    ) -> Dict[str, Any]:
        """Create a 402 payment request."""
        return {
            "payTo": recipient,
            "maxAmountRequired": str(amount),
            "asset": "USDC",
            "network": "base-mainnet",
            "expiresAt": (datetime.now() + timedelta(seconds=ttl_seconds)).isoformat()
        }

    def verify_payment(
        payment_header: str,
        expected_amount: Decimal
    ) -> bool:
        """Verify a payment from x-payment header."""
        pass
```

### Integration with AI Projects Feature

```
User creates AI Character
        │
        ▼
┌─────────────────────────────────────┐
│  Character Settings                  │
│                                      │
│  💰 Monetization                     │
│                                      │
│  ○ Free access                       │
│  ● Paid access                       │
│                                      │
│  Price per message: $0.01            │
│  Monthly subscription: $3.00         │
│                                      │
│  Payment address: 0x...              │
│  (auto-generated from your wallet)   │
└─────────────────────────────────────┘
        │
        ▼
Character gets x402-enabled endpoint
Users pay per message via USDC
```

---

## Developer Account Setup

### Required from Circle

1. **API Key** - For attestation API (CCTP)
2. **Entity ID** - For Programmable Wallets
3. **Entity Secret** - For signing wallet operations
4. **Webhook URL** - For payment/bridge notifications

### Environment Variables to Add

```env
# Circle Configuration
CIRCLE_API_KEY=your-api-key
CIRCLE_ENTITY_ID=your-entity-id
CIRCLE_ENTITY_SECRET=your-entity-secret

# Circle Endpoints
CIRCLE_API_URL=https://api.circle.com/v1
CIRCLE_ATTESTATION_URL=https://iris-api.circle.com/attestations
```

### Dashboard Access Needed
- https://console.circle.com
- Sandbox environment for testing
- Production credentials for mainnet

---

## Implementation Timeline

### Week 1-2: CCTP Foundation
- [ ] Get Circle API credentials
- [ ] Create `cctp_client.py`
- [ ] Add contract ABIs for TokenMessenger
- [ ] Implement `initiate_bridge()`
- [ ] Test on testnet (Sepolia → Base Sepolia)

### Week 3-4: CCTP Production
- [ ] Implement attestation polling
- [ ] Implement `complete_bridge()`
- [ ] Add UI for cross-chain sends
- [ ] Bridge progress tracking
- [ ] Mainnet testing

### Week 5-6: Programmable Wallets (Optional)
- [ ] Set up Circle entity
- [ ] Create `circle_wallet.py`
- [ ] Unified `WalletInterface`
- [ ] Onboarding flow updates
- [ ] Migration tool (self-custody ↔ hosted)

### Week 7-8: x402 Foundation
- [ ] Design x402 flow
- [ ] Create `x402_handler.py`
- [ ] AI character payment settings
- [ ] Test with internal agents

---

## Risk Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Circle API downtime | Bridge stuck mid-transfer | Local queue, retry logic, user notification |
| Attestation delays | Poor UX on bridges | Clear progress UI, estimated times |
| Key management (hosted) | Regulatory questions | Clear disclosure, user choice |
| x402 adoption | Low usage | Start with internal features |

---

## Success Metrics

| Metric | Target (90 days) |
|--------|------------------|
| Cross-chain transfers enabled | Yes |
| CCTP bridges completed | 100+ |
| Average bridge time | <20 min |
| Hosted wallet signups | 20% of new users |
| x402 payments processed | 50+ (internal testing) |

---

## Open Questions

1. **Should hosted wallets be default?**
   - Pro: Lower friction
   - Con: Less aligned with self-custody ethos

2. **CCTP fee handling?**
   - Who pays attestation/gas on destination?
   - Options: User pays, USDChat subsidizes, split

3. **x402 pricing?**
   - Fixed fee per payment?
   - Percentage?
   - Free for internal use?

---

## References

- [Circle Programmable Wallets Docs](https://developers.circle.com/w3s/programmable-wallets)
- [CCTP Documentation](https://developers.circle.com/stablecoins/cctp)
- [x402 Protocol Spec](https://developers.circle.com/stablecoins/x402)
- [Circle API Reference](https://developers.circle.com/api-reference)

---

*Document Owner: Engineering Team*
*Last Updated: January 2026*
