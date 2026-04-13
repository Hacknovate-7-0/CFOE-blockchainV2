# Carbon Credit Token System - How It Works

## Token Economics: 1 Token = 10 Carbon Credits

### Overview

The CfoE Carbon Credit Token (CCT) system uses a **10:1 conversion rate**:
- **1 CCT Token = 10 Carbon Credits (tons CO2eq)**
- This makes tokens more valuable and easier to manage
- Fractional tokens supported with 1 decimal place (0.1 CCT = 1 ton CO2eq)

---

## Why 10:1 Ratio?

### Benefits

1. **Higher Token Value**
   - Each token represents significant emission reduction (10 tons)
   - More prestigious to hold/trade tokens
   - Reduces transaction count for large volumes

2. **Easier Management**
   - Smaller numbers to track (500 tokens vs 5000 credits)
   - Cleaner UI display
   - Simpler accounting

3. **Fractional Precision**
   - 1 decimal place allows 0.1 CCT = 1 ton CO2eq
   - Precise credit allocation without excessive decimals
   - Example: 2,500 tons = 250.0 CCT

4. **Industry Standard**
   - Many carbon markets use bundled credits
   - Aligns with traditional carbon offset packages
   - Professional presentation

---

## How It Works

### 1. Token Creation

```python
# Create token with 10M carbon credits
tm.create_carbon_credit_token(
    total_credits=10_000_000,  # 10 million tons CO2eq
    decimals=1,                 # 1 decimal place
    unit_name="CCT",
    asset_name="CfoE Carbon Credit"
)

# Result:
# - Total Tokens: 1,000,000 CCT
# - Total Credits: 10,000,000 tons CO2eq
# - Rate: 1 CCT = 10 tons CO2eq
```

**Calculation:**
```
Total Tokens = Total Credits / 10
1,000,000 CCT = 10,000,000 / 10
```

---

### 2. Credit Issuance

When a supplier reduces emissions, they receive tokens:

```python
# Supplier reduces 5000 tons CO2eq
tm.issue_credits(
    recipient_address="ALGO_ADDRESS",
    carbon_credits=5000,  # Input in tons CO2eq
    reason="Q1 2024 emission reduction",
    audit_id="AUD-12345"
)

# Result:
# - Carbon Credits: 5,000 tons CO2eq
# - Tokens Issued: 500.0 CCT
# - Rate: 1 CCT = 10 tons
```

**Calculation:**
```
Tokens Issued = Carbon Credits / 10
500 CCT = 5000 / 10
```

**Example Scenarios:**

| Carbon Credits (tons) | Tokens Issued (CCT) | Description |
|-----------------------|---------------------|-------------|
| 10 | 1.0 | Minimum issuance |
| 100 | 10.0 | Small reduction |
| 1,000 | 100.0 | Medium reduction |
| 5,000 | 500.0 | Large reduction |
| 10,000 | 1,000.0 | Major reduction |
| 50,000 | 5,000.0 | Enterprise reduction |

---

### 3. Credit Retirement (Burn)

When credits are used to offset emissions:

```python
# Company offsets 1000 tons CO2eq
tm.retire_credits(
    carbon_credits=1000,  # Input in tons CO2eq
    reason="2024 Q1 carbon offset",
    beneficiary="GreenCorp Manufacturing"
)

# Result:
# - Carbon Credits: 1,000 tons CO2eq
# - Tokens Retired: 100.0 CCT
# - Status: PERMANENTLY RETIRED
```

**Calculation:**
```
Tokens Retired = Carbon Credits / 10
100 CCT = 1000 / 10
```

---

### 4. Balance Queries

Check token and credit balance:

```python
balance = tm.get_credit_balance("ALGO_ADDRESS")

# Returns:
{
    "tokens": 500.0,           # CCT tokens
    "carbon_credits": 5000.0   # Equivalent tons CO2eq
}
```

**Calculation:**
```
Carbon Credits = Tokens × 10
5000 = 500 × 10
```

---

## Complete Example Workflow

### Scenario: Supplier Emission Reduction Program

**Step 1: Create Token Pool**
```python
# Create 10M credit pool (1M tokens)
asset_id = tm.create_carbon_credit_token(
    total_credits=10_000_000
)
# Result: 1,000,000 CCT tokens created
```

**Step 2: Supplier Reduces Emissions**
```
Supplier: GreenCorp Manufacturing
Baseline Emissions: 10,000 tons CO2eq/year
Actual Emissions: 5,000 tons CO2eq/year
Reduction: 5,000 tons CO2eq
```

