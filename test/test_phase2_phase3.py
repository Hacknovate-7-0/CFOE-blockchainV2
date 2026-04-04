"""
Test script for Phase 2 (Registry) and Phase 3 (Trajectory) implementation
"""

from agents.registry_agent import validate_registry_id, get_entity_info
from agents.trajectory_agent import calculate_trajectory, check_compliance_trajectory

def test_registry_validation():
    """Test entity registry validation"""
    print("=" * 60)
    print("PHASE 2: ENTITY REGISTRY VALIDATION TESTS")
    print("=" * 60)
    
    # Test 1: Valid registry ID
    print("\n[Test 1] Valid Registry ID: REFOE001MP")
    result = validate_registry_id("REFOE001MP")
    assert result["valid"] == True
    assert result["entity"]["name"] == "Midwest Petroleum Refinery"
    assert result["entity"]["sector"] == "refinery"
    print(f"✓ Valid: {result['entity']['name']} ({result['entity']['sector']})")
    
    # Test 2: Invalid registry ID
    print("\n[Test 2] Invalid Registry ID: INVALID123")
    result = validate_registry_id("INVALID123")
    assert result["valid"] == False
    assert "not found" in result["error"]
    print(f"✓ Invalid: {result['error']}")
    
    # Test 3: Empty registry ID
    print("\n[Test 3] Empty Registry ID")
    result = validate_registry_id("")
    assert result["valid"] == False
    assert "required" in result["error"]
    print(f"✓ Empty: {result['error']}")
    
    # Test 4: Get entity info
    print("\n[Test 4] Get Entity Info: TXTOE007PB")
    entity = get_entity_info("TXTOE007PB")
    assert entity is not None
    assert entity["name"] == "Pacific Basin Textiles"
    print(f"✓ Entity: {entity['name']} - Status: {entity['status']}")
    
    print("\n✅ All registry validation tests passed!")

def test_trajectory_calculation():
    """Test multi-year trajectory calculation"""
    print("\n" + "=" * 60)
    print("PHASE 3: MULTI-YEAR TRAJECTORY TESTS")
    print("=" * 60)
    
    # Mock audit history
    mock_history = [
        {
            "audit_id": "AUD-001",
            "supplier_name": "TestCorp",
            "timestamp": "2025-01-15T10:00:00",
            "risk_score": 0.38,
            "classification": "Low Risk",
            "emissions": 2000,
            "violations": 1
        },
        {
            "audit_id": "AUD-002",
            "supplier_name": "TestCorp",
            "timestamp": "2024-12-10T10:00:00",
            "risk_score": 0.42,
            "classification": "Moderate Risk",
            "emissions": 2200,
            "violations": 2
        },
        {
            "audit_id": "AUD-003",
            "supplier_name": "TestCorp",
            "timestamp": "2024-11-05T10:00:00",
            "risk_score": 0.45,
            "classification": "Moderate Risk",
            "emissions": 2400,
            "violations": 2
        },
        {
            "audit_id": "AUD-004",
            "supplier_name": "TestCorp",
            "timestamp": "2024-10-01T10:00:00",
            "risk_score": 0.48,
            "classification": "Moderate Risk",
            "emissions": 2600,
            "violations": 3
        },
        {
            "audit_id": "AUD-005",
            "supplier_name": "OtherCorp",
            "timestamp": "2024-09-15T10:00:00",
            "risk_score": 0.65,
            "classification": "Critical Risk",
            "emissions": 5000,
            "violations": 5
        }
    ]
    
    # Test 1: Calculate trajectory for supplier with multiple audits
    print("\n[Test 1] Calculate Trajectory: TestCorp (4 audits)")
    trajectory = calculate_trajectory("TestCorp", mock_history)
    assert trajectory["audit_count"] == 4
    assert trajectory["trend"] in ["improving", "deteriorating", "stable"]
    assert trajectory["latest_score"] == 0.38
    assert trajectory["oldest_score"] == 0.48
    print(f"✓ Audit Count: {trajectory['audit_count']}")
    print(f"✓ Trend: {trajectory['trend_label']}")
    print(f"✓ Score Change: {trajectory['score_change']}")
    print(f"✓ Improvement Rate: {trajectory['improvement_rate']:.3f}/audit")
    
    # Test 2: Check compliance trajectory
    print("\n[Test 2] Check Compliance Trajectory: TestCorp")
    compliance = check_compliance_trajectory("TestCorp", mock_history, 2023, 2027)
    assert "on_track" in compliance
    assert compliance["audit_count"] == 4
    print(f"✓ On Track: {compliance.get('on_track')}")
    print(f"✓ Status: {compliance.get('status', 'N/A')}")
    if compliance.get("years_remaining"):
        print(f"✓ Years Remaining: {compliance['years_remaining']}")
        print(f"✓ Required Rate: {compliance['required_rate']:.3f}/year")
    
    # Test 3: Supplier with no audits
    print("\n[Test 3] Calculate Trajectory: NonExistent (0 audits)")
    trajectory = calculate_trajectory("NonExistent", mock_history)
    assert trajectory["audit_count"] == 0
    assert trajectory["trend"] == "no_data"
    print(f"✓ No Data: {trajectory['message']}")
    
    # Test 4: Supplier with single audit
    print("\n[Test 4] Calculate Trajectory: OtherCorp (1 audit)")
    trajectory = calculate_trajectory("OtherCorp", mock_history)
    assert trajectory["audit_count"] == 1
    assert trajectory["trend"] == "insufficient_data"
    print(f"✓ Insufficient Data: {trajectory['message']}")
    
    print("\n✅ All trajectory calculation tests passed!")

