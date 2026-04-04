"""
Carbon Footprint Optimization Engine (CfoE)
Simplified version with 3-point blockchain integration.

Three cryptographic integration points:
1. Score Anchoring   - after CalculationAgent (immutable score + data hash)
2. HITL Decision     - after PolicyAgent (wallet-signed proof of human review)
3. Report Hash       - after ReportingAgent (SHA-256 tamper detection)
"""

import os
import hashlib
from dotenv import load_dotenv
from config.groq_config import get_groq_client
from blockchain_client import get_blockchain_client

load_dotenv()
client = get_groq_client()


def calculate_carbon_score(emissions: float, violations: int) -> dict:
    """Deterministic ESG risk score calculation."""
    if emissions < 1000:
        emissions_score = 0.1
    elif emissions < 3000:
        emissions_score = 0.25
    elif emissions < 5000:
        emissions_score = 0.35
    else:
        emissions_score = 0.5

    violations_score = min(violations * 0.1, 0.5)
    risk_score = emissions_score + violations_score

    if risk_score >= 0.7:
        classification = "Critical Risk"
    elif risk_score >= 0.4:
        classification = "Moderate Risk"
    else:
        classification = "Low Risk"

    return {
        "risk_score": round(risk_score, 2),
        "classification": classification,
        "emissions_score": round(emissions_score, 2),
        "violations_score": round(violations_score, 2),
    }


def enforce_policy_hitl(risk_score: float, supplier_name: str) -> dict:
    """Enforce compliance policy with HITL for critical risks."""
    if risk_score >= 0.7:
        return {
            "decision": "PAUSE - Human Approval Required",
            "human_approval_required": True,
            "reason": f"Critical risk detected (score: {risk_score}). Manual review mandatory.",
            "recommended_action": "Suspend supplier relationship pending investigation",
        }
    elif risk_score >= 0.4:
        return {
            "decision": "FLAGGED - Enhanced Monitoring",
            "human_approval_required": False,
            "reason": f"Moderate risk detected (score: {risk_score}). Increased oversight recommended.",
            "recommended_action": "Implement quarterly audits and improvement plan",
        }
    else:
        return {
            "decision": "APPROVED - Standard Monitoring",
            "human_approval_required": False,
            "reason": f"Low risk detected (score: {risk_score}). Continue normal operations.",
            "recommended_action": "Maintain annual audit schedule",
        }


