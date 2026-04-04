# CfoE Sample Test Data - Gazette Compliance Testing

## 📋 Overview
This file contains sample supplier data for testing all 5 Gazette requirements:
1. Sector-specific emission intensity targets
2. Normalized output metrics per sector
3. Multi-year compliance trajectory
4. Obligated entity registry lookup
5. Pro-rata target calculation

---

## 🧪 Test Scenario 1: Aluminium Sector - Low Risk

**Supplier Name:** European Aluminium Corp  
**Sector:** aluminium  
**Emissions:** 9500 tons  
**Violations:** 1  
**Production Volume:** 1000  
**Production Unit:** tonne  
**Registry ID:** ALMOE003EU  
**Notes:** Q1 2025 audit - excellent performance, on track for 2027 targets

**Expected Results:**
- Emissions Intensity: 9.5 tCO2eq/tonne
- Risk Score: ~0.20 (Low Risk)
- Sector Thresholds: Low < 0.30, Critical ≥ 0.65
- Registry: ✓ Valid
- Pro-rata Progress: ~40% towards 2027

---

## 🧪 Test Scenario 2: Refinery Sector - Critical Risk

**Supplier Name:** Midwest Petroleum Refinery  
**Sector:** refinery  
**Emissions:** 28000 tons  
**Violations:** 5  
**Production Volume:** 1000  
**Production Unit:** MBBLS  
**Registry ID:** REFOE001MP  
**Notes:** High emissions detected, multiple violations, requires immediate HITL review

**Expected Results:**
- Emissions Intensity: 28.0 tCO2eq/MBBLS
- Risk Score: ~0.80 (Critical Risk)
- Sector Thresholds: Low < 0.35, Critical ≥ 0.70
- Registry: ✓ Valid
- HITL Required: Yes
- Human approval needed before completion

---

## 🧪 Test Scenario 3: Textiles Sector - Moderate Risk

**Supplier Name:** Pacific Basin Textiles  
**Sector:** textiles  
**Emissions:** 6500 tons  
**Violations:** 2  
**Production Volume:** 1000  
**Production Unit:** tonne  
**Registry ID:** TXTOE007PB  
**Notes:** Mid-range performance, some improvement needed

**Expected Results:**
- Emissions Intensity: 6.5 tCO2eq/tonne
- Risk Score: ~0.45 (Moderate Risk)
- Sector Thresholds: Low < 0.25, Critical ≥ 0.60
- Registry: ✓ Valid
- Pro-rata Progress: ~40%

---

## 🧪 Test Scenario 4: Petrochemicals Sector - Moderate Risk

**Supplier Name:** Asia Petrochemicals Ltd  
**Sector:** petrochemicals  
**Emissions:** 26000 tons  
**Violations:** 3  
**Production Volume:** 1000  
**Production Unit:** tonne  
**Registry ID:** PETOE009AS  
**Notes:** Standard petrochemical operations, within acceptable range

**Expected Results:**
- Emissions Intensity: 26.0 tCO2eq/tonne
- Risk Score: ~0.55 (Moderate Risk)
- Sector Thresholds: Low < 0.40, Critical ≥ 0.75
- Registry: ✓ Valid

---

## 🧪 Test Scenario 5: General Industry - Low Risk (No Registry)

**Supplier Name:** GreenTech Manufacturing  
**Sector:** default  
**Emissions:** 2500 tons  
**Violations:** 0  
**Production Volume:** 500  
**Production Unit:** tonne  
**Registry ID:** (leave empty)  
**Notes:** Small manufacturer, excellent compliance record

**Expected Results:**
- Emissions Intensity: 5.0 tCO2eq/tonne
- Risk Score: ~0.15 (Low Risk)
- Sector Thresholds: Low < 0.40, Critical ≥ 0.70
- Registry: Not provided (optional field)

---

## 🧪 Test Scenario 6: Aluminium - Without Production Volume

**Supplier Name:** Alpine Aluminium Works  
**Sector:** aluminium  
**Emissions:** 3500 tons  
**Violations:** 1  
**Production Volume:** (leave empty)  
**Production Unit:** tonne  
**Registry ID:** (leave empty)  
**Notes:** Testing fallback to absolute emissions scoring

**Expected Results:**
- Emissions Intensity: Not calculated (no volume)
- Risk Score: ~0.35 (Moderate Risk)
- Fallback to absolute emissions scoring
- Sector Thresholds still apply

---

## 🧪 Test Scenario 7: Multi-Year Trajectory Test (Submit 3 times)

**Test Purpose:** Demonstrate multi-year compliance trajectory feature

### Audit 1 (December 2024)
**Supplier Name:** TrajectoryTest Corp  
**Sector:** default  
**Emissions:** 5000 tons  
**Violations:** 4  
**Production Volume:** 1000  
**Production Unit:** tonne  
**Registry ID:** (leave empty)  
**Notes:** Baseline audit - December 2024

**Expected:** Risk Score ~0.50

### Audit 2 (January 2025)
**Supplier Name:** TrajectoryTest Corp  
**Sector:** default  
**Emissions:** 4500 tons  
**Violations:** 3  
**Production Volume:** 1000  
**Production Unit:** tonne  
**Registry ID:** (leave empty)  
**Notes:** Improvement shown - January 2025

**Expected:** Risk Score ~0.45, Trajectory starts showing

### Audit 3 (February 2025)
**Supplier Name:** TrajectoryTest Corp  
**Sector:** default  
**Emissions:** 4000 tons  
**Violations:** 2  
**Production Volume:** 1000  
**Production Unit:** tonne  
**Registry ID:** (leave empty)  
**Notes:** Continued improvement - February 2025

**Expected:** 
- Risk Score ~0.40
- Trend: 📈 Improving
- Score Change: -0.10
- Status: ✅ On Track

