# 🚀 Quick Start Guide - Testing CfoE with Sample Data

## 📋 Overview

This guide helps you quickly test all 5 Gazette requirements using the provided sample data.

---

## ⚡ 3-Minute Quick Start

### Step 1: Start the Server
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Start server
uvicorn webapp:app --reload
```

### Step 2: Open Browser
Navigate to: **http://127.0.0.1:8000**

### Step 3: Test with Sample Data

#### Option A: Manual Testing (Copy-Paste)
Open `SAMPLE_TEST_DATA.md` and copy any scenario into the form.

**Quick Example - Low Risk:**
```
Supplier Name: GreenTech Manufacturing
Sector: default
Emissions: 2500
Violations: 0
Production Volume: 500
Production Unit: tonne
Registry ID: (leave empty)
Notes: Excellent compliance
```

#### Option B: Automated Testing (Script)
```bash
python submit_test_data.py
# Choose option 1 for quick test
```

---

## 🎯 Testing Each Gazette Requirement

### 1️⃣ Sector-Specific Targets

**Test:** Submit audits with different sectors

```
Aluminium:
  Supplier: European Aluminium Corp
  Sector: aluminium
  Emissions: 9500
  Violations: 1
  Production Volume: 1000
  Production Unit: tonne
  Registry ID: ALMOE003EU

Refinery:
  Supplier: Midwest Petroleum Refinery
  Sector: refinery
  Emissions: 28000
  Violations: 5
  Production Volume: 1000
  Production Unit: MBBLS
  Registry ID: REFOE001MP
```

**Verify:**
- ✅ Different risk thresholds per sector
- ✅ Sector name displayed in results
- ✅ Classification changes based on sector

---

### 2️⃣ Normalized Metrics

**Test:** Submit with production volume

```
With Volume:
  Supplier: Pacific Basin Textiles
  Sector: textiles
  Emissions: 6500
  Violations: 2
  Production Volume: 1000
  Production Unit: tonne
  Registry ID: TXTOE007PB

Without Volume:
  Supplier: Alpine Aluminium Works
  Sector: aluminium
  Emissions: 3500
  Violations: 1
  Production Volume: (leave empty)
```

**Verify:**
- ✅ Emissions intensity calculated (tCO2eq/unit)
- ✅ Fallback to absolute scoring when no volume
- ✅ Different units supported (tonne, MBBLS, NRGF)

---

### 3️⃣ Multi-Year Trajectory

**Test:** Submit 3 audits for same supplier

```
Audit 1:
  Supplier: TrajectoryTest Corp
  Emissions: 5000
  Violations: 4
  Production Volume: 1000

Audit 2:
  Supplier: TrajectoryTest Corp
  Emissions: 4500
  Violations: 3
  Production Volume: 1000

Audit 3:
  Supplier: TrajectoryTest Corp
  Emissions: 4000
  Violations: 2
  Production Volume: 1000
```

**Verify:**
- ✅ Trajectory panel appears after 2+ audits
- ✅ Trend indicator (📈 Improving)
- ✅ On-track status (✅ On Track)
- ✅ Recent audit history displayed

---

### 4️⃣ Entity Registry Lookup

**Test:** Enter valid and invalid registry IDs

```
Valid:
  Registry ID: REFOE001MP
  (Should show: ✓ Valid: Midwest Petroleum Refinery)

Invalid:
  Registry ID: INVALID123
  (Should show: ✗ Registry ID not found)
```

**Valid Registry IDs:**
- REFOE001MP - Midwest Petroleum Refinery (refinery)
- TXTOE007PB - Pacific Basin Textiles (textiles)
- ALMOE003EU - European Aluminium Corp (aluminium)
- PETOE009AS - Asia Petrochemicals Ltd (petrochemicals)

**Verify:**
- ✅ Real-time validation on blur
- ✅ Green checkmark for valid IDs
- ✅ Red X with error for invalid IDs
- ✅ Optional field (can be empty)

---

### 5️⃣ Pro-Rata Calculation

**Test:** Any audit automatically calculates pro-rata

```
Any Supplier:
  Emissions: 4000
  Production Volume: 1000
  (Pro-rata calculated automatically based on current date)
