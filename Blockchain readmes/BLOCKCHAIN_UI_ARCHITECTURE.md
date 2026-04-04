# Blockchain UI Architecture Diagram

## System Architecture with Blockchain Integration

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE (Browser)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Audit      │  │  Blockchain  │  │   Latest     │              │
│  │   Form       │  │   Status     │  │   Result     │              │
│  │              │  │   Panel      │  │   + BC Info  │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                  │                       │
│         │                 │                  │                       │
│         └─────────────────┴──────────────────┘                       │
│                           │                                          │
│                           │ HTTP/WebSocket                           │
└───────────────────────────┼──────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND (webapp.py)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  POST /api/audit                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  1. run_audit(request)                                       │   │
│  │     ├─ calculate_carbon_score()                              │   │
│  │     │  └─ [Blockchain] anchor_score() ──────────────┐       │   │
│  │     ├─ enforce_policy_hitl()                         │       │   │
│  │     ├─ generate_ai_report()                          │       │   │
│  │     └─ [Blockchain] register_report_hash() ─────────┤       │   │
│  └─────────────────────────────────────────────────────┼───────┘   │
│                                                         │             │
│  POST /api/approvals/{id}/approve                      │             │
│  ┌─────────────────────────────────────────────────────┼───────┐   │
│  │  2. approve_audit(id, approval)                     │       │   │
│  │     └─ [Blockchain] record_hitl_decision() ─────────┤       │   │
│  └─────────────────────────────────────────────────────┼───────┘   │
│                                                         │             │
│  GET /api/blockchain/status                            │             │
│  ┌─────────────────────────────────────────────────────┼───────┐   │
│  │  3. blockchain_status()                             │       │   │
│  │     └─ get_blockchain_client().get_status() ────────┤       │   │
│  └─────────────────────────────────────────────────────┼───────┘   │
│                                                         │             │
└─────────────────────────────────────────────────────────┼─────────────┘
                                                          │
                                                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                BLOCKCHAIN CLIENT (blockchain_client.py)              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  CfoEBlockchainClient                                                │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  • connect()                                                │    │
│  │  • anchor_score()          ──┐                              │    │
│  │  • record_hitl_decision()  ──┼─ _send_note_tx()            │    │
│  │  • register_report_hash()  ──┘                              │    │
│  │  • get_balance()                                            │    │
│  │  • get_status_report()                                      │    │
│  └────────────────────────────────────────────────────────────┘    │
│                           │                                          │
│                           │ algosdk                                  │
└───────────────────────────┼──────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ALGORAND BLOCKCHAIN NETWORK                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Testnet Node: https://testnet-api.algonode.cloud                   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Transaction Types:                                           │  │
│  │                                                                │  │
│  │  1. Score Anchor (CfoE_SCORE_ANCHOR)                         │  │
│  │     • supplier_name                                           │  │
│  │     • risk_score (scaled x100)                               │  │
│  │     • classification                                          │  │
│  │     • input_data_hash (SHA-256)                              │  │
│  │     • timestamp                                               │  │
│  │                                                                │  │
│  │  2. HITL Decision (CfoE_HITL_DECISION)                       │  │
│  │     • supplier_name                                           │  │
│  │     • decision (APPROVED/REJECTED)                           │  │
│  │     • risk_score_at_decision                                 │  │
│  │     • auditor_address (wallet signature = proof)             │  │
│  │     • score_anchor_tx (links to score)                       │  │
│  │                                                                │  │
│  │  3. Report Hash (CfoE_REPORT_HASH)                           │  │
│  │     • supplier_name                                           │  │
│  │     • report_sha256                                           │  │
│  │     • verification_code                                       │  │
│  │     • score_anchor_tx (chain of custody)                     │  │
│  │     • hitl_decision_tx (chain of custody)                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

### Normal Audit Flow (Low/Moderate Risk)

```
User Input
   │
   ├─ Supplier Name: "TestCorp"
   ├─ Emissions: 2500 tons
   └─ Violations: 2
   │
   ▼
┌──────────────────────────────────────┐
│ Step 1: Calculate Risk Score         │
│ ├─ emissions_score = 0.30            │
│ ├─ violations_score = 0.15           │
│ └─ risk_score = 0.45 (Moderate)      │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ [BLOCKCHAIN] Anchor Score             │
│ ├─ TX Type: CfoE_SCORE_ANCHOR        │
│ ├─ Data Hash: SHA256(input)          │
│ ├─ TX ID: SCORE-0001                 │
│ └─ Status: On-Chain ✓                │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ Step 2: Enforce Policy                │
│ ├─ Decision: Continue monitoring     │
│ ├─ HITL Required: No                 │
│ └─ Action: Quarterly review          │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ Step 3: Generate AI Report           │
│ ├─ Source: groq-llama                │
│ ├─ Length: 1500 chars                │
│ └─ Content: Executive summary...     │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ [BLOCKCHAIN] Register Report Hash     │
│ ├─ TX Type: CfoE_REPORT_HASH         │
│ ├─ Report Hash: SHA256(report)       │
│ ├─ Verify Code: A3F2B8C9D1E4         │
│ ├─ TX ID: REPORT-0001                │
│ └─ Status: On-Chain ✓                │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ Step 4: Finalize & Store              │
│ ├─ Save to history.json              │
│ ├─ Export PDF/DOCX                   │
│ └─ Update metrics                    │
└──────────────┬───────────────────────┘
               │
               ▼
         User sees result
         with blockchain info
```

### Critical Risk Audit Flow (HITL Required)

