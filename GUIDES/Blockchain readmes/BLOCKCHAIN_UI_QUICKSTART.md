# Blockchain UI - Quick Reference

## What's New? 🎉

The CfoE dashboard now records every audit on the Algorand blockchain for **immutable compliance tracking**.

## Visual Guide

### 1. Blockchain Status Panel
```
┌─────────────────────────────────────────┐
│ ⛓️ Blockchain Status                    │
├─────────────────────────────────────────┤
│ Status:        [Connected]              │
│ Network:       Algorand Testnet         │
│ Address:       4KG534Q6BUNUN...         │
│ Balance:       1.234567 ALGO            │
│ Score Anchors: 15 (12 on-chain)         │
│ HITL Decisions: 3                       │
│ Report Hashes:  15                      │
└─────────────────────────────────────────┘
```

### 2. Latest Result with Blockchain Info
```
┌─────────────────────────────────────────┐
│ Latest Result                           │
├─────────────────────────────────────────┤
│ [Moderate Risk] [Score 0.45] [Completed]│
│ TestSupplier Corp | Emissions 2500 | ...│
│ Decision: Continue with monitoring      │
│ ...                                     │
├─────────────────────────────────────────┤
│ ⛓️ Blockchain Verification              │
├─────────────────────────────────────────┤
│ Status:        [On-Chain]               │
│ Score TX:      SCORE-0001               │
│ Data Hash:     a3f2b8c9d1e4...          │
│ Verify Code:   A3F2B8C9D1E4             │
│ Report TX:     REPORT-0001              │
└─────────────────────────────────────────┘
```

### 3. Audit Progress Logs
```
Starting audit for TestSupplier Corp...
[1/5] Calculating ESG risk scores...
✓ Risk Score: 0.45 (Moderate Risk)
✓ Score anchored on blockchain: SCORE-0001...
[2/5] Enforcing policy rules...
✓ Policy Decision: Continue with monitoring
[3/5] Generating AI report...
✓ AI report generated successfully
[4/5] Recording report hash on blockchain...
✓ Report hash: A3F2B8C9D1E4
[5/5] Finalizing audit results...
✓ Audit complete for TestSupplier Corp
```

## Key Features

### 🔒 Immutable Audit Trail
Every audit is recorded on the blockchain with:
- Risk score + timestamp
- Input data hash (emissions, violations)
- Report hash (tamper detection)
- Human approval proof (for critical risks)

### ✅ Cryptographic Verification
Three verification points:
1. **Score Anchor** - Proves score wasn't changed
2. **HITL Decision** - Proves human reviewed it
3. **Report Hash** - Proves report wasn't altered

### 🌐 Transparent & Auditable
- Regulators can verify any audit
- Suppliers can validate their scores
- Auditors have cryptographic proof
- Complete chain of custody

## How It Works

### Normal Audit (Low/Moderate Risk)
```
Submit → Calculate → [Blockchain: Anchor Score] → 
Policy → Report → [Blockchain: Hash Report] → Complete
```

### Critical Risk Audit (HITL Required)
```
Submit → Calculate → [Blockchain: Anchor Score] → 
Policy → PAUSE → Human Review → Approve/Reject → 
[Blockchain: Record Decision] → Report → 
[Blockchain: Hash Report] → Complete
```

## Verification Codes

Each audit gets a **Verification Code** (12-character hex):
```
A3F2B8C9D1E4
```

Use this to:
- Quickly validate a report
- Share with stakeholders
- Reference in disputes
- Prove authenticity

## Transaction IDs

Three types of blockchain transactions:
1. **Score TX** - `SCORE-0001` or `TX_ABC123...`
2. **Report TX** - `REPORT-0001` or `TX_DEF456...`
3. **HITL TX** - `HITL-0001` or `TX_GHI789...`

Format:
- `SCORE-XXXX` = Local only (offline mode)
- `TX_XXXXXX...` = On-chain (Algorand transaction)

## Status Badges

### Connection Status
- 🟢 **Connected** - On-chain recording active
- 🟡 **Offline** - Local logging only

### Audit Status
- 🟢 **Completed** - Audit finished
- 🟡 **Pending Approval** - Awaiting HITL review
- 🔴 **Rejected** - HITL rejected

### Risk Classification
- 🟢 **Low Risk** - Score < 0.40
- 🟡 **Moderate Risk** - Score 0.40-0.69
- 🔴 **Critical Risk** - Score ≥ 0.70

## Quick Actions

### View Blockchain Info
1. Run an audit
2. Check "Latest Result" panel
3. See blockchain verification section

### Inspect Full Details
1. Click "Info" button in history
2. Scroll to blockchain section
3. Copy transaction IDs

### Check Connection Status
1. Look at "Blockchain Status" panel
2. Verify "Connected" badge
3. Check balance > 0.1 ALGO

### Verify Report Integrity
1. Get verification code from audit
2. Compare with report hash
3. Confirm match = authentic

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Status shows "Offline" | Check `.env` has `ALGORAND_ADDRESS` |
| Balance is 0 | Get testnet ALGO from faucet |
| TX shows "LOCAL-XXXX" | Connection failed, logged locally |
| No blockchain section | Old audit (before integration) |

## Testing

### Quick Test
```bash
python test_blockchain_ui.py
```

### Full Test
```bash
uvicorn webapp:app --reload
# Open http://127.0.0.1:8000
# Submit audit with:
# - Supplier: TestCorp
# - Emissions: 2500
# - Violations: 2
# Check blockchain info appears
```

## Benefits Summary

| Stakeholder | Benefit |
|-------------|---------|
| **Auditors** | Cryptographic proof of work |
| **Regulators** | Verify audit authenticity |
| **Suppliers** | Transparent scoring process |
| **Management** | Immutable compliance records |

## Cost

- **Per Audit**: ~0.003 ALGO (~$0.0003 USD)
- **Minimum Balance**: 0.1 ALGO (~$0.01 USD)
- **Testnet**: FREE (use faucet)

## Next Steps

1. ✅ Test with `test_blockchain_ui.py`
2. ✅ Start webapp: `uvicorn webapp:app --reload`
3. ✅ Submit test audit
4. ✅ Verify blockchain info appears
5. ✅ Check status panel shows connection
6. ✅ Review audit info modal

---

**Made with 💗 by Team Bankrupts**
