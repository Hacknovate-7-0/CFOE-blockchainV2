# Blockchain UI Integration - CfoE

## Overview

The CfoE web dashboard now includes **full blockchain integration** with the Algorand network, providing immutable audit trails and cryptographic verification for all ESG compliance audits.

## Features

### 🔗 Blockchain Status Panel
- Real-time connection status to Algorand Testnet
- Account balance and address display
- Transaction statistics (Score Anchors, HITL Decisions, Report Hashes)
- On-chain vs local transaction counts

### 📊 Audit Blockchain Verification
Each audit now includes blockchain verification data:
- **Score TX**: Transaction ID for the anchored risk score
- **Data Hash**: SHA-256 hash of input data for integrity verification
- **Verification Code**: Short code for quick report validation
- **Report TX**: Transaction ID for the report hash
- **HITL TX**: Transaction ID for human approval decisions (when applicable)

### 🔐 Three-Point Cryptographic Integration

#### 1. Score Anchoring (After Calculation)
- Immutable timestamp of risk score computation
- SHA-256 hash of input data (emissions, violations)
- Prevents retroactive score manipulation
- Stored on-chain with transaction proof

#### 2. HITL Decision Ledger (After Policy Enforcement)
- Cryptographic proof of human review
- Wallet-signed transaction = proof of identity
- Records approval/rejection with auditor address
- Links back to original score anchor

#### 3. Report Hash Registry (After Report Generation)
- SHA-256 hash of final audit report
- Tamper detection for PDF/DOCX exports
- Verification code for quick validation
- Complete chain of custody

## UI Components

### Blockchain Status Panel
Located below the Portfolio Metrics panel, displays:
- Connection status badge (Connected/Offline)
- Network name (Algorand Testnet)
- Wallet address (truncated)
- Account balance in ALGO
- Transaction counts by type

### Latest Result Blockchain Info
When viewing an audit result, blockchain verification details appear:
- On-Chain/Local status badge
- Score transaction ID
- Input data hash
- Report verification code
- Report transaction ID
- HITL decision transaction ID (if applicable)

### Audit Info Modal
The "Info" button in audit history now includes:
- Full blockchain verification section
- All transaction IDs (clickable/copyable)
- Complete hash values
- Chain of custody visualization

## Workflow Integration

### Audit Submission Flow
```
1. User submits supplier data
   ↓
2. [1/5] Calculate ESG risk scores
   ↓
3. [Blockchain] Anchor score on-chain
   ↓
4. [2/5] Enforce policy rules
   ↓
5. [3/5] Generate AI report
   ↓
6. [4/5] Record report hash on blockchain
   ↓
7. [5/5] Finalize audit results
```

### HITL Approval Flow
```
1. Critical risk audit paused
   ↓
2. Human reviews in Pending Approvals panel
   ↓
3. Approver makes decision (approve/reject)
   ↓
4. [Blockchain] Record HITL decision on-chain
   ↓
5. Audit moved to history with crypto proof
```

## API Endpoints

### New Blockchain Endpoint
```
GET /api/blockchain/status
```
Returns:
- `connected`: Boolean connection status
- `address`: Wallet address (truncated)
- `balance`: Account balance in ALGO
- `network`: Network name
- `score_anchors`: Count of score anchors
- `hitl_decisions`: Count of HITL decisions
- `report_hashes`: Count of report hashes
- `on_chain_count`: Number of on-chain transactions

### Modified Audit Endpoints
All audit responses now include a `blockchain` object:
```json
{
  "audit_id": "AUD-...",
  "supplier_name": "...",
  "risk_score": 0.45,
  "blockchain": {
    "score_tx": "TX_ID or LOCAL_ID",
    "score_hash": "SHA256_HASH",
    "report_tx": "TX_ID or LOCAL_ID",
    "report_hash": "SHA256_HASH",
    "verification_code": "SHORT_CODE",
    "hitl_tx": "TX_ID or LOCAL_ID (if applicable)",
    "on_chain": true/false
  }
}
```

## Testing

### Quick Test
```bash
python test_blockchain_ui.py
```

This will:
1. Test blockchain connection
2. Check account balance
3. Anchor a test score
4. Record a test HITL decision
5. Register a test report hash
6. Display full status report

### Full UI Test
```bash
# Start the webapp
uvicorn webapp:app --reload

# Navigate to
http://127.0.0.1:8000

# Submit a test audit and verify:
# 1. Blockchain status panel shows connection
# 2. Audit logs show blockchain steps
# 3. Latest result shows blockchain verification
# 4. Audit info modal includes blockchain section
```

## Configuration

### Environment Variables
```env
# Required for blockchain integration
ALGORAND_ADDRESS=your_wallet_address
ALGORAND_PRIVATE_KEY=your_private_key

# Optional (defaults to Algorand Testnet)
ALGOD_SERVER=https://testnet-api.algonode.cloud
ALGOD_TOKEN=
```

### Offline Mode
If blockchain connection fails:
- UI continues to work normally
- Transactions logged locally with LOCAL_ID
- Status panel shows "Offline" badge
- All features remain functional

## Security Notes

### Private Key Handling
- Never commit `.env` file to version control
- Private key required for transaction signing
- Use testnet for development/testing
- Rotate keys regularly

### Transaction Costs
- Each on-chain transaction costs ~0.001 ALGO
- Minimum balance requirement: ~0.1 ALGO
- Monitor balance in status panel
- Testnet ALGO is free (use faucet)

### Data Privacy
- Only hashes stored on-chain (not raw data)
- Supplier names visible on-chain
- Report content NOT stored on-chain
- Use data anonymization if required

## Troubleshooting

### "Blockchain connection failed"
- Check `ALGORAND_ADDRESS` in `.env`
- Verify network connectivity
- Confirm Algorand node is accessible
- Check account has sufficient balance

### "Transaction failed"
- Ensure account has ALGO balance
- Verify private key is correct
- Check network status
- Review transaction size (max 1KB note)

### "Local mode only"
- Install `py-algorand-sdk`: `pip install py-algorand-sdk`
- Verify `.env` configuration
- Check firewall/proxy settings
- Confirm testnet node availability

## Benefits

### For Auditors
- Immutable audit trail
- Cryptographic proof of reviews
- Tamper-evident reports
- Regulatory compliance

### For Regulators
- Verify audit authenticity
- Check report integrity
- Validate human approvals
- Audit the auditors

### For Suppliers
- Transparent scoring process
- Verifiable audit results
- Dispute resolution support
- Trust through transparency

## Future Enhancements

- [ ] Smart contract deployment UI
- [ ] Multi-signature approvals
- [ ] Audit history explorer with blockchain links
- [ ] Report verification tool (upload PDF, check hash)
- [ ] Mainnet support toggle
- [ ] Transaction cost estimator
- [ ] Batch transaction optimization

## Support

For blockchain-specific issues:
- Check Algorand documentation: https://developer.algorand.org
- Review blockchain_client.py implementation
- Test with test_blockchain_ui.py
- Verify .env configuration

For UI issues:
- Check browser console for errors
- Verify API endpoints with `/docs`
- Review webapp.py logs
- Test WebSocket connection
