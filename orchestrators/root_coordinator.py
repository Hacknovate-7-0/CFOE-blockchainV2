"""
Root Coordinator - Sequential orchestration using custom framework with Groq
Includes Algorand blockchain integration for immutable audit recording.
"""

import re
from dataclasses import dataclass
from datetime import datetime

from config.agent_framework import SequentialOrchestrator, AgentContext
from config.groq_config import get_groq_client

from agents.monitor_agent import create_monitor_agent
from agents.calculation_agent import create_calculation_agent, calculate_carbon_score
from agents.policy_agent import create_policy_agent, enforce_policy_hitl
from agents.reporting_agent import create_reporting_agent
from agents.credit_agent import calculate_carbon_credits
from blockchain_client import get_blockchain_client


@dataclass
class CoordinatorResponse:
    """Response object compatible with main.py expectations."""
    text: str


class RootCoordinator:
    """
    Root coordinator using custom framework for multi-agent orchestration.
    
    Workflow:
    1. Monitor Agent - Gathers external risk data via Tavily Search
    2. Calculation Agent - Computes deterministic ESG risk scores
    3. Policy Agent - Enforces compliance policies with HITL
    4. Reporting Agent - Generates executive summary
    """

    def __init__(self, client):
        self.client = client
        self.context = None  # Store context for external access

    @staticmethod
    def _extract_field(pattern: str, text: str, cast_type):
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            return None
        raw = match.group(1).strip()
        try:
            return cast_type(raw)
        except (TypeError, ValueError):
            return None

    def _parse_audit_input(self, audit_input: str):
        supplier_name = self._extract_field(r"Supplier Name:\s*(.+)", audit_input, str)
        emissions = self._extract_field(r"Annual CO2 Emissions:\s*([0-9]+(?:\.[0-9]+)?)", audit_input, float)
        violations = self._extract_field(r"Regulatory Violations:\s*(\d+)", audit_input, int)

        if supplier_name is None or emissions is None or violations is None:
            raise ValueError("Could not parse supplier_name/emissions/violations from audit input.")

        return supplier_name, emissions, violations

    def generate_content(self, audit_input: str):
        """
        Orchestrates the complete multi-agent audit pipeline with
        three blockchain integration points:

        Agent Pipeline:
          MonitorAgent -> CalculationAgent -> [BLOCKCHAIN: Score Anchor]
                       -> PolicyAgent      -> [BLOCKCHAIN: HITL Decision]
                       -> ReportingAgent   -> [BLOCKCHAIN: Report Hash]
        """
        # Parse input
        supplier_name, emissions, violations = self._parse_audit_input(audit_input)

        print(f"\n{'='*60}")
        print(f"MULTI-AGENT PIPELINE WITH BLOCKCHAIN INTEGRATION")
        print(f"{'='*60}\n")

        blockchain = get_blockchain_client()

        # Track blockchain TX IDs for chain of custody
        score_anchor_tx = None
        hitl_decision_tx = None
        report_hash_tx = None

        try:
            # ---------------------------------------------------------- #
            #  STEP 1: Create agents
            # ---------------------------------------------------------- #
            print("[1/7] Creating agents...")
            monitor_agent = create_monitor_agent(self.client)
            calculation_agent = create_calculation_agent()
            policy_agent = create_policy_agent(self.client)
            reporting_agent = create_reporting_agent(self.client)
            print("  > All 4 agents created\n")

            # Initialize shared context
            context = AgentContext()
            context.state["supplier_name"] = supplier_name
            context.state["emissions"] = emissions
            context.state["violations"] = violations
            self.context = context

            query = (
                f"Conduct a comprehensive ESG audit for supplier: {supplier_name}. "
                f"Emissions: {emissions} tons CO2. Violations: {violations}."
            )

            # ---------------------------------------------------------- #
            #  STEP 2: MonitorAgent — External risk detection
            # ---------------------------------------------------------- #
            print("[2/7] MonitorAgent: Searching for external risks...")
            monitor_output = monitor_agent.execute(context, query)
            print(f"  > Monitor complete (external risks captured)\n")

            # ---------------------------------------------------------- #
            #  STEP 3: CalculationAgent — Deterministic scoring
            # ---------------------------------------------------------- #
            print("[3/7] CalculationAgent: Computing ESG risk score...")
            calc_output = calculation_agent.execute(context, monitor_output)
            risk_score = context.state.get("ESG_RISK_SCORE", 0)
            classification = context.state.get("risk_classification", "Unknown")
            print(f"  > Score: {risk_score:.2f} | Class: {classification}\n")

            # ---------------------------------------------------------- #
            #  BLOCKCHAIN POINT 1: Score Anchoring
            # ---------------------------------------------------------- #
            print("[  ] BLOCKCHAIN: Anchoring score on-chain...")
            try:
                score_result = blockchain.anchor_score(
                    supplier_name=supplier_name,
                    risk_score=risk_score,
                    classification=classification,
                    emissions=emissions,
                    violations=violations,
                    emissions_score=context.state.get("emissions_score", 0),
                    violations_score=context.state.get("violations_score", 0),
                    external_risk_score=context.state.get("external_risk_score", 0),
                )
                score_anchor_tx = score_result.get("tx_id")
                context.state["score_anchor_tx"] = score_anchor_tx
                context.state["score_data_hash"] = score_result.get("data_hash", "")
            except Exception as e:
                print(f"  [Blockchain] Score anchor failed: {e}")
            print()

            # ---------------------------------------------------------- #
            #  STEP 4: PolicyAgent — HITL enforcement
            # ---------------------------------------------------------- #
            print("[4/7] PolicyAgent: Enforcing compliance policy...")
            policy_output = policy_agent.execute(context, calc_output)
            policy_outcome = context.state.get("policy_decision_outcome", {})
            requires_hitl = policy_outcome.get("human_approval_required", False)
            decision = policy_outcome.get("decision", "N/A")
            reason = policy_outcome.get("reason", "")
            action = policy_outcome.get("recommended_action", "")
            hitl_str = "HITL REQUIRED" if requires_hitl else "Auto-approved"
            print(f"  > Decision: {decision} | {hitl_str}\n")

            # ---------------------------------------------------------- #
            #  BLOCKCHAIN POINT 2: HITL Decision Ledger
            # ---------------------------------------------------------- #
            print("[  ] BLOCKCHAIN: Recording HITL decision on-chain...")
            try:
                hitl_result = blockchain.record_hitl_decision(
                    supplier_name=supplier_name,
                    score_anchor_tx=score_anchor_tx,
                    approved=not requires_hitl,  # Auto-approved if no HITL needed
                    risk_score=risk_score,
                    decision=decision,
                    reason=reason,
                    recommended_action=action,
                )
                hitl_decision_tx = hitl_result.get("tx_id")
                context.state["hitl_decision_tx"] = hitl_decision_tx
            except Exception as e:
                print(f"  [Blockchain] HITL decision recording failed: {e}")
            print()

            # ---------------------------------------------------------- #
            #  STEP 5: ReportingAgent — Executive summary
            # ---------------------------------------------------------- #
            print("[5/7] ReportingAgent: Generating executive report...")
            # Enrich context with blockchain references before reporting
            context.state["blockchain_score_tx"] = score_anchor_tx or "N/A"
            context.state["blockchain_hitl_tx"] = hitl_decision_tx or "N/A"

            report_output = reporting_agent.execute(context, policy_output)
            report_text = report_output
            print(f"  > Report generated ({len(report_text)} chars)\n")

            # If report is empty or too short, use fallback
            if not report_text or len(report_text) < 200:
                print("  > Generating fallback report...")
                report_text = self._generate_fallback_report(
                    supplier_name, emissions, violations, context.state
                )

            # ---------------------------------------------------------- #
            #  BLOCKCHAIN POINT 3: Report Hash Registry
            # ---------------------------------------------------------- #
            print("[6/7] BLOCKCHAIN: Registering report hash on-chain...")
            try:
                report_result = blockchain.register_report_hash(
                    supplier_name=supplier_name,
                    score_anchor_tx=score_anchor_tx,
                    hitl_decision_tx=hitl_decision_tx,
                    report_text=report_text,
                )
                report_hash_tx = report_result.get("tx_id")
                context.state["report_hash_tx"] = report_hash_tx
                context.state["report_verification_code"] = report_result.get("verification_code", "")
            except Exception as e:
                print(f"  [Blockchain] Report hash registration failed: {e}")

            # ---------------------------------------------------------- #
            #  STEP 7: Carbon Credit Scoring
            # ---------------------------------------------------------- #
            print("[7/8] CreditAgent: Calculating carbon credits...")
            credit_result = calculate_carbon_credits({
                "supplier_name": supplier_name,
                "risk_score": risk_score,
            })
            context.state["carbon_credits"] = credit_result
            print(f"  > Credits earned: {credit_result['total_credits']} | "
                  f"New total: {credit_result['new_total']} | "
                  f"Badges: {credit_result['badges_earned']}\n")

            # ---------------------------------------------------------- #
            #  STEP 8: Complete
            # ---------------------------------------------------------- #
            print(f"\n[8/8] Pipeline complete!")
            print(f"\n{'='*60}")
            print(f"CHAIN OF CUSTODY (Algorand Testnet)")
            print(f"{'='*60}")
            print(f"  1. Score Anchor TX:   {(score_anchor_tx or 'N/A')[:30]}...")
            print(f"  2. HITL Decision TX:  {(hitl_decision_tx or 'N/A')[:30]}...")
            print(f"  3. Report Hash TX:    {(report_hash_tx or 'N/A')[:30]}...")
            print(f"{'='*60}\n")

            return CoordinatorResponse(text=report_text)

        except Exception as e:
            print(f"\n  Error in pipeline: {e}")
            import traceback
            traceback.print_exc()

            # Fallback to deterministic report
            risk_data = calculate_carbon_score(emissions, violations)
            policy_data = enforce_policy_hitl(risk_data["risk_score"], supplier_name)

            fallback_report = self._generate_fallback_report(
                supplier_name, emissions, violations,
                {"ESG_RISK_SCORE": risk_data["risk_score"],
                 "risk_classification": risk_data["classification"],
                 "policy_decision_outcome": policy_data}
            )
            
            return CoordinatorResponse(text=fallback_report)

    def _generate_fallback_report(self, supplier_name, emissions, violations, state):
        """Generate comprehensive fallback report"""
        
        risk_score = state.get("ESG_RISK_SCORE", 0)
        classification = state.get("risk_classification", "Unknown")
        policy_outcome = state.get("policy_decision_outcome", {})
        external_risks = state.get("external_risks", "No external risk data available")
        
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Determine emissions analysis
        if emissions > 10000:
            emissions_analysis = f"The annual emissions of {emissions} tons CO2 are significantly high, indicating substantial environmental impact. This level requires immediate attention and aggressive reduction strategies."
        elif emissions > 5000:
            emissions_analysis = f"The annual emissions of {emissions} tons CO2 are moderately high, suggesting room for improvement in environmental practices and carbon reduction initiatives."
        else:
            emissions_analysis = f"The annual emissions of {emissions} tons CO2 are within acceptable ranges, though continuous monitoring and improvement efforts are recommended."
        
        # Determine violations analysis
        if violations >= 5:
            violations_analysis = f"With {violations} regulatory violations, this supplier demonstrates a concerning pattern of non-compliance. This poses significant legal and reputational risks that require immediate remediation."
        elif violations >= 2:
            violations_analysis = f"The {violations} regulatory violations indicate compliance challenges that need to be addressed through enhanced monitoring and corrective action plans."
        else:
            violations_analysis = f"With {violations} violation(s), the supplier shows relatively good compliance, though maintaining vigilance is essential."
        
        # Determine recommendations based on risk
        if classification == 'Critical Risk':
            recommendations = """   • IMMEDIATE: Suspend new orders pending compliance review
   • SHORT-TERM: Conduct on-site audit within 30 days
   • MEDIUM-TERM: Implement mandatory emissions reduction plan
   • LONG-TERM: Quarterly compliance reviews for 12 months
   • MONITORING: Weekly status reports until risk is mitigated
   • ESCALATION: Executive approval required for contract renewal"""
            final_rec = "Given the critical risk level, we recommend immediate suspension of new business pending a comprehensive compliance review. The supplier must demonstrate concrete improvement plans before partnership continuation can be considered."
        elif classification == 'Moderate Risk':
            recommendations = """   • SHORT-TERM: Request detailed emissions reduction roadmap
   • MEDIUM-TERM: Implement enhanced monitoring protocols
   • LONG-TERM: Bi-annual compliance audits
   • MONITORING: Monthly progress reports
   • SUPPORT: Provide ESG best practices guidance
   • REVIEW: Re-evaluate partnership terms in 6 months"""
            final_rec = "The partnership may continue with enhanced monitoring and clear improvement milestones. The supplier should provide quarterly progress reports on emissions reduction and compliance improvements."
        else:
            recommendations = """   • SHORT-TERM: Maintain current monitoring protocols
   • MEDIUM-TERM: Encourage continuous improvement initiatives
   • LONG-TERM: Annual compliance reviews
   • MONITORING: Standard quarterly reports
   • RECOGNITION: Consider for preferred supplier status
   • COLLABORATION: Share sustainability best practices"""
            final_rec = "The supplier demonstrates acceptable ESG performance. Continue partnership with standard monitoring protocols and encourage ongoing sustainability improvements."
        
        decision = policy_outcome.get('decision', 'N/A')
        reason = policy_outcome.get('reason', 'N/A')
        action = policy_outcome.get('recommended_action', 'N/A')
        human_approval = policy_outcome.get('human_approval_required', False)
        
        report_text = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUPPLIER AUDIT REPORT - {supplier_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. EXECUTIVE SUMMARY
   • Supplier Name: {supplier_name}
   • Audit Date: {current_date}
   • Risk Classification: {classification}
   • Overall Risk Score: {risk_score:.2f} / 1.00
   • Audit Status: {'CRITICAL' if risk_score >= 0.7 else 'FLAGGED' if risk_score >= 0.4 else 'PASSED'}

   Summary: This comprehensive ESG audit evaluates {supplier_name} across 
   environmental impact, regulatory compliance, and external risk factors. 
   The supplier has been classified as {classification} based on 
   emissions data and violation history. {reason}

2. ENVIRONMENTAL IMPACT ASSESSMENT
   • Annual CO2 Emissions: {emissions} tons
   • Emissions Score: {state.get('emissions_score', 'N/A')} / 1.00
   • Industry Benchmark: {'Above average' if emissions > 5000 else 'Within normal range'}
   
   Analysis: {emissions_analysis}

3. REGULATORY COMPLIANCE REVIEW
   • Regulatory Violations: {violations} incidents
   • Violations Score: {state.get('violations_score', 'N/A')} / 1.00
   • Compliance Status: {'CRITICAL' if violations >= 5 else 'NON-COMPLIANT' if violations >= 2 else 'COMPLIANT'}
   
   Analysis: {violations_analysis}

4. EXTERNAL RISK FACTORS
   {external_risks}

5. POLICY ENFORCEMENT OUTCOME
   • Decision: {decision}
   • Human Approval Required: {'YES' if human_approval else 'NO'}
   • Recommended Action: {action}
   
   Rationale: {reason}

6. RISK MITIGATION RECOMMENDATIONS
{recommendations}

7. FINAL RECOMMENDATION
   {final_rec} Key success metrics include: emissions reduction 
   trajectory, violation remediation progress, and implementation of recommended 
   corrective actions. Regular monitoring will ensure continuous improvement and 
   alignment with our ESG standards.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Report Generated: {current_date}
Report Source: Deterministic Fallback
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REFERENCES & RESOURCES:
• ESG Reporting Standards: https://www.globalreporting.org/standards/
• Carbon Disclosure Project: https://www.cdp.net/
• Science Based Targets Initiative: https://sciencebasedtargets.org/
• EPA Compliance Resources: https://www.epa.gov/compliance
• ISO 14001 Environmental Management: https://www.iso.org/iso-14001-environmental-management.html

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return report_text



def create_root_coordinator(client):
    """
    Creates the Root Coordinator with 3-point blockchain integration.

    Pipeline:
    1. MonitorAgent:      External risk detection (Tavily Search)
    2. CalculationAgent:  Deterministic ESG risk scoring
       -> BLOCKCHAIN:     Score Anchor (immutable score + data hash)
    3. PolicyAgent:       HITL compliance enforcement
       -> BLOCKCHAIN:     HITL Decision Ledger (wallet-signed proof)
    4. ReportingAgent:    Executive audit report
       -> BLOCKCHAIN:     Report Hash Registry (SHA-256 tamper detection)
    """

    return RootCoordinator(client)