**Step 3: Issue Credits**
```python
tm.issue_credits(
    recipient_address=greencorp_address,
    carbon_credits=5000,
    reason="Annual emission reduction verified",
    audit_id="AUD-2024-001"
)
# GreenCorp receives: 500.0 CCT tokens
```

**Step 4: GreenCorp Trades Tokens**
```
GreenCorp sells 200 CCT to BlueCorp
= 2,000 tons CO2eq worth of credits
```

**Step 5: BlueCorp Retires Credits**
```python
tm.retire_credits(
    carbon_credits=2000,
    reason="Q1 2024 operational offset",
    beneficiary="BlueCorp Industries"
)
# 200.0 CCT permanently retired
```

**Final Balances:**
- GreenCorp: 300 CCT (3,000 tons CO2eq)
- BlueCorp: 0 CCT (retired 2,000 tons)
- Circulating: 300 CCT (3,000 tons)
- Retired: 200 CCT (2,000 tons)

---

## Technical Implementation

### Token Configuration

```python
AssetConfigTxn(
    total=1_000_000 * 10,  # 1M tokens × 10 (1 decimal)
    decimals=1,             # Allows 0.1 precision
    unit_name="CCT",
    asset_name="CfoE Carbon Credit"
)
```

### Conversion Functions

```python
# Credits to Tokens
def credits_to_tokens(carbon_credits: float) -> float:
    return carbon_credits / 10

# Tokens to Credits
def tokens_to_credits(tokens: float) -> float:
    return tokens * 10

# To blockchain micro-units (1 decimal)
def to_micro(tokens: float) -> int:
    return int(tokens * 10)
```

### Example Conversions

| Carbon Credits | Tokens | Micro-units |
|----------------|--------|-------------|
| 1 ton | 0.1 CCT | 1 |
| 10 tons | 1.0 CCT | 10 |
| 100 tons | 10.0 CCT | 100 |
| 1,000 tons | 100.0 CCT | 1,000 |
| 10,000 tons | 1,000.0 CCT | 10,000 |

---

## API Usage

### Create Token
```bash
POST /api/tokens/create
{
  "total_credits": 10000000,  # 10M tons CO2eq
  "unit_name": "CCT",
  "asset_name": "CfoE Carbon Credit"
}
# Creates 1M CCT tokens
```

### Issue Credits
```bash
POST /api/tokens/issue
{
  "recipient_address": "ALGO_ADDRESS",
  "amount": 5000,  # 5000 tons CO2eq
  "reason": "Q1 2024 reduction",
  "audit_id": "AUD-12345"
}
# Issues 500 CCT tokens
```

### Retire Credits
```bash
POST /api/tokens/retire
{
  "amount": 1000,  # 1000 tons CO2eq
  "reason": "Q1 offset",
  "beneficiary": "GreenCorp"
}
# Retires 100 CCT tokens
```

### Check Balance
```bash
GET /api/tokens/balance/ALGO_ADDRESS

Response:
{
  "address": "ALGO_ADDRESS",
  "balance": {
    "tokens": 500.0,
    "carbon_credits": 5000.0
  },
  "asset_id": 123456
}
```

---

## Benefits Summary

### For Suppliers
✅ Receive valuable tokens for emission reductions  
✅ Trade tokens on carbon markets  
✅ Hold tokens as environmental assets  
✅ Transparent on-chain verification  

### For Buyers
✅ Purchase bundled credits (10 tons per token)  
✅ Retire credits for compliance  
✅ Verify authenticity on blockchain  
✅ Track offset history  

### For Regulators
✅ Audit trail for all credit movements  
✅ Prevent double-counting via retirement  
✅ Verify emission reduction claims  
✅ Monitor market activity  

---

## Testing

```bash
# Run complete test
python test_carbon_tokens.py

# Expected output:
# - Token created: 1M CCT (10M credits)
# - Issued: 500 CCT (5000 credits)
# - Retired: 100 CCT (1000 credits)
# - Balance: 400 CCT (4000 credits)
```

---

## Summary

**Token Economics:**
- 1 CCT Token = 10 Carbon Credits (tons CO2eq)
- 1 decimal place precision (0.1 CCT = 1 ton)
- Total supply: 1M tokens = 10M credits

**Key Operations:**
- Issue: `carbon_credits / 10 = tokens`
- Retire: `carbon_credits / 10 = tokens`
- Balance: `tokens × 10 = carbon_credits`

**Benefits:**
- Higher token value
- Easier management
- Industry alignment
- Professional presentation