```

**Verify:**
- ✅ Pro-rata progress % displayed
- ✅ Expected intensity adjusted for current date
- ✅ Progress from baseline (2023) to target (2027)

---

## 🧪 Automated Testing

### Quick Test (3 scenarios)
```bash
python submit_test_data.py
# Choose option 1
```

Tests:
- ✅ Low Risk scenario
- ✅ Moderate Risk scenario
- ✅ Critical Risk scenario (HITL)

### Full Test (10 scenarios)
```bash
python submit_test_data.py
# Choose option 2
```

Tests all features:
- ✅ All 5 sectors
- ✅ With/without production volume
- ✅ Valid/invalid registry IDs
- ✅ Different risk levels
- ✅ HITL workflow

### Trajectory Test
```bash
python submit_test_data.py
# Choose option 3
```

Submits 3 audits for same supplier to demonstrate trajectory.

---

## 📊 Expected Results

### Low Risk Audit
```
Risk Score: 0.15-0.30
Classification: Low Risk
Policy Decision: APPROVE
HITL Required: No
```

### Moderate Risk Audit
```
Risk Score: 0.40-0.65
Classification: Moderate Risk
Policy Decision: REVIEW
HITL Required: No
```

### Critical Risk Audit
```
Risk Score: 0.70-1.00
Classification: Critical Risk
Policy Decision: ESCALATE
HITL Required: Yes
Status: Pending Approval
```

---

## 🔍 What to Check

### In Latest Result Panel
- ✅ Risk score and classification
- ✅ Sector name
- ✅ Emissions intensity (if volume provided)
- ✅ Pro-rata progress percentage
- ✅ Registry validation status
- ✅ Trajectory panel (if multiple audits)
- ✅ Policy decision
- ✅ Blockchain verification info

### In Blockchain Status Panel
- ✅ Connection status
- ✅ Wallet address and balance
- ✅ Transaction counts
- ✅ On-chain vs local ratio

### In Audit History
- ✅ All audits listed
- ✅ Filter by risk level
- ✅ Search by supplier name
- ✅ Click row to view details
- ✅ Info button for full details

---

## 🚨 Troubleshooting

### Server Not Running
```
Error: Connection refused
Fix: uvicorn webapp:app --reload
```

### Registry Validation Not Working
```
Issue: No validation message
Fix: Click outside the field (onblur event)
```

### Trajectory Not Showing
```
Issue: No trajectory panel
Fix: Submit 2+ audits for same supplier name (exact match)
```

### Blockchain Offline
```
Issue: Blockchain status shows "Offline"
Fix: Add ALGORAND_ADDRESS and ALGORAND_PRIVATE_KEY to .env
Note: System works fine in offline mode
```

---

## 📝 Testing Checklist

### Basic Functionality
- [ ] Server starts successfully
- [ ] UI loads at http://127.0.0.1:8000
- [ ] Form accepts input
- [ ] Audit submits successfully
- [ ] Results display correctly

### Gazette Requirements
- [ ] Sector dropdown works (5 options)
- [ ] Production volume calculates intensity
- [ ] Registry ID validates in real-time
- [ ] Trajectory shows after 2+ audits
- [ ] Pro-rata progress displays

### Risk Levels
- [ ] Low risk audit (score < 0.40)
- [ ] Moderate risk audit (0.40-0.69)
- [ ] Critical risk audit (≥ 0.70)
- [ ] HITL workflow triggers

### Blockchain
- [ ] Blockchain status panel shows
- [ ] Score anchor recorded
- [ ] Report hash generated
- [ ] Verification code displayed
- [ ] HITL decision recorded (if applicable)

---

## 🎓 Learning Path

### Beginner (5 minutes)
1. Start server
2. Submit one low risk audit
3. View results

### Intermediate (15 minutes)
1. Test all 5 sectors
2. Test with/without production volume
3. Test valid registry ID
4. View blockchain info

### Advanced (30 minutes)
1. Run automated test suite
2. Submit trajectory test (3 audits)
3. Test HITL workflow
4. Compare multiple audits
5. Download reports (PDF/DOCX)

---

## 📚 Additional Resources

- **SAMPLE_TEST_DATA.md** - All test scenarios with details
- **sample_test_data.json** - JSON format test data
- **CRITICAL_GAPS_IMPLEMENTATION.md** - Complete implementation guide
- **QUICK_REFERENCE.md** - Fast lookup for all features
- **ALL_GAPS_COMPLETE_SUMMARY.md** - Executive summary

---

## 💡 Pro Tips

1. **Use Registry IDs:** Test with valid IDs to see full feature set
2. **Test Trajectory:** Submit 3+ audits for same supplier to see trends
3. **Try HITL:** Submit critical risk audit to see approval workflow
4. **Compare Audits:** Select 2 history rows to see side-by-side comparison
5. **Download Reports:** Use Info button → Download Files for exports

---

**Made with 💗 by Team Bankrupts**

**Status:** ✅ Ready for Testing  
**Version:** 1.0.0  
**Last Updated:** 2024
