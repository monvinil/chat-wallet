# Compliance Workstream — USDChat
## Regulatory Analysis, Requirements & Sprint 0 Deliverables

**Document Owner:** Compliance Officer
**Last Updated:** February 6, 2026
**Status:** Sprint 0 — Initial Analysis Complete
**Classification:** INTERNAL — PRIVILEGED & CONFIDENTIAL

---

> **CONSERVATIVE POSTURE:** This document adopts a conservative compliance stance. It is better to over-comply and remove restrictions later than to face enforcement action, lose a Circle partnership, or have user funds seized. Requirements are clearly separated into **MUST-HAVE BEFORE LAUNCH** and **SHOULD-HAVE EVENTUALLY**.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Classification & Regulatory Mapping](#2-product-classification--regulatory-mapping)
3. [FinCEN / Bank Secrecy Act Analysis](#3-fincen--bank-secrecy-act-analysis)
4. [GENIUS Act & Stablecoin Legislation](#4-genius-act--stablecoin-legislation)
5. [State Money Transmitter Analysis](#5-state-money-transmitter-analysis)
6. [Securities Law — DeFi Yield & Agent Marketplace](#6-securities-law--defi-yield--agent-marketplace)
7. [OFAC Sanctions Screening](#7-ofac-sanctions-screening)
8. [Data Privacy — GDPR / CCPA / State Laws](#8-data-privacy--gdpr--ccpa--state-laws)
9. [AI Agent & x402 Micropayment Compliance](#9-ai-agent--x402-micropayment-compliance)
10. [Consumer Protection & Disclosures](#10-consumer-protection--disclosures)
11. [Circle Partnership Compliance Requirements](#11-circle-partnership-compliance-requirements)
12. [Requirements Matrix — Must-Have vs Should-Have](#12-requirements-matrix--must-have-vs-should-have)
13. [Sprint 0 Deliverables & Action Items](#13-sprint-0-deliverables--action-items)
14. [Risk Register](#14-risk-register)
15. [Regulatory Monitoring Calendar](#15-regulatory-monitoring-calendar)

---

## 1. Executive Summary

### Product Description (Regulatory Framing)

USDChat is a **self-custodial cryptocurrency wallet** that enables users to:
- Hold and transfer USDC stablecoins across multiple blockchains (Base, Arbitrum, Ethereum, Solana)
- Earn yield by depositing USDC into DeFi protocols (Aave)
- Set up automated dollar-cost-averaging (DCA) schedules
- Purchase gift cards via third-party providers (Bitrefill)
- Interact with AI agents that can accept micropayments (future: x402)

### Key Regulatory Risk Factors

| Factor | Risk Level | Rationale |
|--------|-----------|-----------|
| Self-custodial wallet (users control keys) | **FAVORABLE** | Generally exempt from money transmitter licensing under FinCEN guidance |
| Meta-transaction relayer (gasless txns) | **ELEVATED** | Platform signs/submits transactions on behalf of users — could be construed as transmission |
| Yield aggregation (Aave deposits) | **HIGH** | Potential unregistered investment adviser or securities intermediary |
| Agent marketplace with payments | **HIGH** | Platform facilitating third-party payments — potential money transmission |
| Fee collection (0.2% + flat fee) | **ELEVATED** | Revenue from facilitating value transfer strengthens MSB argument |
| AI-directed transactions | **ELEVATED** | Novel area — AI autonomously executing financial transactions raises fiduciary and consumer protection questions |
| Cross-chain bridging (CCTP) | **MODERATE** | Using Circle's regulated infrastructure mitigates risk |
| Gift card purchases (Bitrefill) | **MODERATE** | Bitrefill is the merchant; we're the buyer's software tool |

### Bottom Line

USDChat's **core self-custodial wallet functionality** likely falls outside money transmitter definitions under current FinCEN guidance. However, several planned features — **yield aggregation, the agent marketplace with payment facilitation, the meta-transaction relayer, and fee collection** — create regulatory gray areas that must be addressed before launch. The platform should be architected to stay clearly on the non-custodial, software-provider side of every regulatory line.

---

## 2. Product Classification & Regulatory Mapping

### Feature-by-Feature Regulatory Analysis

| Feature | Regulatory Regime | Classification | Risk |
|---------|-------------------|----------------|------|
| Wallet creation (BIP39/44) | FinCEN MSB rules | Non-custodial software provider | LOW |
| USDC send/receive | FinCEN, state MTL | Software tool (user controls keys) | LOW |
| Meta-transaction relayer | FinCEN, state MTL | **Ambiguous** — potentially facilitating transmission | MEDIUM |
| Gasless transfers (fee in USDC) | FinCEN, state MTL | Fee extraction from user funds = value handling | MEDIUM |
| Aave yield deposits | SEC (Investment Advisers Act), state securities | Potential investment advice / securities intermediary | HIGH |
| DCA scheduling | SEC, CFTC | Automated trading features | MEDIUM |
| Gift card purchases | FTC, state consumer protection | Software tool purchasing from licensed vendor | LOW |
| Agent marketplace | FinCEN, SEC, state MTL | Payment facilitation platform | HIGH |
| x402 micropayments | FinCEN, state MTL, GENIUS Act | Depends on custodial vs non-custodial implementation | HIGH |
| Cross-chain bridging (CCTP) | FinCEN | Using Circle's regulated rails | LOW-MEDIUM |
| Email invoice scanning | GDPR/CCPA, ECPA | Privacy-sensitive data processing | MEDIUM |
| AI chat with financial actions | Consumer protection, fiduciary law | Novel — AI executing financial decisions | HIGH |

### Jurisdictional Scope

| Jurisdiction | Applicability | Priority |
|-------------|---------------|----------|
| **United States (Federal)** | Primary market, FinCEN/SEC/CFTC | P0 |
| **United States (States)** | State MTL, consumer protection | P0 |
| **European Union** | If/when serving EU users (MiCA, GDPR) | P1 |
| **United Kingdom** | FCA registration if UK users | P2 |
| **Global** | OFAC sanctions apply regardless | P0 |

---

## 3. FinCEN / Bank Secrecy Act Analysis

### Current FinCEN Guidance on Self-Custodial Wallets

**Key Guidance Documents:**
- FinCEN Guidance FIN-2019-G001 (May 2019): "Application of FinCEN's Regulations to Certain Business Models Involving Convertible Virtual Currencies"
- FinCEN Proposed Rule (December 2020): Requirements for Certain Transactions Involving Convertible Virtual Currency or Digital Assets (withdrawn but informative)
- FinCEN 2024-2025 enforcement actions and no-action letters

**FinCEN's Position on Non-Custodial Wallets:**

FinCEN distinguishes between:
1. **Money transmitters** — entities that accept and transmit value on behalf of others
2. **Software providers** — entities that provide tools enabling users to manage their own value

> "An entity that provides the delivery, communication, or network access services used by a money transmitter to support money transmission services is not a money transmitter." — FinCEN 2019 Guidance

### USDChat's Classification Arguments

**Arguments FOR non-custodial software provider classification:**
- Users generate and control their own private keys (BIP39/BIP44 HD wallet)
- Keys are encrypted locally with user-chosen password (PBKDF2 + Fernet)
- Platform never has access to unencrypted private keys
- Users sign all transactions
- No omnibus wallet or pooled funds

**Arguments AGAINST (risk factors that weaken the position):**

| Risk Factor | Concern | Mitigation Required |
|-------------|---------|---------------------|
| Meta-transaction relayer | Platform submits transactions to the blockchain on behalf of users | Document that user signs the core transaction; relayer only wraps and submits |
| Fee extraction from USDC | Platform deducts fees from user funds during transactions | Ensure fee is deducted as a separate user-authorized operation, not custodial handling |
| Scheduled transactions (DCA) | Platform executes transactions without real-time user approval | Require explicit user authorization for each scheduled execution OR implement pre-signed transaction model |
| Encrypted key storage in Supabase? | If encrypted keys are stored server-side, even encrypted | **CRITICAL:** Verify keys are ONLY stored client-side. Server storage of encrypted keys is a custodial red flag |

### MUST-DO: FinCEN Compliance Requirements

Even as a non-custodial software provider, USDChat should:

1. **[ ] Register as an MSB with FinCEN** — Even non-transmitter MSBs may need to register if they deal in convertible virtual currencies above de minimis thresholds. Registration is low-cost and provides regulatory goodwill. Recommended as a precautionary measure.

2. **[ ] Implement a basic AML/KYC program** — Not legally required for pure non-custodial software providers, but:
   - Circle partnership will likely require it
   - Demonstrates good faith to regulators
   - Protects against bad actors using the platform

3. **[ ] Maintain transaction records** — Even if not a money transmitter, maintain records that can be produced if subpoenaed

4. **[ ] File Suspicious Activity Reports (SARs)** if suspicious patterns are detected — Voluntary filing demonstrates compliance posture

### Architecture Requirements

```
CRITICAL ARCHITECTURE PRINCIPLE:
The platform must NEVER have the ability to unilaterally move user funds.
Every transaction must require a user-side signature.

Current Status: NEEDS VERIFICATION
- [ ] Audit wallet_manager.py — confirm no server-side key access
- [ ] Audit meta_tx.py — confirm user signs inner transaction
- [ ] Audit scheduler_executor.py — confirm how scheduled txns are authorized
- [ ] Audit transaction_relayer.py — confirm relayer cannot redirect funds
- [ ] Verify Supabase does NOT store encrypted private keys
```

---

## 4. GENIUS Act & Stablecoin Legislation

### Current Status (February 2026)

The **Guiding and Establishing National Innovation for U.S. Stablecoins (GENIUS) Act** was signed into law in 2025, establishing the first comprehensive federal framework for payment stablecoins in the United States. Key provisions relevant to USDChat:

### Provisions Relevant to USDChat

| Provision | Impact on USDChat | Action Required |
|-----------|-------------------|-----------------|
| **Payment stablecoin definition** | USDC is a regulated payment stablecoin under the Act | Positive — regulatory clarity for our core asset |
| **Issuer requirements** | Circle (USDC issuer) must maintain 1:1 reserves, monthly attestations | No action — Circle's responsibility, but monitor compliance |
| **Non-custodial wallet treatment** | Act does not impose licensing on non-custodial wallet software | Favorable — reinforces our classification |
| **Stablecoin payment acceptance** | Federal recognition of stablecoins for commercial payments | Positive — validates our gift card and merchant payment use cases |
| **Illicit finance provisions** | Enhanced obligations for entities in stablecoin ecosystem | Monitor — may impose requirements on wallet providers in future rulemakings |
| **State/federal dual regime** | States can regulate stablecoin issuers under $10B; federal regime for larger issuers | No direct impact — we're not an issuer |

### Strategic Implications

1. **USDC-first strategy is validated** — GENIUS Act gives USDC regulatory legitimacy that most other tokens lack
2. **Self-custodial positioning is strong** — Act explicitly does not regulate non-custodial wallet software
3. **Future rulemaking risk** — Treasury and Federal Reserve will issue implementing regulations; these could impose new obligations on wallet providers
4. **Circle partnership value increases** — Circle's compliance with the Act makes our infrastructure more defensible

### Action Items

- **[ ] Monitor Treasury Department implementing regulations** — Expected Q2-Q3 2026
- **[ ] Monitor Federal Reserve stablecoin supervisory guidance** — Ongoing
- **[ ] Ensure all marketing references to USDC are accurate** — Cannot imply FDIC insurance or government backing
- **[ ] Add GENIUS Act disclosures** — "USDC is a payment stablecoin regulated under the GENIUS Act. USDC is not insured by the FDIC or any government agency."

---

## 5. State Money Transmitter Analysis

### The Core Question

Even if USDChat is not a federal money transmitter under FinCEN, **state money transmitter laws vary significantly** and may capture activities that FinCEN does not.

### State-by-State Risk Assessment

| State | MTL Regime | Non-Custodial Wallet Treatment | Risk for USDChat |
|-------|-----------|-------------------------------|-------------------|
| **New York** | BitLicense (NYDFS) | Narrowly interpreted — non-custodial may still need license if facilitating transactions | **HIGH** |
| **California** | DFPI Digital Financial Assets Law (eff. 2025) | Covers "digital financial asset transaction kiosks" and exchanges; non-custodial software unclear | **MEDIUM-HIGH** |
| **Texas** | Money Services Act | Non-custodial generally exempt; guidance favorable to software providers | **LOW** |
| **Florida** | Money Transmitter Act (updated 2023) | Virtual currency explicitly included; non-custodial exemptions exist | **MEDIUM** |
| **Wyoming** | Digital Asset Law | Most favorable regime — explicit exemptions for non-custodial software | **LOW** |
| **Illinois** | Transmitter of Money Act | Broad definition; crypto businesses have been required to obtain license | **MEDIUM-HIGH** |
| **Washington** | Money Transmitter Act (updated) | Has required licenses for crypto businesses even with limited custodial functions | **HIGH** |

### High-Risk State Analysis

#### New York BitLicense
- **Risk:** NYDFS interprets "virtual currency business activity" broadly
- **Includes:** "receiving virtual currency for transmission or transmitting virtual currency"
- **Non-custodial exemption:** Unclear — NYDFS has not issued definitive guidance
- **Our position:** Software tool only; never possess or control user funds
- **Recommendation:** **GEO-BLOCK New York users at launch** or obtain legal opinion before serving NY residents

#### California DFPI
- **Risk:** California's Digital Financial Assets Law (effective July 2025) requires licensing for entities engaged in "digital financial asset business activity"
- **Includes:** "exchanging, transferring, or storing digital financial assets"
- **Non-custodial exemption:** Exists for "providing only connectivity software or computing hardware"
- **Our position:** Likely falls under the software exemption
- **Recommendation:** Obtain California-specific legal opinion before launch

#### Washington State
- **Risk:** Washington has historically required licenses for crypto businesses
- **Includes:** Broad "money transmission" definition
- **Recommendation:** **GEO-BLOCK Washington users at launch** pending legal analysis

### Recommended Approach

**Phase 1 (Launch):**
1. **GEO-BLOCK** users in New York and Washington state
2. Operate in states with clear non-custodial exemptions (Wyoming, Texas)
3. Add state-by-state availability as legal opinions are obtained

**Phase 2 (Post-Launch):**
1. Engage MTL counsel for state-by-state analysis
2. Apply for licenses in key states if required
3. Consider applying for New York BitLicense if user demand justifies cost ($100K+ in legal/compliance costs)

### MUST-DO: State Compliance

```
BEFORE LAUNCH:
- [ ] Implement geo-blocking for NY and WA users
- [ ] Add Terms of Service restriction on NY/WA residents
- [ ] Create state availability matrix
- [ ] Obtain legal opinion for CA, FL, IL, TX (top user states)
- [ ] Implement IP-based geo-detection for restricted states
```

---

## 6. Securities Law — DeFi Yield & Agent Marketplace

### 6A. DeFi Yield Products (Aave Integration)

#### The Core Risk

When USDChat enables users to deposit USDC into Aave to earn yield, the platform may be:

1. **Acting as an unregistered investment adviser** — if the platform recommends or automatically allocates to yield strategies
2. **Offering an unregistered security** — if the yield product is structured in a way that constitutes an "investment contract" under Howey
3. **Acting as an unregistered broker-dealer** — if facilitating purchases of securities (aUSDC tokens from Aave)

#### Howey Test Analysis for USDChat Yield

| Howey Prong | Analysis | Risk |
|-------------|----------|------|
| Investment of money | User deposits USDC — yes | MET |
| Common enterprise | Pooled in Aave lending pool — yes | MET |
| Expectation of profit | APY prominently displayed — yes | MET |
| From efforts of others | Aave protocol manages lending — yes | MET |

**Conclusion:** There is a non-trivial argument that directing users into Aave yield positions involves the offer of a security. The SEC has taken enforcement actions against platforms that facilitated DeFi lending (e.g., SEC v. Coinbase for its "Lend" product, SEC enforcement against BlockFi Yield).

#### Mitigation Strategies

1. **Position as software tool, not adviser:**
   - USDChat does NOT recommend yield strategies
   - USDChat does NOT manage the yield position
   - User makes all decisions; platform merely executes user instructions
   - Display neutral information, not promotional APY "suggestions"

2. **Avoid "Earn" language in marketing:**
   - Instead of "Start Earning 8.2% APY" → "Deposit to Aave Lending Protocol"
   - Instead of "Your money earns while you sleep" → "Access DeFi lending protocols"
   - Do NOT display projected earnings as guaranteed or expected returns

3. **Add prominent risk disclosures:**
   ```
   REQUIRED DISCLOSURE (before any yield deposit):

   "DeFi Protocol Risk Disclosure:

   Depositing USDC into decentralized lending protocols involves significant risks:

   - Smart contract risk: Protocols may contain bugs that result in loss of funds
   - Liquidity risk: You may not be able to withdraw funds immediately
   - Regulatory risk: DeFi protocols may be subject to future regulatory actions
   - Market risk: Yield rates are variable and may decline to 0%
   - No FDIC insurance: Your deposits are not protected by any government agency
   - No guarantee of returns: Past APY does not guarantee future performance

   USDChat is a software tool that provides access to third-party DeFi protocols.
   USDChat does not manage, control, or guarantee any yield positions.
   You retain full custody and control of your funds at all times."
   ```

4. **Architecture requirements:**
   - [ ] User must explicitly initiate each yield deposit (no auto-deposit)
   - [ ] User must acknowledge risk disclosure before first deposit
   - [ ] No "recommended" or "suggested" allocations
   - [ ] Clear labeling of third-party protocol (Aave) vs USDChat platform
   - [ ] No pooling of user funds — each user interacts directly with Aave

### 6B. Agent Marketplace Securities Risks

#### The Risk

If agents on the marketplace:
- Offer trading strategies (Hyperliquid, Polymarket)
- Charge subscriptions for investment signals
- Pool user funds for collective strategies ("Community Vaults")

These could constitute:
- **Unregistered securities** (investment contracts)
- **Unregistered investment adviser activity**
- **Unregistered commodity trading adviser activity** (CFTC jurisdiction)

#### Community Vaults — HIGH RISK

The planned "Community Vault" feature (shared strategies, pooled capital) is the **single highest securities risk** in the entire platform.

| Howey Prong | Community Vault | Risk |
|-------------|-----------------|------|
| Investment of money | Users deposit USDC into shared vault | MET |
| Common enterprise | Capital is pooled | MET |
| Expectation of profit | Vault earns yield/trading returns | MET |
| From efforts of others | Vault strategy managed by creator | MET |

**Conclusion:** Community Vaults almost certainly constitute securities under current SEC guidance.

**Recommendation:** **DO NOT LAUNCH Community Vaults without SEC registration or exemption (e.g., Regulation D).** This feature should be removed from the roadmap until proper legal framework is established.

#### Agent Marketplace Mitigation

1. **[ ] Prohibit agents from offering investment advice** — Terms of Service must prohibit agents from making specific investment recommendations
2. **[ ] Prohibit agents from pooling user funds** — No Community Vaults without SEC registration
3. **[ ] Require agent creators to certify compliance** — Creator certification that agent does not offer securities
4. **[ ] Implement agent review process** — Review agents for securities law compliance before publication
5. **[ ] Add disclaimers to all agent interactions** — "This agent is not a registered investment adviser"

### MUST-DO: Securities Compliance

```
BEFORE LAUNCH:
- [ ] Remove or disable Community Vault feature
- [ ] Rewrite all yield-related UI copy to be neutral (not promotional)
- [ ] Add DeFi risk disclosure (mandatory acknowledgment before first deposit)
- [ ] Ensure no auto-yield (user must opt-in to each deposit)
- [ ] Remove projected earnings from marketing materials
- [ ] Add "not investment advice" disclaimers throughout

BEFORE AGENT MARKETPLACE LAUNCH:
- [ ] Agent review process for securities compliance
- [ ] Agent creator certification process
- [ ] Prohibited agent categories list (no pooled investment products)
- [ ] Legal opinion on agent marketplace structure
```

---

## 7. OFAC Sanctions Screening

### Requirements

**Office of Foreign Assets Control (OFAC) sanctions compliance is mandatory for all U.S. persons and entities, regardless of whether you are a money transmitter.** There is NO exemption for non-custodial wallet software providers.

OFAC has explicitly added cryptocurrency wallet addresses to its Specially Designated Nationals (SDN) list. The Tornado Cash enforcement action (2022-2023) established that even decentralized protocols can face sanctions.

### What USDChat Must Do

#### Tier 1 — MUST-HAVE BEFORE LAUNCH

1. **[ ] Screen all wallet addresses against OFAC SDN list before processing any transaction**
   - Screen recipient addresses before sending
   - Screen sender addresses on incoming transactions
   - Use the SDN list, which includes cryptocurrency addresses

2. **[ ] Block transactions to/from sanctioned addresses**
   - Return clear error: "This transaction cannot be processed due to compliance requirements"
   - Do NOT reveal that the specific address is sanctioned (tipping off)

3. **[ ] Block users from sanctioned jurisdictions**
   - Comprehensive Sanctions: Cuba, Iran, North Korea, Syria, Crimea/Donetsk/Luhansk regions
   - Implement IP-based geo-blocking
   - Add jurisdiction check to onboarding flow

4. **[ ] Maintain sanctions screening logs**
   - Log all screening results (hits and clears)
   - Retain for 5 years minimum

#### Tier 2 — SHOULD-HAVE (Within 90 Days of Launch)

5. **[ ] Integrate a commercial sanctions screening provider**
   - Options: Chainalysis, TRM Labs, Elliptic
   - Provides real-time address risk scoring beyond just SDN list
   - Identifies indirect exposure (addresses that have transacted with sanctioned entities)
   - **Circle partnership likely requires this**

6. **[ ] Implement ongoing transaction monitoring**
   - Monitor for patterns indicative of sanctions evasion
   - Chain-hopping, structuring, mixing service usage

7. **[ ] Establish sanctions compliance procedures**
   - Written OFAC compliance policy
   - Designated compliance officer
   - Annual risk assessment
   - Employee training

### Implementation Approach

```python
# Recommended architecture for sanctions screening

class SanctionsScreener:
    """
    OFAC sanctions screening for all transactions.

    MVP: Check against OFAC SDN list (free, updated regularly)
    Production: Integrate Chainalysis/TRM Labs for comprehensive screening
    """

    # SDN list download: https://sanctionslist.ofac.treas.gov/
    # Crypto addresses in SDN: filter by "Digital Currency Address"

    def screen_address(self, address: str) -> ScreeningResult:
        """Screen a wallet address against sanctions lists."""
        # 1. Check local SDN cache
        # 2. Check commercial provider (Chainalysis/TRM)
        # 3. Return PASS/FAIL/REVIEW
        pass

    def screen_transaction(self, from_addr: str, to_addr: str, amount: Decimal) -> ScreeningResult:
        """Screen a complete transaction."""
        # Screen both addresses
        # Check for sanctioned jurisdiction indicators
        # Log result
        pass
```

### Recommended Providers

| Provider | Cost | Features | Circle Integration |
|----------|------|----------|-------------------|
| **Chainalysis KYT** | $$$$ | Real-time screening, risk scoring, compliance reporting | Yes — Circle uses Chainalysis |
| **TRM Labs** | $$$ | Transaction monitoring, wallet screening, investigation tools | Yes — referenced in Circle brief |
| **Elliptic** | $$$ | Wallet screening, transaction monitoring | Yes |
| **OFAC SDN List (DIY)** | Free | Basic address matching only | N/A |

**Recommendation:** Start with OFAC SDN list (free) for MVP. Integrate Chainalysis or TRM Labs within 90 days, before significant user volume.

---

## 8. Data Privacy — GDPR / CCPA / State Laws

### 8A. What Personal Data USDChat Collects

| Data Type | Where Stored | Classification | Regulatory Regime |
|-----------|-------------|----------------|-------------------|
| Email address | Supabase | PII | GDPR, CCPA, state laws |
| Wallet addresses | Supabase | **Personal data** (EDPB 2025 guidance) | GDPR, CCPA |
| Transaction history | Supabase | Financial PII | GDPR, CCPA, GLBA |
| IP addresses | Server logs | PII | GDPR, CCPA |
| Chat messages (AI interactions) | Application | May contain PII | GDPR, CCPA |
| Gmail data (invoice scanning) | Temporary processing | Sensitive PII | GDPR, CCPA, ECPA |
| Encrypted private keys | **Client-side only** (verify) | Most sensitive | All regimes |
| Session data | Supabase | PII | GDPR, CCPA |
| Device/browser fingerprint | Analytics | PII under GDPR | GDPR, CCPA |

### 8B. EDPB Blockchain Guidelines (April 2025)

The European Data Protection Board's April 2025 guidelines established that:

1. **Wallet addresses are personal data** — Even pseudonymous data counts as personal data if it can be linked to an individual
2. **Transaction data on public blockchains is personal data** — Cannot be deleted (right to erasure conflict)
3. **Off-chain storage recommended** — Personal data should be kept off-chain wherever possible
4. **Data Protection Impact Assessment (DPIA) required** — Before deploying any blockchain solution that processes personal data

**Impact on USDChat:**
- Wallet addresses stored in Supabase = personal data requiring full GDPR protection
- On-chain transaction records cannot be erased = design must account for this
- DPIA must be completed before serving EU users

### 8C. CCPA/CPRA Requirements (2026 Updates)

As of January 1, 2026, CCPA threshold: businesses with >$26.6M annual revenue, or processing data of 100K+ California residents, or deriving 50%+ revenue from data sales.

**Even below thresholds, CCPA compliance is recommended because:**
- Demonstrates privacy-first posture
- Many states (Kentucky, Rhode Island, Indiana — eff. Jan 2026) have similar laws
- Cost of compliance is low relative to risk

**Key requirements:**
1. **Privacy policy** — Must disclose categories of data collected, purposes, third-party sharing
2. **Right to delete** — Must honor deletion requests for off-chain data
3. **Right to opt-out** — Of data sales/sharing (Global Privacy Control recognition required as of 2026)
4. **Right to access** — Users can request all data collected about them
5. **Automated decision-making disclosures** — CCPA 2026 requires disclosure of AI/automated systems used in decision-making (directly relevant to USDChat's AI-driven transactions)

### 8D. Gmail Integration Privacy Risks

The Gmail invoice scanning feature presents **elevated privacy risks:**

| Risk | Severity | Mitigation |
|------|----------|------------|
| Accessing user email content | HIGH | Explicit consent, minimal scope OAuth, process-and-discard |
| Storing invoice data | MEDIUM | Encrypt at rest, auto-delete after processing |
| Google API compliance | HIGH | Must comply with Google API Services User Data Policy |
| ECPA (Electronic Communications Privacy Act) | MEDIUM | User consent required for email access |

**Requirements:**
- [ ] Google OAuth scope must be minimal (read-only, specific labels)
- [ ] Invoice data processed in memory, not persisted
- [ ] Explicit user consent with clear explanation of what data is accessed
- [ ] Google API compliance verification (annual)

### MUST-DO: Privacy Compliance

```
BEFORE LAUNCH:
- [ ] Write and publish Privacy Policy
- [ ] Write and publish Terms of Service
- [ ] Implement data deletion capability (right to delete)
- [ ] Add cookie consent banner (if using analytics cookies)
- [ ] Implement data export capability (right to access/portability)
- [ ] Add AI/automated decision-making disclosure
- [ ] Conduct Data Protection Impact Assessment (if serving EU users)
- [ ] Verify Global Privacy Control (GPC) signal recognition

BEFORE GMAIL FEATURE LAUNCH:
- [ ] Google API Services compliance review
- [ ] Explicit consent flow for email access
- [ ] Data minimization audit (process-and-discard)
- [ ] ECPA compliance review
```

---

## 9. AI Agent & x402 Micropayment Compliance

### 9A. AI Agent Regulatory Considerations

USDChat's AI executes financial transactions based on natural language instructions. This creates novel regulatory questions:

| Question | Current Regulatory Position | Our Approach |
|----------|-----------------------------|--------------|
| Can AI execute financial transactions? | No specific prohibition, but consumer protection applies | User must confirm every transaction |
| Is AI-driven investing "investment advice"? | Likely yes if AI recommends specific investments | AI must NOT recommend; only execute user instructions |
| Who is liable for AI errors? | Platform likely bears responsibility | Transaction limits, confirmation required, audit trail |
| Must AI decisions be explainable? | CCPA 2026 requires automated decision-making disclosure | Log all AI decisions with reasoning |

### Requirements for AI Financial Actions

1. **[ ] Mandatory transaction confirmation** — No AI-initiated transaction should execute without user confirmation
2. **[ ] Transaction limits** — Implement per-transaction and daily limits that users configure
3. **[ ] Decision audit trail** — Log every AI decision with:
   - User's original instruction
   - AI's interpretation
   - Actions taken
   - Amounts involved
   - Timestamp
4. **[ ] Error handling** — If AI misinterprets instruction, user must be able to dispute/reverse
5. **[ ] Disclosures** — "Transactions are executed by AI based on your instructions. Review all transaction details before confirming."

### 9B. x402 Micropayment Compliance

The x402 protocol for AI agent micropayments creates specific compliance challenges:

#### Regulatory Analysis

Per legal analysis from Braumiller Law Group (December 2025), x402's legal status depends on:
1. **What assets are moved** (USDC — a regulated payment stablecoin)
2. **Who operates the facilitator/wallet** (Coinbase hosted vs. self-hosted)
3. **Use case** (consumer payments vs. B2B/machine-to-machine)

**USDChat's x402 position:**
- Self-custodial wallet → user controls signing → lower regulatory risk
- BUT platform facilitates discovery and connection → potential payment facilitator
- Agent marketplace creates a multi-sided payment platform → elevated risk

#### x402 Compliance Requirements

1. **[ ] Use Circle's Gateway or Coinbase's facilitator** — Do NOT build a custom x402 facilitator (inherits their compliance)
2. **[ ] Implement per-transaction sanctions screening** — Even for micropayments
3. **[ ] Set micropayment limits** — Cap per-transaction and daily x402 spend
4. **[ ] Agent payment disclosures** — Users must know they are paying for agent services before payment executes
5. **[ ] Refund mechanism** — Must have process for erroneous micropayments

### 9C. Agent Marketplace Platform Liability

As a platform facilitating payments between agent creators and users:

| Risk | Concern | Mitigation |
|------|---------|------------|
| Money transmission | Facilitating payments between parties | Ensure USDChat never takes custody of funds; payments are direct wallet-to-wallet |
| Agent fraud | Agent creators scamming users | Review process, refund policy, creator identity verification |
| Tax reporting | 1099-K obligations for agent creators | Collect W-9 from creators earning above thresholds; file 1099-K |
| Content liability | Section 230 protections | Terms of Service establishing platform-as-intermediary |

---

## 10. Consumer Protection & Disclosures

### Required Disclosures

The following disclosures must be prominently displayed and acknowledged by users:

#### Disclosure 1: General Risk Disclosure (Onboarding)

```
IMPORTANT DISCLOSURES:

USDChat is a self-custodial cryptocurrency wallet. By using USDChat, you acknowledge:

1. SELF-CUSTODY RISK: You are solely responsible for safeguarding your wallet
   recovery phrase (seed phrase). If you lose your recovery phrase, your funds
   cannot be recovered by USDChat or any third party.

2. NO FDIC INSURANCE: USDC and other digital assets held in your wallet are
   NOT insured by the Federal Deposit Insurance Corporation (FDIC) or any
   government agency.

3. STABLECOIN RISK: While USDC is designed to maintain a 1:1 peg with the
   U.S. dollar, there is no guarantee that USDC will always maintain this peg.
   USDC is regulated under the GENIUS Act but is not a bank deposit.

4. SMART CONTRACT RISK: Interactions with DeFi protocols (including yield
   deposits) involve smart contract risk. Smart contracts may contain bugs
   that could result in partial or total loss of deposited funds.

5. IRREVERSIBLE TRANSACTIONS: Cryptocurrency transactions are generally
   irreversible. Sending funds to the wrong address may result in permanent
   loss.

6. REGULATORY RISK: The regulatory environment for digital assets is evolving.
   Changes in law or regulation may affect your ability to use USDChat or
   access your funds through this platform.

7. AI-ASSISTED TRANSACTIONS: USDChat uses artificial intelligence to interpret
   your instructions. AI may misinterpret instructions. Always review
   transaction details before confirming.

8. NOT INVESTMENT ADVICE: USDChat does not provide investment, financial,
   tax, or legal advice. Consult a qualified professional before making
   financial decisions.
```

#### Disclosure 2: DeFi Yield Disclosure (Before First Deposit)

See Section 6A above.

#### Disclosure 3: Fee Disclosure (Before Each Transaction)

```
TRANSACTION FEE DISCLOSURE:

This transaction includes a fee of $[X.XX] (0.2% + $0.005, max $3.00).
This fee is charged by USDChat for facilitating this transaction.
Network gas fees, if applicable, are separate and paid to blockchain validators.

Transaction amount: $[X.XX]
USDChat fee: $[X.XX]
Estimated gas fee: $[X.XX]
Total: $[X.XX]
```

### Additional Consumer Protection Requirements

1. **[ ] Clear fee schedule** — Published, easy-to-find fee schedule
2. **[ ] Transaction receipts** — Email/in-app receipt for every transaction
3. **[ ] Dispute process** — Published process for disputing transactions or reporting errors
4. **[ ] Contact information** — Published customer support contact
5. **[ ] Cooling-off period** — Consider 24-hour cancellation window for large transactions
6. **[ ] Account recovery** — Clear documentation of what happens if user loses access

---

## 11. Circle Partnership Compliance Requirements

### Expected Circle Requirements

Based on Circle's public partner requirements and the executive brief, Circle will likely require:

| Requirement | Status | Priority |
|-------------|--------|----------|
| AML/KYC program | NOT IMPLEMENTED | P0 — CRITICAL |
| Sanctions screening (OFAC) | NOT IMPLEMENTED | P0 — CRITICAL |
| Transaction monitoring | NOT IMPLEMENTED | P0 — CRITICAL |
| Privacy policy | NOT IMPLEMENTED | P0 |
| Terms of Service | NOT IMPLEMENTED | P0 |
| Security audit | NOT COMPLETED | P1 |
| SOC 2 compliance | NOT STARTED | P2 |
| Incident response plan | NOT WRITTEN | P1 |
| Data processing agreement | NOT SIGNED | P1 |

### What Circle Partnership Requires Before Signing

Based on industry standard partnership requirements for stablecoin infrastructure:

1. **Written AML/KYC policy** — Even if light-touch for non-custodial
2. **OFAC screening integration** — Ideally Chainalysis or TRM Labs (Circle's preferred vendors)
3. **Published Terms of Service and Privacy Policy** — Legal foundation
4. **Security assessment** — At minimum, a penetration test report
5. **Compliance officer designation** — Named individual responsible for compliance
6. **Insurance** — Errors & omissions, cyber liability
7. **Incident response plan** — Written plan for security breaches, regulatory inquiries

### MUST-DO: Circle Partnership Readiness

```
BEFORE CIRCLE ENGAGEMENT:
- [ ] Write AML/KYC policy document
- [ ] Implement OFAC sanctions screening (at minimum SDN list)
- [ ] Write and publish Terms of Service
- [ ] Write and publish Privacy Policy
- [ ] Designate compliance officer (can be founding team member initially)
- [ ] Write incident response plan
- [ ] Schedule security audit / penetration test
- [ ] Prepare compliance documentation package for Circle review
```

---

## 12. Requirements Matrix — Must-Have vs Should-Have

### MUST-HAVE BEFORE LAUNCH (Blockers)

| # | Requirement | Category | Effort | Status |
|---|-------------|----------|--------|--------|
| 1 | **Terms of Service** | Legal | Medium | NOT STARTED |
| 2 | **Privacy Policy** | Legal/Privacy | Medium | NOT STARTED |
| 3 | **OFAC sanctions screening (SDN list)** | Sanctions | Medium | NOT STARTED |
| 4 | **Geo-blocking for sanctioned countries** | Sanctions | Low | NOT STARTED |
| 5 | **Geo-blocking for NY and WA states** | State MTL | Low | NOT STARTED |
| 6 | **DeFi yield risk disclosure** | Securities | Low | NOT STARTED |
| 7 | **General risk disclosures (onboarding)** | Consumer Protection | Low | NOT STARTED |
| 8 | **Fee disclosure before each transaction** | Consumer Protection | Low | NOT STARTED |
| 9 | **Transaction confirmation for all actions** | Consumer Protection | Low | PARTIAL |
| 10 | **Verify non-custodial architecture** (audit key handling) | FinCEN | Medium | NOT STARTED |
| 11 | **Remove/disable Community Vault feature** | Securities | Low | NOT STARTED |
| 12 | **Rewrite yield UI copy** (neutral, not promotional) | Securities | Low | NOT STARTED |
| 13 | **AI automated decision-making disclosure** | CCPA 2026 | Low | NOT STARTED |
| 14 | **Data deletion capability** | Privacy | Medium | NOT STARTED |
| 15 | **Cookie/analytics consent** | Privacy | Low | NOT STARTED |

### SHOULD-HAVE WITHIN 90 DAYS OF LAUNCH

| # | Requirement | Category | Effort | Status |
|---|-------------|----------|--------|--------|
| 16 | Commercial sanctions screening (Chainalysis/TRM) | Sanctions | High ($$) | NOT STARTED |
| 17 | AML/KYC program (written policy) | FinCEN | Medium | NOT STARTED |
| 18 | MSB registration with FinCEN | FinCEN | Low | NOT STARTED |
| 19 | Transaction monitoring system | AML | High | NOT STARTED |
| 20 | Incident response plan | Security | Medium | NOT STARTED |
| 21 | Security audit / penetration test | Security | High ($$) | NOT STARTED |
| 22 | State legal opinions (CA, FL, IL, TX) | State MTL | High ($$) | NOT STARTED |
| 23 | Data Protection Impact Assessment | GDPR | Medium | NOT STARTED |
| 24 | Agent review process (securities screening) | Securities | Medium | NOT STARTED |
| 25 | Data export capability (right to access) | Privacy | Medium | NOT STARTED |
| 26 | SAR filing procedures | AML | Medium | NOT STARTED |
| 27 | Decision audit trail for AI actions | Consumer Protection | Medium | NOT STARTED |

### SHOULD-HAVE EVENTUALLY (6-12 Months)

| # | Requirement | Category | Effort | Status |
|---|-------------|----------|--------|--------|
| 28 | SOC 2 Type II compliance | Security | Very High ($$$$) | NOT STARTED |
| 29 | State MTL applications (if required) | State MTL | Very High ($$$$) | NOT STARTED |
| 30 | BitLicense application (if entering NY) | State MTL | Very High ($$$$) | NOT STARTED |
| 31 | Insurance (E&O, cyber) | Risk | High ($$) | NOT STARTED |
| 32 | Agent creator identity verification | KYC | Medium | NOT STARTED |
| 33 | Tax reporting (1099-K for agent creators) | Tax | High | NOT STARTED |
| 34 | Google API compliance audit (Gmail feature) | Privacy | Medium | NOT STARTED |
| 35 | Annual compliance risk assessment | All | Medium | NOT STARTED |
| 36 | Employee compliance training program | All | Medium | NOT STARTED |
| 37 | MiCA compliance assessment (EU expansion) | EU Regulation | High | NOT STARTED |

---

## 13. Sprint 0 Deliverables & Action Items

### Sprint 0 Completed Tasks

- [x] **Regulatory landscape analysis** — Comprehensive review of FinCEN, SEC, CFTC, OFAC, GDPR, CCPA, state MTL, and GENIUS Act requirements
- [x] **Product feature risk assessment** — Feature-by-feature regulatory classification
- [x] **Requirements matrix** — Prioritized list of compliance requirements
- [x] **Risk register** — Identified and rated regulatory risks
- [x] **Circle partnership compliance gap analysis** — Identified what Circle will require

### Immediate Action Items (Sprint 1 — Next 2 Weeks)

| # | Action | Owner | Priority | Estimated Effort |
|---|--------|-------|----------|-----------------|
| 1 | **Audit key handling architecture** — Verify no server-side key access in wallet_manager.py, meta_tx.py, scheduler_executor.py, transaction_relayer.py | Engineering | P0 | 1 day |
| 2 | **Draft Terms of Service** | Legal/Compliance | P0 | 3-5 days |
| 3 | **Draft Privacy Policy** | Legal/Compliance | P0 | 3-5 days |
| 4 | **Implement OFAC SDN list screening** | Engineering | P0 | 2-3 days |
| 5 | **Implement geo-blocking** (sanctioned countries + NY + WA) | Engineering | P0 | 1-2 days |
| 6 | **Write risk disclosures** (onboarding, yield, fees) | Compliance | P0 | 1-2 days |
| 7 | **Rewrite yield UI copy** — Remove promotional language | Product/Engineering | P0 | 1 day |
| 8 | **Disable Community Vault references** in codebase | Engineering | P0 | 0.5 days |
| 9 | **Engage compliance counsel** — Obtain quotes from crypto-specialized law firms | Founder | P0 | Ongoing |

### Sprint 2 (Weeks 3-4)

| # | Action | Owner | Priority |
|---|--------|-------|----------|
| 10 | Finalize and publish ToS and Privacy Policy | Legal | P0 |
| 11 | Write AML/KYC policy document | Compliance | P1 |
| 12 | Implement data deletion capability | Engineering | P1 |
| 13 | Implement cookie consent mechanism | Engineering | P1 |
| 14 | Begin MSB registration process with FinCEN | Compliance | P1 |
| 15 | Write incident response plan | Security/Compliance | P1 |

### Sprint 3 (Weeks 5-6)

| # | Action | Owner | Priority |
|---|--------|-------|----------|
| 16 | Evaluate and select sanctions screening vendor (Chainalysis/TRM) | Compliance | P1 |
| 17 | Obtain legal opinions for priority states (CA, FL, IL, TX) | Legal | P1 |
| 18 | Implement transaction monitoring baseline | Engineering | P1 |
| 19 | Prepare Circle compliance documentation package | Compliance | P1 |
| 20 | Implement AI decision audit trail | Engineering | P1 |

---

## 14. Risk Register

| # | Risk | Likelihood | Impact | Severity | Mitigation | Owner |
|---|------|-----------|--------|----------|------------|-------|
| R1 | **SEC enforcement for yield products** | Medium | Critical | **HIGH** | Neutral UI copy, risk disclosures, no investment advice, no auto-deposit | Compliance |
| R2 | **State AG action for unlicensed MTL** | Medium | High | **HIGH** | Geo-blocking, legal opinions, license applications where required | Legal |
| R3 | **OFAC violation (sanctioned address)** | Low | Critical | **HIGH** | SDN screening, commercial provider, sanctioned country blocking | Engineering |
| R4 | **Circle rejects partnership due to compliance gaps** | High | High | **HIGH** | Complete compliance checklist before engagement | Compliance |
| R5 | **GDPR enforcement (EU users)** | Low-Medium | High | **MEDIUM** | DPIA, privacy policy, data deletion, consent management | Compliance |
| R6 | **Community Vault classified as security** | High | Critical | **CRITICAL** | Do not launch without SEC registration/exemption | Legal |
| R7 | **Agent marketplace classified as payment facilitator** | Medium | High | **HIGH** | Direct wallet-to-wallet payments, no custody of agent funds | Engineering |
| R8 | **AI transaction error causes financial loss** | Medium | Medium | **MEDIUM** | Confirmation required, transaction limits, audit trail | Engineering |
| R9 | **Data breach exposing user PII** | Low-Medium | Critical | **HIGH** | Security audit, encryption at rest, incident response plan | Security |
| R10 | **FinCEN reclassifies non-custodial wallets** | Low | High | **MEDIUM** | Architecture flexibility, MSB registration as precaution | Legal |
| R11 | **Meta-transaction relayer treated as money transmission** | Medium | High | **HIGH** | Legal opinion on relayer architecture, potentially restructure fee model | Legal |
| R12 | **New state privacy laws (2026-2027)** | High | Medium | **MEDIUM** | Privacy-by-design approach, GPC recognition, proactive compliance | Compliance |

---

## 15. Regulatory Monitoring Calendar

### Ongoing Monitoring Required

| Item | Frequency | Source | Owner |
|------|-----------|--------|-------|
| OFAC SDN list updates | Weekly | treasury.gov | Engineering (automated) |
| FinCEN guidance and rulemakings | Monthly | fincen.gov | Compliance |
| SEC enforcement actions (DeFi/crypto) | Weekly | sec.gov | Compliance |
| GENIUS Act implementing regulations | Monthly | treasury.gov, federalreserve.gov | Compliance |
| State MTL legislative changes | Quarterly | National state survey | Legal |
| GDPR/EDPB guidance updates | Quarterly | edpb.europa.eu | Compliance |
| CCPA/CPRA rulemaking | Quarterly | oag.ca.gov, cppa.ca.gov | Compliance |
| Circle compliance requirements | As updated | Circle partner portal | Compliance |
| x402 protocol governance/standards | Monthly | x402.org, x402 Foundation | Engineering |
| New state privacy laws | Quarterly | IAPP tracker | Compliance |

### Key 2026 Dates

| Date | Event | Impact |
|------|-------|--------|
| Q1 2026 | GENIUS Act implementing regulations expected | May impose new obligations |
| January 1, 2026 | Kentucky, Rhode Island, Indiana privacy laws effective | New state compliance obligations |
| Q2 2026 | Treasury stablecoin supervision guidance expected | May affect USDC ecosystem |
| Ongoing | SEC DeFi enforcement actions | May affect yield product legality |
| Ongoing | State AG cryptocurrency enforcement | Monitor for relevant precedents |

---

## Appendix A: Recommended Legal Counsel

For crypto-specialized compliance counsel, consider firms with demonstrated expertise in:
- Non-custodial wallet regulatory classification
- State money transmitter licensing
- SEC/CFTC digital asset enforcement defense
- OFAC sanctions compliance for crypto
- Circle/stablecoin ecosystem legal

**Note:** Engaging qualified legal counsel is the **single most important compliance action** the team can take. This document provides a framework, but many conclusions require formal legal opinions.

---

## Appendix B: Compliance Architecture Recommendations

### Recommended Technical Stack

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COMPLIANCE MIDDLEWARE LAYER                        │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   SANCTIONS   │  │  GEO-FENCE   │  │   CONSENT    │              │
│  │   SCREENING   │  │   SERVICE    │  │   MANAGER    │              │
│  │              │  │              │  │              │              │
│  │  • OFAC SDN  │  │  • IP-based  │  │  • Cookie    │              │
│  │  • TRM/Chain │  │  • GPS (mob) │  │  • Privacy   │              │
│  │  • Tx monitor│  │  • State/JX  │  │  • GPC signal│              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   DISCLOSURE  │  │   AUDIT LOG  │  │  RATE LIMIT  │              │
│  │   ENGINE     │  │   SERVICE    │  │  & LIMITS    │              │
│  │              │  │              │  │              │              │
│  │  • Risk disc │  │  • AI decis  │  │  • Per-tx    │              │
│  │  • Fee disc  │  │  • Screen    │  │  • Daily     │              │
│  │  • ToS/PP    │  │  • Consent   │  │  • Velocity  │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Integration Points

Every transaction in USDChat should pass through:

1. **Pre-transaction:** Sanctions screening → Geo-fence check → Rate limit check → Disclosure display → User confirmation
2. **Post-transaction:** Audit log → Transaction monitoring → Receipt generation
3. **Ongoing:** SDN list updates → Consent management → Regulatory monitoring

---

## Appendix C: Research Sources

This analysis drew on the following sources (February 2026):

- FinCEN Guidance FIN-2019-G001 (May 2019) — Application of Regulations to CVC Business Models
- GENIUS Act (2025) — Stablecoin regulatory framework
- SEC v. Coinbase (2023-2024) — DeFi lending product enforcement
- SEC v. BlockFi (2022) — Yield product enforcement
- OFAC SDN List — sanctionslist.ofac.treas.gov
- EDPB Guidelines on blockchain and personal data (April 2025)
- CCPA/CPRA 2026 amendments — California Privacy Protection Agency
- Braumiller Law Group — x402 legal framework analysis (December 2025)
- Circle USDC regulatory compliance documentation
- State money transmitter statutes (NY, CA, WA, TX, WY, FL, IL)

---

*Document Owner: Compliance Officer*
*Created: February 6, 2026*
*Last Updated: February 6, 2026*
*Next Review: March 6, 2026*
*Status: Sprint 0 COMPLETE — Awaiting legal counsel engagement for formal opinions*
