"""
Calculation Agent - Deterministic ESG risk scoring with sector-specific targets
"""

from datetime import datetime
from config.agent_framework import DeterministicAgent

# Sector-specific emission intensity targets and thresholds
SECTOR_THRESHOLDS = {
    "aluminium": {
        "name": "Aluminium",
        "low": 0.30,
        "critical": 0.65,
        "baseline_intensity": 15.0,  # tCO2eq/tonne
        "target_intensity": 10.0
    },
    "refinery": {
        "name": "Refinery",
        "low": 0.35,
        "critical": 0.70,
        "baseline_intensity": 25.0,  # tCO2eq/MBBLS
        "target_intensity": 18.0
    },
    "petrochemicals": {
        "name": "Petrochemicals",
        "low": 0.40,
        "critical": 0.75,
        "baseline_intensity": 30.0,  # tCO2eq/tonne
        "target_intensity": 22.0
    },
    "textiles": {
        "name": "Textiles",
        "low": 0.25,
        "critical": 0.60,
        "baseline_intensity": 8.0,  # tCO2eq/tonne
        "target_intensity": 5.0
    },
    "default": {
        "name": "General Industry",
        "low": 0.40,
        "critical": 0.70,
        "baseline_intensity": 20.0,
        "target_intensity": 15.0
    }
}

def calculate_prorata_target(baseline_year: int = 2023, target_year: int = 2027, 
                            audit_date: datetime = None) -> float:
    """
    Calculate pro-rata progress ratio for mid-year audits.
    
    Args:
        baseline_year: Baseline year (default 2023)
        target_year: Target year (default 2027)
        audit_date: Date of audit (default: today)
    
    Returns:
        Progress ratio (0.0 to 1.0)
    """
    if audit_date is None:
        audit_date = datetime.now()
    
    baseline_date = datetime(baseline_year, 1, 1)
    target_date = datetime(target_year, 12, 31)
    
    if audit_date <= baseline_date:
        return 0.0
    elif audit_date >= target_date:
        return 1.0
    
    days_elapsed = (audit_date - baseline_date).days
    total_days = (target_date - baseline_date).days
    
    return days_elapsed / total_days

def calculate_carbon_score(emissions: float, violations: int, sector: str = "default",
                          production_volume: float = None, audit_date: datetime = None) -> dict:
    """
    Deterministic ESG risk score calculation with sector-specific targets.
    
    Args:
        emissions: Annual CO2 emissions in tons
        violations: Number of regulatory violations
        sector: Industry sector (aluminium, refinery, petrochemicals, textiles, default)
        production_volume: Production volume for normalized intensity calculation
        audit_date: Date of audit for pro-rata calculation
        
    Returns:
        dict with risk_score (0.0-1.0), classification, and sector info
    """
    
    # Get sector-specific thresholds
    sector_config = SECTOR_THRESHOLDS.get(sector.lower(), SECTOR_THRESHOLDS["default"])
    
    # Calculate pro-rata progress
    prorata_progress = calculate_prorata_target(audit_date=audit_date)
    
    # Calculate normalized emissions intensity if production volume provided
    emissions_intensity = None
    intensity_score = 0.0
    
    if production_volume and production_volume > 0:
        emissions_intensity = emissions / production_volume
        
        # Calculate expected intensity based on pro-rata progress
        baseline_intensity = sector_config["baseline_intensity"]
        target_intensity = sector_config["target_intensity"]
        expected_intensity = baseline_intensity - (baseline_intensity - target_intensity) * prorata_progress
        
        # Score based on deviation from expected intensity
        if emissions_intensity <= expected_intensity * 0.8:  # 20% better
            intensity_score = 0.05
        elif emissions_intensity <= expected_intensity:
            intensity_score = 0.15
        elif emissions_intensity <= expected_intensity * 1.2:  # 20% worse
            intensity_score = 0.30
        else:
            intensity_score = 0.50
    else:
        # Fallback to absolute emissions scoring
        if emissions < 1000:
            intensity_score = 0.1
        elif emissions < 3000:
            intensity_score = 0.25
        elif emissions < 5000:
            intensity_score = 0.35
        else:
            intensity_score = 0.5
    
    # Violations scoring (0-0.5 range)
    violations_score = min(violations * 0.1, 0.5)
    
    # Total risk score
    risk_score = intensity_score + violations_score
    
    # Classification using sector-specific thresholds
    if risk_score >= sector_config["critical"]:
        classification = "Critical Risk"
    elif risk_score >= sector_config["low"]:
        classification = "Moderate Risk"
    else:
        classification = "Low Risk"
    
    result = {
        "risk_score": round(risk_score, 2),
        "classification": classification,
        "emissions_score": round(intensity_score, 2),
        "violations_score": round(violations_score, 2),
        "sector": sector_config["name"],
        "sector_key": sector.lower(),
        "prorata_progress": round(prorata_progress, 3),
        "sector_thresholds": {
            "low": sector_config["low"],
            "critical": sector_config["critical"]
        }
    }
    
    if emissions_intensity is not None:
        result["emissions_intensity"] = round(emissions_intensity, 3)
        result["expected_intensity"] = round(expected_intensity, 3)
        result["baseline_intensity"] = baseline_intensity
        result["target_intensity"] = target_intensity
    
    return result

