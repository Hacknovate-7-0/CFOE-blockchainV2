"""
Carbon Footprint Optimization Engine (CfoE)
Main entry point for running the multi-agent system using ADK framework
with Algorand blockchain integration for immutable audit recording.
"""

import os
from dotenv import load_dotenv
from config.groq_config import get_groq_client
from blockchain_client import get_blockchain_client

# Load environment variables
load_dotenv()

# Configure Groq client
client = get_groq_client()

# Import the root coordinator
from orchestrators.root_coordinator import create_root_coordinator


def run_audit(supplier_name: str, emissions: float, violations: int):
    """
    Run a complete ESG audit for a supplier using ADK multi-agent pipeline.
    Results are automatically recorded on the Algorand blockchain.

    Args:
        supplier_name: Name of the supplier
        emissions: Annual CO2 emissions in tons
        violations: Number of regulatory violations
    """
    print(f"\n{'='*60}")
    print(f"Starting ESG Audit for: {supplier_name}")
    print(f"{'='*60}\n")

    # Create the root coordinator
    root_coordinator = create_root_coordinator(client)

    # Prepare input
    audit_input = f"""
    Conduct a comprehensive ESG audit for the following supplier:
    
    Supplier Name: {supplier_name}
    Annual CO2 Emissions: {emissions} tons
    Regulatory Violations: {violations}
    
    Please provide a complete risk assessment and recommendations.
    """

    # Run the multi-agent audit pipeline
    # (blockchain recording happens automatically inside the coordinator)
    try:
        response = root_coordinator.generate_content(audit_input)

        print(f"\n{'='*60}")
        print("FINAL AUDIT REPORT")
        print(f"{'='*60}\n")
        print(response.text)
        print(f"\n{'='*60}\n")

        return response

    except Exception as e:
        print(f"Error during audit: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """Main function with example usage"""

    print("\n" + "=" * 60)
    print("Carbon Footprint Optimization Engine (CfoE)")
    print("Multi-Agent ESG Compliance System (Groq + Llama)")
    print("Blockchain: Algorand Testnet")
    print("=" * 60 + "\n")

    # Initialize blockchain connection
    blockchain = get_blockchain_client()
    balance_info = blockchain.get_balance()
    if balance_info.get("status") == "OK":
        print(f"  Blockchain: CONNECTED")
        print(f"  Balance: {balance_info['balance_algo']:.6f} ALGO")
        print(f"  Address: {balance_info['address'][:16]}...")
    else:
        print(f"  Blockchain: OFFLINE (local logging only)")
    print()

    # Example 1: Low Risk Supplier
    print("\n--- Example 1: Low Risk Supplier ---")
    run_audit(
        supplier_name="GreenTech Solutions",
        emissions=500,
        violations=0
    )

    # Example 2: Moderate Risk Supplier
    print("\n--- Example 2: Moderate Risk Supplier ---")
    run_audit(
        supplier_name="StandardCorp Manufacturing",
        emissions=2500,
        violations=2
    )

    # Example 3: High Risk Supplier (triggers HITL)
    print("\n--- Example 3: High Risk Supplier ---")
    run_audit(
        supplier_name="PolluteCo Industries",
        emissions=8000,
        violations=5
    )

    # Print blockchain audit summary
    print("\n" + "=" * 60)
    print("BLOCKCHAIN AUDIT TRAIL")
    print("=" * 60)
    print(blockchain.get_audit_summary())
    print()
    print(blockchain.get_status_report())


if __name__ == "__main__":
    main()
