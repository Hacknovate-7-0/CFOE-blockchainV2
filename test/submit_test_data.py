"""
Automated Test Data Submission Script
Quickly submit sample audits to test all Gazette requirements
"""

import json
import requests
import time
from pathlib import Path

# API endpoint
API_URL = "http://127.0.0.1:8000/api/audit"

def load_test_data():
    """Load test data from JSON file"""
    data_file = Path(__file__).parent / "sample_test_data.json"
    with open(data_file, 'r') as f:
        return json.load(f)

def submit_audit(data, scenario_name):
    """Submit a single audit to the API"""
    print(f"\n{'='*60}")
    print(f"Submitting: {scenario_name}")
    print(f"{'='*60}")
    print(f"Supplier: {data['supplier_name']}")
    print(f"Sector: {data['sector']}")
    print(f"Emissions: {data['emissions']} tons")
    print(f"Violations: {data['violations']}")
    if data.get('production_volume'):
        print(f"Production: {data['production_volume']} {data['production_unit']}")
    if data.get('registry_id'):
        print(f"Registry ID: {data['registry_id']}")
    
    try:
        response = requests.post(API_URL, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ SUCCESS")
            print(f"Audit ID: {result['audit_id']}")
            print(f"Risk Score: {result['risk_score']} ({result['classification']})")
            if result.get('emissions_intensity'):
                print(f"Emissions Intensity: {result['emissions_intensity']:.2f} tCO2eq/{data['production_unit']}")
            if result.get('prorata_progress'):
                print(f"Pro-rata Progress: {result['prorata_progress']*100:.1f}%")
            print(f"Policy Decision: {result['policy_decision']}")
            if result.get('human_approval_required'):
                print(f"⚠️  HITL Required: Human approval needed")
            return True
        else:
            print(f"\n❌ FAILED: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ CONNECTION ERROR")
        print(f"Make sure the server is running: uvicorn webapp:app --reload")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

def run_quick_tests():
    """Run quick test suite with 3 basic scenarios"""
    print("\n" + "="*60)
    print("QUICK TEST SUITE - 3 Scenarios")
    print("="*60)
    
    test_data = load_test_data()
    quick_tests = test_data['quick_test_data']
    
    scenarios = [
        ("Low Risk", quick_tests['low_risk']),
        ("Moderate Risk", quick_tests['moderate_risk']),
        ("Critical Risk", quick_tests['critical_risk'])
    ]
    
    results = []
    for name, data in scenarios:
        success = submit_audit(data, name)
        results.append((name, success))
        time.sleep(1)  # Brief pause between requests
    
    print("\n" + "="*60)
    print("QUICK TEST RESULTS")
    print("="*60)
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{name}: {status}")

def run_full_tests():
    """Run full test suite with all scenarios"""
    print("\n" + "="*60)
    print("FULL TEST SUITE - All Scenarios")
    print("="*60)
    
    test_data = load_test_data()
    scenarios = test_data['test_scenarios']
    
    results = []
    for scenario in scenarios:
        # Skip invalid registry test in automated mode
        if scenario.get('expected', {}).get('should_fail'):
            print(f"\nSkipping: {scenario['name']} (expected to fail)")
            continue
            
        success = submit_audit(scenario['data'], scenario['name'])
        results.append((scenario['name'], success))
        time.sleep(1)  # Brief pause between requests
    
    print("\n" + "="*60)
    print("FULL TEST RESULTS")
    print("="*60)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print("="*60)
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{name}: {status}")

def run_trajectory_test():
    """Run trajectory test by submitting 3 audits for same supplier"""
    print("\n" + "="*60)
    print("TRAJECTORY TEST - 3 Sequential Audits")
    print("="*60)
    print("This will submit 3 audits for 'TrajectoryTest Corp'")
    print("to demonstrate multi-year compliance trajectory feature")
    
    test_data = load_test_data()
    scenarios = test_data['test_scenarios']
    
    # Find trajectory test scenarios
    trajectory_scenarios = [s for s in scenarios if 'scenario_7' in s['id']]
    
    results = []
    for i, scenario in enumerate(trajectory_scenarios, 1):
        print(f"\n--- Audit {i}/3 ---")
        success = submit_audit(scenario['data'], scenario['name'])
        results.append((scenario['name'], success))
        time.sleep(2)  # Longer pause to ensure proper ordering
    
    print("\n" + "="*60)
    print("TRAJECTORY TEST COMPLETE")
    print("="*60)
    print("Check the UI to see the trajectory panel with:")
    print("  - Trend indicator (📈 Improving)")
    print("  - Score change over time")
    print("  - On-track status")
    print("  - Recent audit history")

def show_menu():
    """Display interactive menu"""
    print("\n" + "="*60)
    print("CfoE TEST DATA SUBMISSION TOOL")
    print("="*60)
    print("\nOptions:")
    print("  1. Quick Test (3 scenarios: Low, Moderate, Critical)")
    print("  2. Full Test (All 10 scenarios)")
    print("  3. Trajectory Test (3 audits for same supplier)")
    print("  4. Submit Single Scenario")
    print("  5. Show Valid Registry IDs")
    print("  6. Exit")
    print("\nMake sure the server is running:")
    print("  uvicorn webapp:app --reload")
    
    choice = input("\nEnter choice (1-6): ").strip()
    return choice

def submit_single_scenario():
    """Let user choose and submit a single scenario"""
    test_data = load_test_data()
    scenarios = test_data['test_scenarios']
    
    print("\n" + "="*60)
    print("AVAILABLE SCENARIOS")
    print("="*60)
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['name']}")
    
    try:
        choice = int(input("\nEnter scenario number: ").strip())
        if 1 <= choice <= len(scenarios):
            scenario = scenarios[choice - 1]
            submit_audit(scenario['data'], scenario['name'])
        else:
            print("Invalid choice")
    except ValueError:
        print("Invalid input")

def show_registry_ids():
    """Display valid registry IDs"""
    test_data = load_test_data()
    registry_ids = test_data['valid_registry_ids']
    
    print("\n" + "="*60)
    print("VALID REGISTRY IDs")
    print("="*60)
    for entity in registry_ids:
        print(f"{entity['id']}: {entity['name']} ({entity['sector']})")

def main():
    """Main entry point"""
    while True:
        choice = show_menu()
        
        if choice == '1':
            run_quick_tests()
        elif choice == '2':
            run_full_tests()
        elif choice == '3':
            run_trajectory_test()
        elif choice == '4':
            submit_single_scenario()
        elif choice == '5':
            show_registry_ids()
        elif choice == '6':
            print("\nExiting...")
            break
        else:
            print("\nInvalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