def calculate_carbon_score_logic(context):
    """Execute carbon score calculation from context"""
    emissions = context.state.get('emissions', 0)
    violations = context.state.get('violations', 0)
    external_risk_score = context.state.get('external_risk_score', 0.0)
    sector = context.state.get('sector', 'default')
    production_volume = context.state.get('production_volume')
    audit_date = context.state.get('audit_date')
    
    result = calculate_carbon_score(emissions, violations, sector, production_volume, audit_date)
    
    # Integrate external risk score (0.0-0.3 range)
    base_risk_score = result["risk_score"]
    adjusted_risk_score = min(1.0, base_risk_score + external_risk_score)
    
    # Reclassify based on adjusted score and sector thresholds
    sector_thresholds = result["sector_thresholds"]
    if adjusted_risk_score >= sector_thresholds["critical"]:
        adjusted_classification = "Critical Risk"
    elif adjusted_risk_score >= sector_thresholds["low"]:
        adjusted_classification = "Moderate Risk"
    else:
        adjusted_classification = "Low Risk"
    
    # Store in context
    context.state["base_risk_score"] = base_risk_score
    context.state["ESG_RISK_SCORE"] = adjusted_risk_score
    context.state["risk_classification"] = adjusted_classification
    context.state["emissions_score"] = result["emissions_score"]
    context.state["violations_score"] = result["violations_score"]
    context.state["external_risk_score"] = external_risk_score
    context.state["sector_info"] = result.get("sector")
    context.state["prorata_progress"] = result.get("prorata_progress", 0.0)
    
    # Build output message
    external_impact = "" if external_risk_score == 0 else f"\n  • External Risk Score: {external_risk_score:.2f}\n  • Base Score: {base_risk_score} → Adjusted Score: {adjusted_risk_score:.2f}"
    
    sector_info = f"\n  • Sector: {result['sector']}\n  • Pro-rata Progress: {result['prorata_progress']:.1%} (towards 2027 target)"
    
    intensity_info = ""
    if "emissions_intensity" in result:
        intensity_info = f"\n\nNormalized Metrics:\n  • Emissions Intensity: {result['emissions_intensity']:.2f} tCO2eq/unit\n  • Expected Intensity: {result['expected_intensity']:.2f} tCO2eq/unit\n  • Baseline (2023): {result['baseline_intensity']:.2f}\n  • Target (2027): {result['target_intensity']:.2f}"
    
    output = f"""ESG Risk Score Calculation Complete:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input Data:
  • Emissions: {emissions} tons
  • Violations: {violations}{sector_info}{external_impact}{intensity_info}

Risk Components:
  • Emissions Score: {result['emissions_score']}
  • Violations Score: {result['violations_score']}
  • External Risk Score: {external_risk_score:.2f}

Sector Thresholds:
  • Low Risk: < {sector_thresholds['low']}
  • Critical Risk: ≥ {sector_thresholds['critical']}

FINAL ESG RISK SCORE: {adjusted_risk_score:.2f}
CLASSIFICATION: {adjusted_classification}
{'🚨 CRITICAL - Requires Human Review' if adjusted_risk_score >= sector_thresholds['critical'] else '🟢 AUTO-APPROVED'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    
    return output

def create_calculation_agent(emissions: float = None, violations: int = None):
    """
    Creates the Calculation Agent with deterministic scoring
    
    Args:
        emissions: Annual CO2 emissions in tons (optional, can be in context)
        violations: Number of regulatory violations (optional, can be in context)
    """
    
    return DeterministicAgent(
        name="CalculationAgent",
        logic_fn=calculate_carbon_score_logic
    )
