# Workstream: Compliance Officer

> **Owner**: Compliance session
> **Status**: Awaiting session start
> **Last updated**: 2026-02-06

---

## Mandate

You are the compliance officer. You own:
- Regulatory landscape analysis (US federal, state, international)
- Money transmission licensing requirements
- KYC/AML obligations assessment
- Privacy law compliance (GDPR, CCPA, etc.)
- Terms of service and privacy policy needs
- Geographic restriction recommendations
- Sanctions screening requirements (OFAC)
- Securities law implications (agent marketplace, yield products)

Your job is to answer: **"What legal/regulatory risks exist, and what must we do before launching?"**

You have **web search access** for researching current regulations.

---

## Context to Read First

1. `docs/COMMAND_CENTER.md` - Project overview
2. `docs/STRATEGIC_DIRECTION.md` - Part 6: "What We Don't Do" (non-custodial, no token, USDC only)
3. `docs/VISION_2026.md` - Part VII: Risk register, Part V: GTM and user segments
4. `docs/CIRCLE_EXECUTIVE_BRIEF.txt` - Regulatory positioning vis-a-vis Circle

## Key Product Characteristics (Compliance-Relevant)
- **Self-custodial**: Users hold their own keys. Platform never has custody.
- **USDC only**: No native token, no ICO, no securities.
- **Multi-chain**: Base, Arbitrum, Ethereum, Solana.
- **AI-driven**: Claude AI executes transactions on user's behalf (with confirmation).
- **Yield**: Routes user funds to Aave (DeFi lending protocol).
- **Agent marketplace**: Third-party agents can accept payments (x402).
- **Gift cards**: Purchases via Bitrefill (indirect merchant payments).
- **Gasless transactions**: Platform relays transactions, charges fee in USDC.
- **Email automation**: Reads user's Gmail for verification codes (OAuth).
- **Scheduled transactions**: Automated recurring payments.
- **Target markets**: Initially US, potentially global.

---

## Sprint 0 Tasks

### 1. Money Transmission Analysis
- [ ] Is USDChat a money transmitter under FinCEN rules?
- [ ] Does "self-custodial + gasless meta-transactions" change the analysis?
- [ ] Does the transaction relayer (which submits txs on behalf of users) create custody?
- [ ] What about the yield routing (platform moves user funds to Aave)?
- [ ] State-by-state money transmitter license requirements
- [ ] Research: how do similar self-custodial wallets (MetaMask, Phantom) handle this?

### 2. Securities Law
- [ ] Does the yield product (Aave routing) constitute an investment contract?
- [ ] Does the agent marketplace create securities (agents as investment vehicles)?
- [ ] Is the 70/20/10 revenue split a security?
- [ ] Do "trading bot" agents trigger broker-dealer requirements?
- [ ] Research: Howey test application to DeFi yield products in 2026

### 3. KYC/AML Requirements
- [ ] What KYC is required for a self-custodial wallet?
- [ ] Does transaction fee collection trigger KYC obligations?
- [ ] At what volume thresholds do reporting requirements kick in?
- [ ] OFAC sanctions screening: is it required? How to implement?
- [ ] Travel Rule compliance for transfers
- [ ] Research: current FinCEN guidance on self-custodial wallets (2025-2026)

### 4. Privacy & Data Protection
- [ ] GDPR implications (if serving EU users)
- [ ] CCPA implications (if serving California users)
- [ ] Gmail OAuth data handling requirements (Google API Terms)
- [ ] What user data is collected and stored? (Audit the database schema)
- [ ] Data retention policies needed
- [ ] Right to deletion implementation requirements

### 5. Stablecoin Regulation
- [ ] Current status of GENIUS Act (stablecoin legislation)
- [ ] Impact on USDC and USDChat if passed
- [ ] Circle's regulatory status and how it affects us
- [ ] State-level stablecoin regulations

### 6. Terms of Service & Legal Documents
- [ ] What legal documents are needed before launch?
  - Terms of Service
  - Privacy Policy
  - Acceptable Use Policy
  - Agent Marketplace Terms (for creators)
  - Risk Disclosures
- [ ] What disclaimers are needed for yield products?
- [ ] What liability limitations are appropriate?

### 7. Geographic Strategy
- [ ] Which countries/states should be blocked at launch?
- [ ] IP-based geoblocking or more robust geo-restriction?
- [ ] Specific state restrictions (NY BitLicense, etc.)

---

## Findings

_Write your regulatory findings here._

### Money Transmission

### Securities

### KYC/AML

### Privacy

### Stablecoin Regulation

---

## Recommendations

### Must-Have Before Launch (Blocking)

### Should-Have Before Scale (Important)

### Nice-to-Have (Future)

---

## Risk Matrix

| Risk | Severity | Likelihood | Mitigation |
|------|----------|-----------|------------|

---

## Urgent Flags

_Flag anything that could result in legal liability or regulatory action._

---