---

## 🧪 Test Scenario 8: Invalid Registry ID

**Supplier Name:** Unregistered Supplier Inc  
**Sector:** refinery  
**Emissions:** 20000 tons  
**Violations:** 2  
**Production Volume:** 800  
**Production Unit:** MBBLS  
**Registry ID:** INVALID123  
**Notes:** Testing registry validation error handling

**Expected Results:**
- Registry Validation: ✗ Invalid
- Error: "Registry ID 'INVALID123' not found in entity database"
- Audit should fail with 400 error

---

## 🧪 Test Scenario 9: High Production Efficiency - Excellent

**Supplier Name:** EcoEfficient Industries  
**Sector:** aluminium  
**Emissions:** 8000 tons  
**Violations:** 0  
**Production Volume:** 1000  
**Production Unit:** tonne  
**Registry ID:** (leave empty)  
**Notes:** Excellent emissions intensity, well below expected

**Expected Results:**
- Emissions Intensity: 8.0 tCO2eq/tonne
- Expected Intensity: ~13.0 (pro-rata adjusted)
- Performance: 61% of expected (excellent!)
- Risk Score: ~0.05 (Low Risk)

---

## 🧪 Test Scenario 10: Poor Production Efficiency - Critical

**Supplier Name:** HighEmissions Corp  
**Sector:** textiles  
**Emissions:** 10000 tons  
**Violations:** 6  
**Production Volume:** 1000  
**Production Unit:** tonne  
**Registry ID:** (leave empty)  
**Notes:** Very high emissions intensity, exceeds expected by >120%

**Expected Results:**
- Emissions Intensity: 10.0 tCO2eq/tonne
- Expected Intensity: ~6.8 (pro-rata adjusted)
- Performance: 147% of expected (poor!)
- Risk Score: ~0.90 (Critical Risk)
- HITL Required: Yes

---

## 📊 Quick Copy-Paste Data Sets

### Low Risk Example
```
Supplier Name: GreenTech Manufacturing
Sector: default
Emissions: 2500
Violations: 0
Production Volume: 500
Production Unit: tonne
Registry ID: 
Notes: Excellent compliance
```

### Moderate Risk Example
```
Supplier Name: Pacific Basin Textiles
Sector: textiles
Emissions: 6500
Violations: 2
Production Volume: 1000
Production Unit: tonne
Registry ID: TXTOE007PB
Notes: Mid-range performance
```

### Critical Risk Example
```
Supplier Name: Midwest Petroleum Refinery
Sector: refinery
Emissions: 28000
Violations: 5
Production Volume: 1000
Production Unit: MBBLS
Registry ID: REFOE001MP
Notes: Requires HITL review
```

---

## 🎯 Testing Checklist

### Phase 1: Sector-Specific Targets
- [ ] Test all 5 sectors (aluminium, refinery, petrochemicals, textiles, default)
- [ ] Verify sector-specific thresholds apply correctly
- [ ] Check risk classification changes per sector

### Phase 2: Normalized Metrics
- [ ] Test with production volume (calculates intensity)
- [ ] Test without production volume (fallback scoring)
- [ ] Test all 3 production units (tonne, MBBLS, NRGF)
- [ ] Verify intensity scoring (≤80%, ≤100%, ≤120%, >120%)

### Phase 3: Pro-Rata Calculation
- [ ] Verify progress percentage displays
- [ ] Check expected intensity adjusts based on date
- [ ] Confirm baseline (2023) and target (2027) years

### Phase 4: Entity Registry
- [ ] Test valid registry IDs (REFOE001MP, TXTOE007PB, ALMOE003EU, PETOE009AS)
- [ ] Test invalid registry ID (should show error)
- [ ] Test empty registry ID (should allow, optional field)
- [ ] Verify real-time validation on blur

### Phase 5: Multi-Year Trajectory
- [ ] Submit 3+ audits for same supplier
- [ ] Verify trajectory panel appears
- [ ] Check trend indicator (📈/📉/➡️)
- [ ] Verify on-track status (✅/⚠️)
- [ ] Confirm recent audit history displays

### Blockchain Integration
- [ ] Verify blockchain status panel shows connection
- [ ] Check score anchor transaction recorded
- [ ] Verify report hash with verification code
- [ ] Test HITL decision recording (critical risk audit)

---

## 🔍 Valid Registry IDs Reference

| Registry ID | Entity Name | Sector |
|-------------|-------------|--------|
| REFOE001MP | Midwest Petroleum Refinery | refinery |
| TXTOE007PB | Pacific Basin Textiles | textiles |
| ALMOE003EU | European Aluminium Corp | aluminium |
| PETOE009AS | Asia Petrochemicals Ltd | petrochemicals |

---

## 💡 Testing Tips

1. **Start Simple:** Begin with Scenario 1 (low risk) to verify basic functionality
2. **Test Registry:** Use Scenario 2 with valid registry ID to see validation
3. **Test Trajectory:** Use Scenario 7 (submit 3 times) to see trend analysis
4. **Test HITL:** Use Scenario 2 or 10 (critical risk) to trigger human approval
5. **Test Errors:** Use Scenario 8 (invalid registry) to verify error handling
6. **Mix and Match:** Combine different fields to create custom scenarios

---

## 📝 Notes

- All emissions values are in tons CO2
- Production volumes are in specified units (tonne, MBBLS, NRGF)
- Violations range from 0-500 (system limit)
- Registry IDs are case-insensitive
- Notes field supports up to 1000 characters
- Supplier names support 2-120 characters

---

**Created for:** CfoE Gazette Compliance Testing  
**Version:** 1.0  
**Last Updated:** 2024  
**Status:** ✅ Ready for Testing