```
User Input (High Risk)
   │
   ├─ Supplier Name: "DangerCorp"
   ├─ Emissions: 15000 tons
   └─ Violations: 25
   │
   ▼
┌──────────────────────────────────────┐
│ Step 1: Calculate Risk Score         │
│ ├─ emissions_score = 0.60            │
│ ├─ violations_score = 0.25           │
│ └─ risk_score = 0.85 (CRITICAL)      │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ [BLOCKCHAIN] Anchor Score             │
│ ├─ TX Type: CfoE_SCORE_ANCHOR        │
│ ├─ Data Hash: SHA256(input)          │
│ ├─ TX ID: SCORE-0002                 │
│ └─ Status: On-Chain ✓                │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ Step 2: Enforce Policy                │
│ ├─ Decision: SUSPEND IMMEDIATELY     │
│ ├─ HITL Required: YES ⚠️             │
│ └─ Status: PENDING_APPROVAL          │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ 🚨 WORKFLOW PAUSED                   │
│ Audit moved to Pending Approvals     │
│ Awaiting human review...             │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ Human Reviews & Decides               │
│ ├─ Reviewer: John Doe                │
│ ├─ Decision: APPROVE                 │
│ └─ Notes: Verified with supplier     │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ [BLOCKCHAIN] Record HITL Decision     │
│ ├─ TX Type: CfoE_HITL_DECISION       │
│ ├─ Decision: APPROVED                │
│ ├─ Auditor: 4KG534Q6BUNUN...         │
│ ├─ Signature: Wallet-signed ✓        │
│ ├─ TX ID: HITL-0001                  │
│ └─ Status: On-Chain ✓                │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ Step 3: Generate AI Report           │
│ (continues as normal...)             │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ [BLOCKCHAIN] Register Report Hash     │
│ (continues as normal...)             │
└──────────────┬───────────────────────┘
               │
               ▼
         Audit complete with
         full blockchain trail:
         Score → HITL → Report
```

## UI Component Hierarchy

```
index.html
│
├─ Audit Form Panel
│  ├─ Input fields
│  ├─ Submit button
│  └─ Log panel (WebSocket)
│
├─ Portfolio Metrics Panel
│  └─ Metric cards (4x)
│
├─ 🆕 Blockchain Status Panel
│  └─ Blockchain grid
│     ├─ Connection status
│     ├─ Network info
│     ├─ Wallet address
│     ├─ Balance
│     └─ Transaction counts
│
├─ Latest Result Panel
│  ├─ Audit details
│  └─ 🆕 Blockchain Info Section
│     ├─ Status badge
│     ├─ Score TX
│     ├─ Data hash
│     ├─ Verification code
│     ├─ Report TX
│     └─ HITL TX (if applicable)
│
├─ Pending Approvals Panel
│  └─ Approval cards
│     └─ Review button → Approval Dialog
│        └─ 🆕 Records HITL on blockchain
│
├─ Audit History Panel
│  └─ History table
│     └─ Info button → Info Dialog
│        └─ 🆕 Blockchain section
│           ├─ All TX IDs
│           ├─ All hashes
│           └─ Chain of custody
│
└─ Compare Panel
   └─ Comparison view
```

## State Management

```
Frontend State (app.js)
│
├─ audits: []                    // All audit history
├─ pendingApprovals: []          // Audits awaiting HITL
├─ selectedForCompare: []        // Selected for comparison
├─ visibleAudits: []             // Filtered audits
└─ 🆕 blockchainStatus: {}       // Blockchain connection info
   ├─ connected: boolean
   ├─ address: string
   ├─ balance: number
   ├─ score_anchors: number
   ├─ hitl_decisions: number
   └─ report_hashes: number

Backend State (blockchain_client.py)
│
└─ CfoEBlockchainClient
   ├─ connected: boolean
   ├─ algod_client: AlgodClient
   ├─ 🆕 score_anchors: []       // In-memory ledger
   ├─ 🆕 hitl_decisions: []      // In-memory ledger
   └─ 🆕 report_hashes: []       // In-memory ledger
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Layer 1: Environment Variables                              │
│  ├─ ALGORAND_PRIVATE_KEY (never exposed to frontend)        │
│  ├─ ALGORAND_ADDRESS (public, safe to display)              │
│  └─ Stored in .env (gitignored)                             │
│                                                               │
│  Layer 2: Transaction Signing                                │
│  ├─ All transactions signed with private key                │
│  ├─ Signature proves identity (non-repudiation)             │
│  └─ Only backend can sign (frontend never sees key)         │
│                                                               │
│  Layer 3: Data Hashing                                       │
│  ├─ Input data hashed before storage (SHA-256)              │
│  ├─ Report hashed before storage (SHA-256)                  │
│  └─ Only hashes on-chain (not raw data)                     │
│                                                               │
│  Layer 4: Blockchain Immutability                            │
│  ├─ Transactions cannot be modified after confirmation      │
│  ├─ Timestamps prove when data was recorded                 │
│  └─ Chain of custody via transaction linking                │
│                                                               │
│  Layer 5: Verification                                       │
│  ├─ Anyone can verify hash matches original                 │
│  ├─ Verification code for quick checks                      │
│  └─ Full transaction history auditable                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Performance Characteristics

```
Operation                    Time        Cost (ALGO)    Notes
─────────────────────────────────────────────────────────────────
Blockchain Connection        ~500ms      0              One-time
Score Anchoring             ~100ms      0.001          Per audit
Report Hash Registration    ~100ms      0.001          Per audit
HITL Decision Recording     ~100ms      0.001          If needed
Status Check                ~50ms       0              Cached
Balance Check               ~50ms       0              Cached

Total per audit:            ~200ms      0.002-0.003    Minimal
```

---

**Legend:**
- 🆕 = New component/feature
- ✓ = Verified/Confirmed
- ⚠️ = Requires attention
- 🚨 = Critical/Important

**Made with 💗 by Team Bankrupts**