def test_integration():
    """Test integration between registry and trajectory"""
    print("\n" + "=" * 60)
    print("INTEGRATION TEST: REGISTRY + TRAJECTORY")
    print("=" * 60)
    
    # Validate registry and get entity
    print("\n[Integration] Validate REFOE001MP and check trajectory")
    validation = validate_registry_id("REFOE001MP")
    assert validation["valid"] == True
    
    entity = validation["entity"]
    print(f"✓ Entity: {entity['name']}")
    print(f"✓ Sector: {entity['sector']}")
    print(f"✓ Status: {entity['status']}")
    
    # Mock history for this entity
    mock_history = [
        {
            "supplier_name": "Midwest Petroleum Refinery",
            "timestamp": "2025-01-10T10:00:00",
            "risk_score": 0.55,
            "classification": "Moderate Risk",
            "emissions": 24000,
            "violations": 3,
            "registry_id": "REFOE001MP"
        },
        {
            "supplier_name": "Midwest Petroleum Refinery",
            "timestamp": "2024-12-01T10:00:00",
            "risk_score": 0.60,
            "classification": "Moderate Risk",
            "emissions": 25000,
            "violations": 4,
            "registry_id": "REFOE001MP"
        }
    ]
    
    trajectory = calculate_trajectory("Midwest Petroleum Refinery", mock_history)
    print(f"✓ Trajectory: {trajectory['trend_label']}")
    print(f"✓ Audits: {trajectory['audit_count']}")
    
    print("\n✅ Integration test passed!")

if __name__ == "__main__":
    try:
        test_registry_validation()
        test_trajectory_calculation()
        test_integration()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED - PHASE 2 & 3 COMPLETE!")
        print("=" * 60)
        print("\nImplemented Features:")
        print("  ✅ Entity Registry Validation")
        print("  ✅ Registry ID Lookup")
        print("  ✅ Multi-Year Trajectory Calculation")
        print("  ✅ Compliance Trend Analysis")
        print("  ✅ On-Track Status Assessment")
        print("\nNext Steps:")
        print("  1. Test in running UI (uvicorn webapp:app --reload)")
        print("  2. Submit audit with registry ID (e.g., REFOE001MP)")
        print("  3. Submit multiple audits for same supplier")
        print("  4. View trajectory panel in latest result")
        print("  5. Verify registry validation on blur event")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise
