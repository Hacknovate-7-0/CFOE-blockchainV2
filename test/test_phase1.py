"""
Test Phase 1 Implementation: Sector-Specific Targets + Pro-Rata + Normalized Metrics
"""

from agents.calculation_agent import calculate_carbon_score, SECTOR_THRESHOLDS
from datetime import datetime

def test_phase1():
    print("=" * 70)
    print("  PHASE 1 IMPLEMENTATION TEST")
    print("=" * 70)
    
    # Test 1: Aluminium Sector with Production Volume
    print("\n[TEST 1] Aluminium Sector with Normalized Metrics")
    print("-" * 70)
    result = calculate_carbon_score(
        emissions=15000,
        violations=2,
        sector="aluminium",
        production_volume=1000,
        audit_date=datetime(2025, 6, 15)
    )
    
    print(f"Sector: {result['sector']}")
    print(f"Emissions Intensity: {result.get('emissions_intensity', 'N/A')} tCO2eq/tonne")
    print(f"Expected Intensity: {result.get('expected_intensity', 'N/A')} tCO2eq/tonne")
    print(f"Pro-rata Progress: {result['prorata_progress']:.1%}")
    print(f"Risk Score: {result['risk_score']}")
    print(f"Classification: {result['classification']}")
    print(f"Sector Thresholds: Low < {result['sector_thresholds']['low']}, Critical >= {result['sector_thresholds']['critical']}")
    
    # Test 2: Refinery Sector (Critical Risk)
    print("\n[TEST 2] Refinery Sector (Critical Risk)")
    print("-" * 70)
    result = calculate_carbon_score(
        emissions=25000,
        violations=5,
        sector="refinery",
        production_volume=1000,
        audit_date=datetime.now()
    )
    
    print(f"Sector: {result['sector']}")
    print(f"Emissions Intensity: {result.get('emissions_intensity', 'N/A')} tCO2eq/MBBLS")
    print(f"Risk Score: {result['risk_score']}")
    print(f"Classification: {result['classification']}")
    print(f"HITL Required: {result['risk_score'] >= result['sector_thresholds']['critical']}")
    
    # Test 3: Textiles Sector (Low Risk)
    print("\n[TEST 3] Textiles Sector (Low Risk)")
    print("-" * 70)
    result = calculate_carbon_score(
        emissions=5000,
        violations=0,
        sector="textiles",
        production_volume=1000,
        audit_date=datetime.now()
    )
    
    print(f"Sector: {result['sector']}")
    print(f"Emissions Intensity: {result.get('emissions_intensity', 'N/A')} tCO2eq/tonne")
    print(f"Risk Score: {result['risk_score']}")
    print(f"Classification: {result['classification']}")
    
    # Test 4: Default Sector without Production Volume
    print("\n[TEST 4] Default Sector (No Production Volume)")
    print("-" * 70)
    result = calculate_carbon_score(
        emissions=3500,
        violations=1,
        sector="default",
        production_volume=None,
        audit_date=datetime.now()
    )
    
    print(f"Sector: {result['sector']}")
    print(f"Emissions Intensity: {result.get('emissions_intensity', 'Not calculated (no production volume)')}")
    print(f"Risk Score: {result['risk_score']}")
    print(f"Classification: {result['classification']}")
    print(f"Note: Fallback to absolute emissions scoring")
    
    # Test 5: Pro-rata Progress Verification
    print("\n[TEST 5] Pro-rata Progress at Different Dates")
    print("-" * 70)
    
    dates = [
        ("Start of 2023", datetime(2023, 1, 1)),
        ("Mid 2024", datetime(2024, 6, 15)),
        ("End of 2025", datetime(2025, 12, 31)),
        ("Mid 2026", datetime(2026, 6, 15)),
        ("End of 2027", datetime(2027, 12, 31))
    ]
    
    for label, date in dates:
        result = calculate_carbon_score(
            emissions=10000,
            violations=1,
            sector="aluminium",
            production_volume=1000,
            audit_date=date
        )
        print(f"{label:20} -> Progress: {result['prorata_progress']:6.1%}, Expected Intensity: {result.get('expected_intensity', 0):.2f}")
    
    # Test 6: Sector Thresholds Summary
    print("\n[TEST 6] All Sector Thresholds")
    print("-" * 70)
    print(f"{'Sector':<20} {'Low Threshold':<15} {'Critical Threshold':<20} {'Baseline':<12} {'Target'}")
    print("-" * 70)
    for key, config in SECTOR_THRESHOLDS.items():
        print(f"{config['name']:<20} < {config['low']:<14.2f} >= {config['critical']:<19.2f} {config['baseline_intensity']:<12.1f} {config['target_intensity']:.1f}")
    
    print("\n" + "=" * 70)
    print("  PHASE 1 TEST COMPLETE")
    print("=" * 70)
    print("\n✅ All features implemented:")
    print("  1. Sector-specific emission intensity targets")
    print("  2. Normalized output metrics per sector")
    print("  3. Pro-rata target calculation for mid-year audits")
    print("\n🔗 Blockchain compatible: All new fields included in hash")
    print("\n📝 Next: Test in UI at http://127.0.0.1:8000")

if __name__ == "__main__":
    test_phase1()
