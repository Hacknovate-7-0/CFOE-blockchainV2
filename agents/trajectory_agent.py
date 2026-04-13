"""
Trajectory Agent - Multi-year compliance trajectory tracking
"""

from datetime import datetime
from typing import List, Dict, Any

def get_historical_audits(supplier_name: str, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Get all historical audits for a supplier.
    
    Args:
        supplier_name: Name of the supplier
        history: Full audit history list
    
    Returns:
        List of audits for the supplier, sorted by timestamp (newest first)
    """
    supplier_audits = [
        audit for audit in history 
        if audit.get("supplier_name", "").lower() == supplier_name.lower()
    ]
    
    # Sort by timestamp descending
    supplier_audits.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return supplier_audits

def calculate_trajectory(supplier_name: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate multi-year compliance trajectory for a supplier.
    
    Args:
        supplier_name: Name of the supplier
        history: Full audit history list
    
    Returns:
        Trajectory analysis with trend, improvement rate, and predictions
    """
    audits = get_historical_audits(supplier_name, history)
    
    if len(audits) == 0:
        return {
            "supplier_name": supplier_name,
            "audit_count": 0,
            "trend": "no_data",
            "message": "No historical audits found for this supplier"
        }
    
    if len(audits) == 1:
        return {
            "supplier_name": supplier_name,
            "audit_count": 1,
            "trend": "insufficient_data",
            "current_score": audits[0].get("risk_score"),
            "current_classification": audits[0].get("classification"),
            "message": "Only one audit available. Need multiple audits for trajectory analysis."
        }
    
    # Extract risk scores and timestamps
    scores = []
    timestamps = []
    for audit in audits:
        if "risk_score" in audit and "timestamp" in audit:
            scores.append(audit["risk_score"])
            timestamps.append(audit["timestamp"])
    
    # Calculate trend
    if len(scores) >= 2:
        latest_score = scores[0]
        oldest_score = scores[-1]
        score_change = latest_score - oldest_score
        
        if score_change < -0.05:
            trend = "improving"
            trend_label = "📈 Improving"
        elif score_change > 0.05:
            trend = "deteriorating"
            trend_label = "📉 Deteriorating"
        else:
            trend = "stable"
            trend_label = "➡️ Stable"
        
        # Calculate average improvement rate per audit
        improvement_rate = -score_change / (len(scores) - 1)
        
        # Predict next audit score (simple linear projection)
        predicted_next_score = max(0.0, min(1.0, latest_score + improvement_rate))
        
        return {
            "supplier_name": supplier_name,
            "audit_count": len(audits),
            "trend": trend,
            "trend_label": trend_label,
            "latest_score": round(latest_score, 2),
            "oldest_score": round(oldest_score, 2),
            "score_change": round(score_change, 3),
            "improvement_rate": round(improvement_rate, 3),
            "predicted_next_score": round(predicted_next_score, 2),
            "audits": [
                {
                    "audit_id": a.get("audit_id"),
                    "timestamp": a.get("timestamp", "")[:10],
                    "risk_score": a.get("risk_score"),
                    "classification": a.get("classification"),
                    "emissions": a.get("emissions"),
                    "violations": a.get("violations")
                }
                for a in audits
            ]
        }
    
    return {
        "supplier_name": supplier_name,
        "audit_count": len(audits),
        "trend": "insufficient_data",
        "message": "Unable to calculate trajectory"
    }

def check_compliance_trajectory(supplier_name: str, history: List[Dict[str, Any]], 
                               baseline_year: int = 2023, target_year: int = 2027) -> Dict[str, Any]:
    """
    Check if supplier is on track to meet target year compliance goals.
    
    Args:
        supplier_name: Name of the supplier
        history: Full audit history list
        baseline_year: Baseline year (default 2023)
        target_year: Target year (default 2027)
    
    Returns:
        Compliance trajectory assessment
    """
    trajectory = calculate_trajectory(supplier_name, history)
    
    if trajectory.get("audit_count", 0) < 2:
        return {
            **trajectory,
            "on_track": None,
            "message": "Insufficient data to assess compliance trajectory"
        }
    
    # Calculate required improvement rate to reach low risk by target year
    current_year = datetime.now().year
    years_remaining = target_year - current_year
    
    if years_remaining <= 0:
        return {
            **trajectory,
            "on_track": False,
            "message": f"Target year {target_year} has passed"
        }
    
    latest_score = trajectory.get("latest_score", 0)
    improvement_rate = trajectory.get("improvement_rate", 0)
    
    # Assume low risk threshold is 0.30 (can be sector-specific)
    target_score = 0.30
    required_improvement = latest_score - target_score
    required_rate = required_improvement / years_remaining
    
    on_track = improvement_rate >= required_rate
    
    return {
        **trajectory,
        "on_track": on_track,
        "years_remaining": years_remaining,
        "target_score": target_score,
        "required_improvement": round(required_improvement, 3),
        "required_rate": round(required_rate, 3),
        "status": "✅ On Track" if on_track else "⚠️ Behind Schedule"
    }
