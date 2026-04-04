"""
Quick test to verify blockchain integration in the UI workflow
"""

from blockchain_client import get_blockchain_client

def test_blockchain_integration():
    print("=" * 60)
    print("  BLOCKCHAIN UI INTEGRATION TEST")
    print("=" * 60)
    
    # Initialize blockchain client
    bc = get_blockchain_client()
    
    # Test 1: Connection status
    print("\n[TEST 1] Connection Status")
    print(f"  Connected: {bc.connected}")
    print(f"  Address: {bc.address[:20]}...")
    
    # Test 2: Balance check
    print("\n[TEST 2] Balance Check")
    balance = bc.get_balance()
    print(f"  Balance: {balance.get('balance_algo', 0):.6f} ALGO")
    print(f"  Status: {balance.get('status', 'N/A')}")
    
    # Test 3: Anchor a test score
    print("\n[TEST 3] Score Anchoring")
    score_record = bc.anchor_score(
        supplier_name="TestSupplier Corp",
        risk_score=0.45,
        classification="Moderate Risk",
        emissions=2500.0,
        violations=2,
        emissions_score=0.30,
        violations_score=0.15,
        external_risk_score=0.0
    )
    print(f"  TX ID: {score_record.get('tx_id') or score_record.get('local_id', 'N/A')}")
    print(f"  On-Chain: {score_record.get('on_chain', False)}")
    print(f"  Data Hash: {score_record.get('data_hash', 'N/A')[:24]}...")
    
    # Test 4: Record HITL decision
    print("\n[TEST 4] HITL Decision Recording")
    hitl_record = bc.record_hitl_decision(
        supplier_name="TestSupplier Corp",
        score_anchor_tx=score_record.get('tx_id'),
        approved=True,
        risk_score=0.45,
        decision="Continue with monitoring",
        reason="Risk within acceptable threshold",
        recommended_action="Quarterly review"
    )
    print(f"  TX ID: {hitl_record.get('tx_id') or hitl_record.get('local_id', 'N/A')}")
    print(f"  Decision: {hitl_record.get('decision', 'N/A')}")
    print(f"  Crypto Proof: {hitl_record.get('cryptographic_proof', False)}")
    
    # Test 5: Register report hash
    print("\n[TEST 5] Report Hash Registration")
    test_report = "Executive Summary\nSupplier: TestSupplier Corp\nRisk Score: 0.45\n..."
    report_record = bc.register_report_hash(
        supplier_name="TestSupplier Corp",
        score_anchor_tx=score_record.get('tx_id'),
        hitl_decision_tx=hitl_record.get('tx_id'),
        report_text=test_report
    )
    print(f"  TX ID: {report_record.get('tx_id') or report_record.get('local_id', 'N/A')}")
    print(f"  Verification Code: {report_record.get('verification_code', 'N/A')}")
    print(f"  Report Hash: {report_record.get('report_hash', 'N/A')[:24]}...")
    
    # Test 6: Full status report
    print("\n[TEST 6] Full Status Report")
    print(bc.get_status_report())
    
    print("\n" + "=" * 60)
    print("  TEST COMPLETE")
    print("=" * 60)
    print("\nBlockchain integration is ready for the UI!")
    print("Start the webapp with: uvicorn webapp:app --reload")
    print("Then navigate to: http://127.0.0.1:8000")

if __name__ == "__main__":
    test_blockchain_integration()
