# Blockchain UI Integration - Verification Checklist

Use this checklist to verify that the blockchain integration is working correctly in your CfoE dashboard.

## Pre-Flight Checks

### Environment Setup
- [ ] `.env` file exists in project root
- [ ] `ALGORAND_ADDRESS` is set in `.env`
- [ ] `ALGORAND_PRIVATE_KEY` is set in `.env` (optional for read-only)
- [ ] `py-algorand-sdk` is installed (`pip list | grep algorand`)
- [ ] Account has balance > 0.1 ALGO (check at https://testnet.algoexplorer.io)

### Dependencies
```bash
# Run this to verify dependencies
pip install -r requirements.txt
python -c "from algosdk.v2client import algod; print('✓ algosdk installed')"
```

## Quick Test (5 minutes)

### Step 1: Run Test Script
```bash
python test_blockchain_ui.py
```

**Expected Output:**
```
==============================================================
  BLOCKCHAIN UI INTEGRATION TEST
==============================================================

[TEST 1] Connection Status
  Connected: True
  Address: 4KG534Q6BUNUN...

[TEST 2] Balance Check
  Balance: 1.234567 ALGO
  Status: OK

[TEST 3] Score Anchoring
  [Blockchain] SCORE ANCHORED on-chain
  ...

[TEST 4] HITL Decision Recording
  [Blockchain] HITL DECISION recorded on-chain
  ...

[TEST 5] Report Hash Registration
  [Blockchain] REPORT HASH registered on-chain
  ...

[TEST 6] Full Status Report
  ==============================================================
  BLOCKCHAIN STATUS
  ==============================================================
  ...
```

**Checklist:**
- [ ] Connection status shows "ACTIVE" or "OFFLINE"
- [ ] Balance shows > 0 ALGO (if connected)
- [ ] Score anchor transaction created
- [ ] HITL decision transaction created
- [ ] Report hash transaction created
- [ ] Status report displays correctly

### Step 2: Start Web Application
```bash
uvicorn webapp:app --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Checklist:**
- [ ] Server starts without errors
- [ ] No import errors in console
- [ ] Port 8000 is accessible

## UI Verification (10 minutes)

### Step 3: Open Dashboard
Navigate to: http://127.0.0.1:8000

**Checklist:**
- [ ] Page loads successfully
- [ ] No JavaScript errors in browser console (F12)
- [ ] All panels render correctly

### Step 4: Verify Blockchain Status Panel

**Location:** Below "Portfolio Metrics" panel

**Checklist:**
- [ ] Panel titled "⛓️ Blockchain Status" is visible
- [ ] Connection status badge shows "Connected" (green) or "Offline" (yellow)
- [ ] Network shows "Algorand Testnet"
- [ ] Address shows truncated wallet address
- [ ] Balance shows ALGO amount
- [ ] Transaction counts display (Score Anchors, HITL Decisions, Report Hashes)

**Screenshot Verification:**
```
┌─────────────────────────────────────┐
│ ⛓️ Blockchain Status                │
├─────────────────────────────────────┤
│ Status:        [Connected]          │
│ Network:       Algorand Testnet     │
│ Address:       4KG534Q6...          │
│ Balance:       1.234567 ALGO        │
│ Score Anchors: 0 (0 on-chain)       │
│ HITL Decisions: 0                   │
│ Report Hashes:  0                   │
└─────────────────────────────────────┘
```

### Step 5: Submit Test Audit

**Test Data:**
- Supplier Name: `TestCorp Blockchain`
- Emissions: `2500`
- Violations: `2`
- Notes: `Testing blockchain integration`

**Checklist:**
- [ ] Click "Run Audit" button
- [ ] Log panel appears showing progress
- [ ] Step [1/5] shows "Calculating ESG risk scores..."
- [ ] Blockchain log shows "✓ Score anchored on blockchain: ..."
- [ ] Step [2/5] shows "Enforcing policy rules..."
- [ ] Step [3/5] shows "Generating AI report..."
- [ ] Step [4/5] shows "Recording report hash on blockchain..."
- [ ] Blockchain log shows "✓ Report hash: ..."
- [ ] Step [5/5] shows "Finalizing audit results..."
- [ ] Status shows "Audit complete for TestCorp Blockchain"

**Expected Log Output:**
```
Starting audit for TestCorp Blockchain...
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
✓ Audit complete for TestCorp Blockchain
```

### Step 6: Verify Latest Result Blockchain Info

**Location:** "Latest Result" panel, below audit details

**Checklist:**
- [ ] Blockchain verification section appears
- [ ] Section titled "⛓️ Blockchain Verification"
- [ ] Status badge shows "On-Chain" (green) or "Local" (yellow)
- [ ] Score TX displays (e.g., "SCORE-0001" or "TX_ABC123...")
- [ ] Data Hash displays (truncated SHA-256)
- [ ] Verification Code displays (12-character hex)
- [ ] Report TX displays
- [ ] No HITL TX (since this is moderate risk)

**Screenshot Verification:**
```
┌─────────────────────────────────────┐
│ ⛓️ Blockchain Verification          │
├─────────────────────────────────────┤
│ Status:        [On-Chain]           │
│ Score TX:      SCORE-0001           │
│ Data Hash:     a3f2b8c9d1e4...      │
│ Verify Code:   A3F2B8C9D1E4         │
│ Report TX:     REPORT-0001          │
└─────────────────────────────────────┘
```

### Step 7: Verify Blockchain Status Updated

**Checklist:**
- [ ] Blockchain Status panel shows updated counts
- [ ] Score Anchors increased by 1
- [ ] Report Hashes increased by 1
- [ ] On-chain count increased (if connected)

### Step 8: Verify Audit Info Modal

**Steps:**
1. Click "Info" button in audit history table
2. Scroll down in the modal

**Checklist:**
- [ ] Modal opens successfully
- [ ] Blockchain section appears (after horizontal line)
- [ ] Section titled "⛓️ Blockchain Verification"
- [ ] Status shows "On-Chain" or "Local Only"
- [ ] Score TX displayed in `<code>` tags
- [ ] Data Hash displayed (truncated)
- [ ] Verification Code displayed (highlighted)
- [ ] Report TX displayed
- [ ] Report Hash displayed (truncated)

### Step 9: Test Critical Risk Audit (HITL)

**Test Data:**
- Supplier Name: `DangerCorp Critical`
- Emissions: `15000`
- Violations: `25`
- Notes: `Testing HITL blockchain integration`

**Checklist:**
- [ ] Submit audit
- [ ] Risk score shows ≥ 0.70 (Critical Risk)
- [ ] Log shows "🚨 CRITICAL RISK - Audit paused for human approval"
- [ ] Audit appears in "Pending Approvals" panel
- [ ] Blockchain status shows score anchor recorded
- [ ] No report hash yet (audit paused)

### Step 10: Test HITL Approval with Blockchain

**Steps:**
1. Click "Review & Decide" in Pending Approvals
2. Enter your name
3. Enter approval notes
4. Click "Approve"

**Checklist:**
- [ ] Approval dialog opens
- [ ] Audit details display
- [ ] Name and notes fields work
- [ ] "Approve" button submits successfully
- [ ] Status shows "Audit approved successfully by [name]"
- [ ] Audit moves to history
- [ ] Blockchain info now includes HITL TX
- [ ] HITL Decisions count increased in status panel

### Step 11: Verify Complete Blockchain Trail

**Steps:**
1. Find the approved critical audit in history
2. Click "Info" button
3. Check blockchain section

**Checklist:**
- [ ] Score TX present
- [ ] Report TX present
- [ ] HITL TX present (this is the key difference!)
- [ ] All three transactions form chain of custody
- [ ] Verification code present

**Expected Chain:**
```
1. Score:  SCORE-0002 or TX_ABC...
2. HITL:   HITL-0001 or TX_DEF...
3. Report: REPORT-0002 or TX_GHI...
```

## Advanced Verification (Optional)

### Step 12: Verify Transaction on Algorand Explorer

**If connected to blockchain:**

1. Copy a transaction ID from the UI (e.g., `TX_ABC123...`)
2. Visit: https://testnet.algoexplorer.io
3. Paste transaction ID in search
4. Verify transaction details

**Checklist:**
- [ ] Transaction found on explorer
- [ ] Sender matches your wallet address
- [ ] Note field contains JSON data
- [ ] Type shows "CfoE_SCORE_ANCHOR" or similar
- [ ] Transaction confirmed

### Step 13: Verify Report Hash Integrity

**Steps:**
1. Get verification code from audit (e.g., `A3F2B8C9D1E4`)
2. Download PDF report
3. Compute SHA-256 hash of report
4. Compare first 12 characters with verification code

**Checklist:**
- [ ] Verification code matches report hash
- [ ] Report integrity confirmed

### Step 14: Test Offline Mode

**Steps:**
1. Stop the webapp
2. Rename `.env` to `.env.backup`
3. Start webapp again
4. Submit audit

**Checklist:**
- [ ] Blockchain status shows "Offline"
- [ ] Audit still completes successfully
- [ ] Transaction IDs show "LOCAL-XXXX" format
- [ ] All features work normally
- [ ] No errors in console

**Restore:**
```bash
# Stop webapp
# Rename .env.backup back to .env
# Restart webapp
```

## Performance Verification

### Step 15: Check Performance Impact

**Checklist:**
- [ ] Audit completes in < 5 seconds (with AI)
- [ ] Blockchain overhead < 500ms per audit
- [ ] Page load time < 2 seconds
- [ ] No UI lag or freezing
- [ ] WebSocket logs update in real-time

## Browser Compatibility

### Step 16: Test in Multiple Browsers

**Checklist:**
- [ ] Chrome/Edge: All features work
- [ ] Firefox: All features work
- [ ] Safari: All features work (if available)
- [ ] Mobile browser: Responsive layout works

## Final Verification

### Step 17: Complete System Check

**Checklist:**
- [ ] All UI panels render correctly
- [ ] Blockchain status panel shows accurate data
- [ ] Audits record blockchain info
- [ ] HITL approvals record on blockchain
- [ ] Info modal shows blockchain section
- [ ] Transaction counts update correctly
- [ ] Offline mode works gracefully
- [ ] No console errors
- [ ] No backend errors in logs
- [ ] Documentation is clear and helpful

## Troubleshooting

### Common Issues

#### Issue: "Blockchain status shows Offline"
**Solutions:**
- [ ] Check `.env` has `ALGORAND_ADDRESS`
- [ ] Verify `py-algorand-sdk` is installed
- [ ] Check network connectivity
- [ ] Verify Algorand node is accessible

#### Issue: "Transaction IDs show LOCAL-XXXX"
**Solutions:**
- [ ] Check blockchain connection status
- [ ] Verify account has ALGO balance
- [ ] Check private key is correct
- [ ] Review backend logs for errors

#### Issue: "Blockchain section not appearing"
**Solutions:**
- [ ] Hard refresh browser (Ctrl+F5)
- [ ] Clear browser cache
- [ ] Check browser console for errors
- [ ] Verify API response includes blockchain data

#### Issue: "Balance shows 0 ALGO"
**Solutions:**
- [ ] Visit https://bank.testnet.algorand.network
- [ ] Request testnet ALGO (free)
- [ ] Wait for transaction to confirm
- [ ] Refresh dashboard

## Success Criteria

### Minimum Requirements (Must Pass)
- [x] Blockchain status panel displays
- [x] Audits complete successfully
- [x] Blockchain info appears in results
- [x] No breaking errors

### Full Integration (Should Pass)
- [x] On-chain transactions recorded
- [x] HITL decisions recorded on blockchain
- [x] Verification codes generated
- [x] Chain of custody complete

### Production Ready (Nice to Have)
- [x] Performance < 500ms overhead
- [x] Offline mode works
- [x] All browsers supported
- [x] Documentation complete

## Sign-Off

**Tested By:** _________________

**Date:** _________________

**Environment:**
- [ ] Local Development
- [ ] Staging
- [ ] Production

**Blockchain Network:**
- [ ] Algorand Testnet
- [ ] Algorand Mainnet

**Status:**
- [ ] ✅ All checks passed - Ready for use
- [ ] ⚠️ Some issues found - See notes below
- [ ] ❌ Major issues - Requires fixes

**Notes:**
```
[Add any observations, issues, or recommendations here]
```

---

**Verification Complete!** 🎉

If all checks passed, your blockchain UI integration is working correctly and ready for production use.

**Next Steps:**
1. Review documentation in `BLOCKCHAIN_UI_INTEGRATION.md`
2. Share verification code with stakeholders
3. Train users on blockchain features
4. Monitor transaction costs and performance

**Made with 💗 by Team Bankrupts**