def run_audit(supplier_name: str, emissions: float, violations: int):
    """
    Run a complete ESG audit with 3 blockchain integration points.

    Pipeline:
      Calculate -> [BLOCKCHAIN: Score Anchor]
      Policy    -> [BLOCKCHAIN: HITL Decision]
      Report    -> [BLOCKCHAIN: Report Hash]
    """
    print(f"\n{'='*60}")
    print(f"ESG AUDIT: {supplier_name}")
    print(f"{'='*60}\n")

    blockchain = get_blockchain_client()

    # Track chain of custody
    score_anchor_tx = None
    hitl_decision_tx = None
    report_hash_tx = None

    # ================================================================ #
    #  PHASE 1: Calculate Risk Score
    # ================================================================ #
    print("[1/6] Calculating ESG risk score...")
    risk_data = calculate_carbon_score(emissions, violations)
    print(f"  > Risk Score:       {risk_data['risk_score']}")
    print(f"  > Classification:   {risk_data['classification']}")
    print(f"  > Emissions Score:  {risk_data['emissions_score']}")
    print(f"  > Violations Score: {risk_data['violations_score']}\n")

    # ================================================================ #
    #  BLOCKCHAIN POINT 1: Score Anchoring
    # ================================================================ #
    print("[  ] BLOCKCHAIN: Anchoring score on-chain...")
    try:
        score_result = blockchain.anchor_score(
            supplier_name=supplier_name,
            risk_score=risk_data["risk_score"],
            classification=risk_data["classification"],
            emissions=emissions,
            violations=violations,
            emissions_score=risk_data["emissions_score"],
            violations_score=risk_data["violations_score"],
        )
        score_anchor_tx = score_result.get("tx_id")
    except Exception as e:
        print(f"  [Blockchain] Score anchor failed: {e}")
    print()

    # ================================================================ #
    #  PHASE 2: Policy Enforcement
    # ================================================================ #
    print("[2/6] Enforcing compliance policy...")
    policy = enforce_policy_hitl(risk_data["risk_score"], supplier_name)
    print(f"  > Decision: {policy['decision']}")
    print(f"  > Reason:   {policy['reason']}")
    print(f"  > Action:   {policy['recommended_action']}\n")

    # ================================================================ #
    #  BLOCKCHAIN POINT 2: HITL Decision Ledger
    # ================================================================ #
    print("[  ] BLOCKCHAIN: Recording HITL decision on-chain...")
    try:
        hitl_result = blockchain.record_hitl_decision(
            supplier_name=supplier_name,
            score_anchor_tx=score_anchor_tx,
            approved=not policy["human_approval_required"],
            risk_score=risk_data["risk_score"],
            decision=policy["decision"],
            reason=policy["reason"],
            recommended_action=policy["recommended_action"],
        )
        hitl_decision_tx = hitl_result.get("tx_id")
    except Exception as e:
        print(f"  [Blockchain] HITL recording failed: {e}")
    print()

    # ================================================================ #
    #  PHASE 3: Generate Report with AI
    # ================================================================ #
    print("[3/6] Generating executive report with AI...\n")

    prompt = f"""
    Generate a comprehensive ESG audit report for the following supplier:
    
    SUPPLIER INFORMATION:
    - Name: {supplier_name}
    - Annual CO2 Emissions: {emissions} tons
    - Regulatory Violations: {violations}
    
    RISK ASSESSMENT:
    - Risk Score: {risk_data['risk_score']} / 1.00
    - Classification: {risk_data['classification']}
    - Emissions Score: {risk_data['emissions_score']}
    - Violations Score: {risk_data['violations_score']}
    
    POLICY DECISION:
    - Decision: {policy['decision']}
    - Human Approval Required: {policy['human_approval_required']}
    - Reason: {policy['reason']}
    - Recommended Action: {policy['recommended_action']}
    
    BLOCKCHAIN VERIFICATION:
    - Score Anchor TX: {score_anchor_tx or 'Pending'}
    - HITL Decision TX: {hitl_decision_tx or 'Pending'}
    - Network: Algorand Testnet
    - Auditor Address: {blockchain.address[:16]}...
    
    You MUST write a detailed, multi-section report covering ALL of the following:
    1. Executive Summary (3-4 sentences)
    2. Key Findings (4+ bullet points)
    3. Risk Analysis (emissions and violations breakdown)
    4. Compliance Status (regulatory standing)
    5. Blockchain Verification (on-chain audit trail with TX references)
    6. Recommended Actions (4+ specific items)
    7. Next Steps (timeline and ownership)

    Each section must be thorough. Do not summarize or truncate.
    
    End with REFERENCES & RESOURCES:
    - ESG Reporting Standards: https://www.globalreporting.org/standards/
    - Carbon Disclosure Project: https://www.cdp.net/
    - Science Based Targets Initiative: https://sciencebasedtargets.org/
    - EPA Compliance Resources: https://www.epa.gov/compliance
    - ISO 14001 Environmental Management: https://www.iso.org/iso-14001-environmental-management.html
    - Algorand Explorer: https://testnet.explorer.perawallet.app/
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior ESG compliance analyst. Produce detailed, "
                        "structured, multi-section audit reports with blockchain "
                        "verification references. Never truncate sections."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=8192,
            temperature=0.7,
        )
        report_text = response.choices[0].message.content

    except Exception as e:
        print(f"  Error generating report: {e}")
        report_text = (
            f"FALLBACK AUDIT REPORT\n"
            f"Supplier: {supplier_name}\n"
            f"Risk Score: {risk_data['risk_score']} ({risk_data['classification']})\n"
            f"Decision: {policy['decision']}\n"
            f"Action: {policy['recommended_action']}\n"
            f"Score TX: {score_anchor_tx or 'N/A'}\n"
            f"HITL TX: {hitl_decision_tx or 'N/A'}\n"
        )

    # ================================================================ #
    #  BLOCKCHAIN POINT 3: Report Hash Registry
    # ================================================================ #
    print("[4/6] BLOCKCHAIN: Registering report hash on-chain...")
    try:
        report_result = blockchain.register_report_hash(
            supplier_name=supplier_name,
            score_anchor_tx=score_anchor_tx,
            hitl_decision_tx=hitl_decision_tx,
            report_text=report_text,
        )
        report_hash_tx = report_result.get("tx_id")
    except Exception as e:
        print(f"  [Blockchain] Report hash registration failed: {e}")

    # ================================================================ #
    #  OUTPUT: Final Report + Chain of Custody
    # ================================================================ #
    print(f"\n{'='*60}")
    print("EXECUTIVE AUDIT REPORT")
    print(f"{'='*60}\n")
    print(report_text)

    print(f"\n{'='*60}")
    print(f"CHAIN OF CUSTODY (Algorand Testnet)")
    print(f"{'='*60}")
    print(f"  1. Score Anchor TX:   {(score_anchor_tx or 'N/A')[:40]}...")
    print(f"  2. HITL Decision TX:  {(hitl_decision_tx or 'N/A')[:40]}...")
    print(f"  3. Report Hash TX:    {(report_hash_tx or 'N/A')[:40]}...")
    print(f"{'='*60}\n")

    return {
        "report": report_text,
        "risk_data": risk_data,
        "policy": policy,
        "chain_of_custody": {
            "score_anchor_tx": score_anchor_tx,
            "hitl_decision_tx": hitl_decision_tx,
            "report_hash_tx": report_hash_tx,
        },
    }


def main():
    """Main function with example usage."""

    print("\n" + "=" * 60)
    print("Carbon Footprint Optimization Engine (CfoE)")
    print("3-Point Blockchain Integration")
    print("Network: Algorand Testnet")
    print("=" * 60 + "\n")

    blockchain = get_blockchain_client()
    balance = blockchain.get_balance()
    if balance.get("status") == "OK":
        print(f"  Blockchain:  CONNECTED")
        print(f"  Balance:     {balance['balance_algo']:.6f} ALGO")
        print(f"  Address:     {balance['address'][:20]}...")
    else:
        print(f"  Blockchain:  OFFLINE (local logging)")
    print()

    # Example 1: Low Risk
    run_audit("GreenTech Solutions", emissions=500, violations=0)

    # Example 2: Moderate Risk
    run_audit("StandardCorp Manufacturing", emissions=2500, violations=2)

    # Example 3: Critical Risk (triggers HITL)
    run_audit("PolluteCo Industries", emissions=8000, violations=5)

    # Print full blockchain summary
    print("\n" + "=" * 60)
    print("BLOCKCHAIN AUDIT TRAIL")
    print("=" * 60)
    print(blockchain.get_audit_summary())
    print()
    print(blockchain.get_status_report())


if __name__ == "__main__":
    main()
