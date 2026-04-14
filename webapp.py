"""Web interface for Carbon Footprint Optimization Engine (CfoE)."""

from __future__ import annotations

import asyncio
from queue import Queue
import csv
import json
import threading
from textwrap import wrap
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from docx import Document
from reportlab.lib.pagesizes import A4

from agents.calculation_agent import calculate_carbon_score
from agents.policy_agent import enforce_policy_hitl
from agents.registry_agent import validate_registry_id, get_entity_info
from agents.trajectory_agent import calculate_trajectory, check_compliance_trajectory
from agents.credit_agent import calculate_carbon_credits, get_supplier_credits, get_supplier_credit_history, get_leaderboard
from orchestrators.root_coordinator import create_root_coordinator

from config.groq_config import get_groq_client
from blockchain_client import get_blockchain_client
from carbon_token_manager import get_token_manager

try:
    from groq import Groq
except ImportError:  # pragma: no cover
    Groq = None


BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
STATIC_DIR = WEB_DIR / "static"
DATA_DIR = BASE_DIR / "data"
HISTORY_PATH = DATA_DIR / "audit_history.json"
PENDING_PATH = DATA_DIR / "pending_approvals.json"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_CSV_PATH = OUTPUT_DIR / "audits_master.csv"

lock = threading.Lock()
log_queue = Queue()
active_websockets: List[WebSocket] = []

def broadcast_log_sync(log_msg: Dict[str, Any]) -> None:
    """Put log in queue and try to send to active websockets"""
    log_queue.put(log_msg)
    # Create async task to broadcast
    for ws in active_websockets[:]:
        try:
            # Use asyncio to send if event loop is running
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(ws.send_json(log_msg))
        except Exception:
            pass


class AuditRequest(BaseModel):
    supplier_name: str = Field(min_length=2, max_length=120)
    emissions: float = Field(ge=0)
    violations: int = Field(ge=0, le=500)
    notes: str = Field(default="", max_length=1000)
    sector: str = Field(default="default")  # Phase 1: Sector-specific targets
    production_volume: float = Field(default=None, ge=0)  # Phase 2: Normalized metrics
    production_unit: str = Field(default="tonne")  # Phase 2: Unit for normalization
    registry_id: str = Field(default="")  # Phase 3: Entity registry
    baseline_year: int = Field(default=2023)  # Phase 1: Pro-rata calculation
    target_year: int = Field(default=2027)  # Phase 1: Pro-rata calculation


class AuditResponse(BaseModel):
    job_id: str
    audit_id: str
    timestamp: str
    supplier_name: str
    emissions: float
    violations: int
    notes: str
    risk_score: float
    classification: str
    emissions_score: float
    violations_score: float
    external_risk_score: float
    policy_decision: str
    human_approval_required: bool
    policy_reason: str
    recommended_action: str
    report_text: str
    report_source: str
    download_links: Dict[str, str]
    status: str  # "completed" or "pending_approval"


class ApprovalRequest(BaseModel):
    audit_id: str
    decision: str  # "approve" or "reject"
    approver_name: str = Field(min_length=2, max_length=100)
    approval_notes: str = Field(default="", max_length=500)


app = FastAPI(
    title="CfoE Dashboard API",
    description="Interactive interface for supplier ESG risk audits.",
    version="1.0.0",
)


@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)

    # Prevent stale frontend assets during local development.
    if request.url.path == "/" or request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    return response

# Ensure static output directory exists before mount.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Mount simulator directory
SIMULATOR_DIR = BASE_DIR / "simulator"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")


@lru_cache(maxsize=1)
def get_client():
    load_dotenv()
    api_key = __import__("os").getenv("GROQ_API_KEY")
    if not api_key or Groq is None:
        return None
    try:
        return Groq(api_key=api_key)
    except Exception:
        return None


def ensure_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not HISTORY_PATH.exists():
        HISTORY_PATH.write_text("[]", encoding="utf-8")
    
    if not PENDING_PATH.exists():
        PENDING_PATH.write_text("[]", encoding="utf-8")

    if not OUTPUT_CSV_PATH.exists():
        with OUTPUT_CSV_PATH.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=[
                    "audit_id",
                    "timestamp",
                    "supplier_name",
                    "emissions",
                    "violations",
                    "risk_score",
                    "classification",
                    "policy_decision",
                    "human_approval_required",
                    "report_source",
                ],
            )
            writer.writeheader()


def load_history() -> List[Dict[str, Any]]:
    ensure_storage()
    with lock:
        try:
            content = HISTORY_PATH.read_text(encoding="utf-8").strip() or "[]"
            data = json.loads(content)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []


def save_history(history: List[Dict[str, Any]]) -> None:
    with lock:
        HISTORY_PATH.write_text(json.dumps(history, indent=2), encoding="utf-8")


def load_pending() -> List[Dict[str, Any]]:
    ensure_storage()
    with lock:
        try:
            content = PENDING_PATH.read_text(encoding="utf-8").strip() or "[]"
            data = json.loads(content)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []


def save_pending(pending: List[Dict[str, Any]]) -> None:
    with lock:
        PENDING_PATH.write_text(json.dumps(pending, indent=2), encoding="utf-8")


def make_audit_prompt(req: AuditRequest) -> str:
    return f"""
Conduct a comprehensive ESG audit for the following supplier:

Supplier Name: {req.supplier_name}
Annual CO2 Emissions: {req.emissions} tons
Regulatory Violations: {req.violations}
Additional Notes: {req.notes or 'N/A'}

Please provide a complete risk assessment and recommendations.
"""


def build_fallback_report(req: AuditRequest, risk_data: Dict[str, Any], policy_data: Dict[str, Any], blockchain_data: Optional[Dict[str, Any]] = None, credit_data: Optional[Dict[str, Any]] = None) -> str:
    report = (
        "Executive Summary\n"
        f"Supplier: {req.supplier_name}\n"
        f"Risk Score: {risk_data['risk_score']} ({risk_data['classification']})\n\n"
        "Key Findings\n"
        f"- Emissions contribution score: {risk_data['emissions_score']}\n"
        f"- Violations contribution score: {risk_data['violations_score']}\n"
        f"- Policy decision: {policy_data['decision']}\n\n"
        "Recommended Action\n"
        f"{policy_data['recommended_action']}\n"
    )
    
    # carbon credits
    if credit_data:
        report += "\n\n" + "="*60 + "\n"
        report += "CARBON CREDITS AWARDED\n"
        report += "="*60 + "\n\n"
        report += f"Base Credits: {credit_data.get('credits_earned', 0)}\n"
        if credit_data.get('streak_bonus', 0) > 0:
            report += f"Streak Bonus: +{credit_data['streak_bonus']}\n"
        if credit_data.get('improvement_bonus', 0) > 0:
            report += f"Improvement Bonus: +{credit_data['improvement_bonus']}\n"
        report += f"Total Earned: {credit_data.get('total_credits', 0)}\n"
        report += f"New Balance: {credit_data.get('new_total', 0)} credits\n"
        if credit_data.get('badges_earned'):
            report += f"Badges: {', '.join(credit_data['badges_earned'])}\n"
    
    # blockchain verification 
    if blockchain_data:
        report += "\n\n" + "="*60 + "\n"
        report += "BLOCKCHAIN VERIFICATION\n"
        report += "="*60 + "\n\n"
        
        if blockchain_data.get("score_tx"):
            report += f"Score Anchor TX: {blockchain_data['score_tx']}\n"
        if blockchain_data.get("score_hash"):
            report += f"Input Data Hash: {blockchain_data['score_hash']}\n"
        if blockchain_data.get("report_hash"):
            report += f"Report SHA-256: {blockchain_data['report_hash']}\n"
        if blockchain_data.get("verification_code"):
            report += f"Verification Code: {blockchain_data['verification_code']}\n"
        if blockchain_data.get("report_tx"):
            report += f"Report Hash TX: {blockchain_data['report_tx']}\n"
        if blockchain_data.get("credit_tx"):
            report += f"Carbon Credits TX: {blockchain_data['credit_tx']}\n"
        if blockchain_data.get("hitl_tx"):
            report += f"HITL Decision TX: {blockchain_data['hitl_tx']}\n"
        
        report += f"\nOn-Chain Status: {'✓ Verified' if blockchain_data.get('on_chain') else '✗ Local Only'}\n"
        report += "\nTo verify this report:\n"
        report += "1. Calculate SHA-256 hash of this report text\n"
        report += "2. Compare with the Report SHA-256 above\n"
        report += "3. Check transactions on Algorand Explorer:\n"
        report += "   https://testnet.algoexplorer.io/tx/[TX_ID]\n"
    
    return report


def run_audit(req: AuditRequest) -> Dict[str, Any]:
    broadcast_log_sync({"type": "info", "message": f"Starting audit for {req.supplier_name}..."})
    
    # Check if wallet is connected
    bc = get_blockchain_client()
    if not bc.wallet_connected:
        broadcast_log_sync({"type": "warning", "message": "⚠ Wallet not connected - transactions will be stored locally"})
    
    broadcast_log_sync({"type": "info", "message": "[1/6] Calculating ESG risk scores..."})
    
    # Calculate audit date for pro-rata
    from datetime import datetime
    audit_date = datetime.now()
    
    risk_data = calculate_carbon_score(
        emissions=req.emissions, 
        violations=req.violations,
        sector=req.sector,
        production_volume=req.production_volume,
        audit_date=audit_date
    )
    
    broadcast_log_sync({"type": "success", "message": f"✓ Risk Score: {risk_data['risk_score']} ({risk_data['classification']}) - Sector: {risk_data['sector']}"})
    
    # Blockchain: Anchor score
    bc = get_blockchain_client()
    if bc.wallet_connected and bc.address:
        broadcast_log_sync({"type": "info", "message": f"[Blockchain] Using wallet: {bc.address[:16]}..."})
    else:
        broadcast_log_sync({"type": "info", "message": "[Blockchain] Wallet not connected - storing locally"})
    
    try:
        score_anchor = bc.anchor_score(
            supplier_name=req.supplier_name,
            risk_score=risk_data["risk_score"],
            classification=risk_data["classification"],
            emissions=req.emissions,
            violations=req.violations,
            emissions_score=risk_data["emissions_score"],
            violations_score=risk_data["violations_score"],
            external_risk_score=risk_data.get("external_risk_score", 0.0)
        )
    except Exception as e:
        broadcast_log_sync({"type": "error", "message": f"✗ Score anchor exception: {str(e)}"})
        score_anchor = None
    
    if score_anchor:
        tx_id = score_anchor.get('tx_id') or score_anchor.get('local_id', 'LOCAL')
        broadcast_log_sync({"type": "success", "message": f"✓ Score anchored on blockchain: {tx_id[:20]}..."})
    else:
        broadcast_log_sync({"type": "error", "message": "✗ Score anchor failed - returned None"})
        score_anchor = {"local_id": "FALLBACK", "on_chain": False}
    
    broadcast_log_sync({"type": "info", "message": "[2/6] Enforcing policy rules..."})
    policy_data = enforce_policy_hitl(risk_score=risk_data["risk_score"], supplier_name=req.supplier_name)
    broadcast_log_sync({"type": "success", "message": f"✓ Policy Decision: {policy_data['decision']}"})

    # Prepare blockchain data for report
    blockchain_data_for_report = {
        "score_tx": score_anchor.get("tx_id") or score_anchor.get("local_id") if score_anchor else None,
        "score_hash": score_anchor.get("data_hash") if score_anchor else None,
        "on_chain": score_anchor.get("on_chain", False) if score_anchor else False
    }

    report_source = "deterministic-fallback"
    report_text = build_fallback_report(req, risk_data, policy_data, blockchain_data_for_report, None)
    external_risk_score = 0.0

    client = get_client()
    if client is not None:
        try:
            broadcast_log_sync({"type": "info", "message": "[3/6] Generating AI report with multi-agent pipeline..."})
            coordinator = create_root_coordinator(client)
            response = coordinator.generate_content(make_audit_prompt(req))
            report_text = response.text
            
            # Extract external_risk_score from coordinator context if available
            if hasattr(coordinator, 'context') and 'external_risk_score' in coordinator.context.state:
                external_risk_score = coordinator.context.state.get('external_risk_score', 0.0)
            
            report_source = "groq-llama"
            broadcast_log_sync({"type": "success", "message": "✓ AI report generated successfully"})
        except Exception as e:
            broadcast_log_sync({"type": "warning", "message": f"⚠ AI report failed, using fallback: {str(e)[:100]}"})
            report_source = "deterministic-fallback"
    else:
        broadcast_log_sync({"type": "warning", "message": "⚠ AI client unavailable, using deterministic report"})

    # Blockchain: Register report hash
    broadcast_log_sync({"type": "info", "message": "[4/6] Recording report hash on blockchain..."})
    try:
        report_hash_record = bc.register_report_hash(
            supplier_name=req.supplier_name,
            score_anchor_tx=score_anchor.get("tx_id") if score_anchor else None,
            hitl_decision_tx=None,
            report_text=report_text
        )
    except Exception as e:
        broadcast_log_sync({"type": "error", "message": f"✗ Report hash exception: {str(e)}"})
        report_hash_record = None
    
    if report_hash_record:
        broadcast_log_sync({"type": "success", "message": f"✓ Report hash: {report_hash_record['verification_code']}"})
        # Update blockchain data for report
        blockchain_data_for_report["report_hash"] = report_hash_record.get("report_hash")
        blockchain_data_for_report["verification_code"] = report_hash_record.get("verification_code")
        blockchain_data_for_report["report_tx"] = report_hash_record.get("tx_id") or report_hash_record.get("local_id")
    else:
        broadcast_log_sync({"type": "error", "message": "✗ Report hash failed - returned None"})
        report_hash_record = {"local_id": "FALLBACK", "on_chain": False}

    broadcast_log_sync({"type": "info", "message": "[5/6] Finalizing audit results..."})
    result = {
        "job_id": f"JOB-{uuid4().hex[:8].upper()}",
        "audit_id": f"AUD-{uuid4().hex[:10].upper()}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "supplier_name": req.supplier_name,
        "emissions": req.emissions,
        "violations": req.violations,
        "notes": req.notes,
        "sector": risk_data.get("sector", "General Industry"),
        "sector_key": risk_data.get("sector_key", "default"),
        "production_volume": req.production_volume,
        "production_unit": req.production_unit,
        "registry_id": req.registry_id,
        "emissions_intensity": risk_data.get("emissions_intensity"),
        "prorata_progress": risk_data.get("prorata_progress", 0.0),
        "baseline_year": req.baseline_year,
        "target_year": req.target_year,
        "risk_score": risk_data["risk_score"],
        "classification": risk_data["classification"],
        "emissions_score": risk_data["emissions_score"],
        "violations_score": risk_data["violations_score"],
        "external_risk_score": external_risk_score,
        "policy_decision": policy_data["decision"],
        "human_approval_required": policy_data["human_approval_required"],
        "policy_reason": policy_data["reason"],
        "recommended_action": policy_data["recommended_action"],
        "report_text": report_text,
        "report_source": report_source,
        "download_links": {},
        "status": "pending_approval" if policy_data["human_approval_required"] else "completed",
        "blockchain": {
            "score_tx": score_anchor.get("tx_id") or score_anchor.get("local_id") if score_anchor else None,
            "score_hash": score_anchor.get("data_hash") if score_anchor else None,
            "report_tx": report_hash_record.get("tx_id") or report_hash_record.get("local_id") if report_hash_record else None,
            "report_hash": report_hash_record.get("report_hash") if report_hash_record else None,
            "verification_code": report_hash_record.get("verification_code") if report_hash_record else None,
            "on_chain": score_anchor.get("on_chain", False) if score_anchor else False
        }
    }

    # ── Carbon Credit Scoring (runs on every audit) ───────────────
    broadcast_log_sync({"type": "info", "message": "[6/6] Calculating carbon credits..."})
    credit_data_for_report = None
    try:
        credit_result = calculate_carbon_credits(result)
        result["carbon_credits"] = credit_result
        
        # Record credits on blockchain
        bc = get_blockchain_client()
        credit_record = bc.record_carbon_credits(
            supplier_name=req.supplier_name,
            audit_id=result["audit_id"],
            credits_earned=credit_result["credits_earned"],
            badges_earned=credit_result["badges_earned"],
            total_credits=credit_result["new_total"],
            esg_score=risk_data["risk_score"],
            streak_bonus=credit_result["streak_bonus"],
            improvement_bonus=credit_result["improvement_bonus"],
        )
        
        # Add credit transaction to blockchain data
        blockchain_data_for_report["credit_tx"] = credit_record.get("tx_id") or credit_record.get("local_id")
        credit_data_for_report = credit_result
        
        # Regenerate report with all blockchain and credit details
        report_text = build_fallback_report(req, risk_data, policy_data, blockchain_data_for_report, credit_data_for_report)
        
        broadcast_log_sync({
            "type": "success",
            "message": (
                f"✓ Credits: +{credit_result['total_credits']} "
                f"(total: {credit_result['new_total']}) | "
                f"Badges: {credit_result['badges_earned']}"
            ),
        })
    except Exception as e:
        broadcast_log_sync({"type": "warning", "message": f"⚠ Credit calculation failed: {str(e)[:80]}"})
        result["carbon_credits"] = None
        # Regenerate report without credits
        report_text = build_fallback_report(req, risk_data, policy_data, blockchain_data_for_report, None)

    # HITL Workflow Pause: If human approval required, save to pending queue
    if policy_data["human_approval_required"]:
        broadcast_log_sync({"type": "warning", "message": "🚨 CRITICAL RISK - Audit paused for human approval"})
        result["status"] = "pending_approval"
        result["approval_status"] = "pending"
        result["approver_name"] = None
        result["approval_notes"] = None
        result["approval_timestamp"] = None
        result["blockchain"]["hitl_tx"] = None
    else:
        broadcast_log_sync({"type": "success", "message": f"✓ Audit complete for {req.supplier_name}"})
    
    return result


def _write_pdf(pdf_path: Path, result: Dict[str, Any]) -> None:
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, topMargin=0.75*inch, bottomMargin=0.75*inch, leftMargin=0.75*inch, rightMargin=0.75*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0d7c66'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    story.append(Paragraph(f"CfoE Audit Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Summary Table with word wrapping
    summary_data = [
        ['Audit ID:', Paragraph(result['audit_id'], styles['Normal'])],
        ['Job ID:', Paragraph(result['job_id'], styles['Normal'])],
        ['Timestamp:', Paragraph(result['timestamp'][:19], styles['Normal'])],
        ['Supplier:', Paragraph(result['supplier_name'], styles['Normal'])],
        ['Emissions:', Paragraph(f"{result['emissions']} tons CO2", styles['Normal'])],
        ['Violations:', Paragraph(str(result['violations']), styles['Normal'])],
        ['Risk Score:', Paragraph(f"{result['risk_score']} ({result['classification']})", styles['Normal'])],
    ]
    
    summary_table = Table(summary_data, colWidths=[1.5*inch, 4.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Policy Section
    policy_style = ParagraphStyle('PolicyHeading', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#0d7c66'))
    story.append(Paragraph("Policy Enforcement", policy_style))
    story.append(Spacer(1, 0.1*inch))
    
    policy_data = [
        ['Decision:', Paragraph(result['policy_decision'], styles['Normal'])],
        ['Reason:', Paragraph(result['policy_reason'], styles['Normal'])],
        ['Recommended Action:', Paragraph(result['recommended_action'], styles['Normal'])],
    ]
    
    policy_table = Table(policy_data, colWidths=[1.5*inch, 4.5*inch])
    policy_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(policy_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Executive Report
    story.append(Paragraph("Executive Report", policy_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Format report text with proper line breaks and structure
    report_style = ParagraphStyle(
        'ReportBody', 
        parent=styles['BodyText'], 
        fontSize=9, 
        leading=13,
        alignment=TA_LEFT,
        leftIndent=0,
        rightIndent=0,
        spaceAfter=6
    )
    
    # Split report into lines and format properly
    report_lines = result['report_text'].split('\n')
    for line in report_lines:
        line = line.strip()
        if line:
            # Replace special characters that might cause issues
            line = line.replace('━', '-')
            line = line.replace('•', '*')
            
            # Check if it's a section header (numbered or all caps)
            if line and (line[0].isdigit() or line.isupper() or line.startswith('---')):
                header_style = ParagraphStyle(
                    'SectionHeader',
                    parent=styles['Heading3'],
                    fontSize=10,
                    textColor=colors.HexColor('#0d7c66'),
                    spaceAfter=4,
                    spaceBefore=8,
                    fontName='Helvetica-Bold'
                )
                story.append(Paragraph(line, header_style))
            else:
                story.append(Paragraph(line, report_style))
    
    doc.build(story)


def _write_docx(docx_path: Path, result: Dict[str, Any]) -> None:
    doc = Document()
    doc.add_heading(f"CfoE Audit Report - {result['audit_id']}", level=1)
    doc.add_paragraph(f"Job ID: {result['job_id']}")
    doc.add_paragraph(f"Timestamp: {result['timestamp']}")
    doc.add_paragraph(f"Supplier: {result['supplier_name']}")
    doc.add_paragraph(f"Emissions: {result['emissions']}")
    doc.add_paragraph(f"Violations: {result['violations']}")
    doc.add_paragraph(f"Risk Score: {result['risk_score']} ({result['classification']})")
    doc.add_paragraph(f"Policy Decision: {result['policy_decision']}")
    doc.add_paragraph(f"Policy Reason: {result['policy_reason']}")
    doc.add_paragraph(f"Recommended Action: {result['recommended_action']}")
    doc.add_heading("Executive Report", level=2)
    doc.add_paragraph(result["report_text"])
    doc.save(str(docx_path))


def export_audit_files(result: Dict[str, Any]) -> Dict[str, str]:
    ensure_storage()

    safe_stem = result["audit_id"].lower()
    job_dir = OUTPUT_DIR / result["job_id"].lower()
    job_dir.mkdir(parents=True, exist_ok=True)

    txt_path = job_dir / f"{safe_stem}.txt"
    docx_path = job_dir / f"{safe_stem}.docx"
    pdf_path = job_dir / f"{safe_stem}.pdf"

    # Save raw report text for verification
    txt_path.write_text(result["report_text"], encoding="utf-8")

    # Try to create PDF, but don't fail if it errors
    pdf_created = False
    try:
        _write_pdf(pdf_path, result)
        pdf_created = True
    except Exception as e:
        print(f"[WARNING] PDF generation failed: {e}")
        print("[INFO] Continuing without PDF export")

    # Try to create DOCX
    docx_created = False
    try:
        _write_docx(docx_path, result)
        docx_created = True
    except Exception as e:
        print(f"[WARNING] DOCX generation failed: {e}")
        print("[INFO] Continuing without DOCX export")

    with lock:
        with OUTPUT_CSV_PATH.open("a", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=[
                    "audit_id",
                    "timestamp",
                    "supplier_name",
                    "emissions",
                    "violations",
                    "risk_score",
                    "classification",
                    "policy_decision",
                    "human_approval_required",
                    "report_source",
                ],
            )
            writer.writerow(
                {
                    "audit_id": result["audit_id"],
                    "timestamp": result["timestamp"],
                    "supplier_name": result["supplier_name"],
                    "emissions": result["emissions"],
                    "violations": result["violations"],
                    "risk_score": result["risk_score"],
                    "classification": result["classification"],
                    "policy_decision": result["policy_decision"],
                    "human_approval_required": result["human_approval_required"],
                    "report_source": result["report_source"],
                }
            )

    links = {"txt": f"/outputs/{result['job_id'].lower()}/{txt_path.name}"}
    if pdf_created:
        links["pdf"] = f"/api/audits/{result['audit_id']}/pdf/download"
    if docx_created:
        links["docx"] = f"/outputs/{result['job_id'].lower()}/{docx_path.name}"
    
    return links


@app.on_event("startup")
def startup_event() -> None:
    ensure_storage()


@app.get("/")
def serve_index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/simulator")
def serve_simulator() -> FileResponse:
    """Serve simulator dashboard on same port"""
    return FileResponse(SIMULATOR_DIR / "dashboard.html")


@app.post("/api/audit", response_model=AuditResponse)
async def create_audit(payload: AuditRequest) -> Dict[str, Any]:
    # Phase 2: Validate registry ID if provided
    if payload.registry_id and payload.registry_id.strip():
        validation = validate_registry_id(payload.registry_id)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail=validation["error"])
    
    try:
        # Clear log queue before starting
        while not log_queue.empty():
            log_queue.get()
        
        result = run_audit(payload)
        result["download_links"] = export_audit_files(result)
    except Exception as exc:
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n[ERROR] Audit failed with exception:")
        print(error_trace)
        raise HTTPException(status_code=500, detail=f"Audit failed: {str(exc)}") from exc

    # If human approval required, save to pending queue instead of history
    if result.get("human_approval_required", False):
        pending = load_pending()
        pending.insert(0, result)
        save_pending(pending)
    else:
        # Auto-approved audits go directly to history
        history = load_history()
        history.insert(0, result)
        save_history(history[:500])
    
    return result


@app.get("/api/audits")
def list_audits(limit: int = 100) -> Dict[str, Any]:
    history = load_history()
    return {"items": history[:max(1, min(limit, 500))], "count": len(history)}


@app.get("/api/approvals")
def list_pending_approvals() -> Dict[str, Any]:
    """Get all audits pending human approval"""
    pending = load_pending()
    return {"items": pending, "count": len(pending)}


@app.post("/api/approvals/{audit_id}/approve")
def approve_audit(audit_id: str, approval: ApprovalRequest) -> Dict[str, Any]:
    """Approve a pending audit and move it to history"""
    if approval.audit_id != audit_id:
        raise HTTPException(status_code=400, detail="Audit ID mismatch")
    
    if approval.decision != "approve":
        raise HTTPException(status_code=400, detail="Use /reject endpoint for rejections")
    
    pending = load_pending()
    audit = next((x for x in pending if x.get("audit_id") == audit_id), None)
    
    if audit is None:
        raise HTTPException(status_code=404, detail="Pending audit not found")
    
    # Blockchain: Record HITL decision
    bc = get_blockchain_client()
    hitl_record = bc.record_hitl_decision(
        supplier_name=audit["supplier_name"],
        score_anchor_tx=audit.get("blockchain", {}).get("score_tx"),
        approved=True,
        risk_score=audit["risk_score"],
        decision=audit["policy_decision"],
        reason=audit["policy_reason"],
        recommended_action=audit["recommended_action"]
    )
    
    # Update audit with approval info
    audit["status"] = "completed"
    audit["approval_status"] = "approved"
    audit["approver_name"] = approval.approver_name
    audit["approval_notes"] = approval.approval_notes
    audit["approval_timestamp"] = datetime.now(timezone.utc).isoformat()
    if "blockchain" not in audit:
        audit["blockchain"] = {}
    audit["blockchain"]["hitl_tx"] = hitl_record.get("tx_id") or hitl_record.get("local_id")
    
    # Remove from pending and add to history
    pending = [x for x in pending if x.get("audit_id") != audit_id]
    save_pending(pending)
    
    history = load_history()
    history.insert(0, audit)
    save_history(history[:500])
    
    return {"status": "approved", "audit": audit}


@app.post("/api/approvals/{audit_id}/reject")
def reject_audit(audit_id: str, approval: ApprovalRequest) -> Dict[str, Any]:
    """Reject a pending audit"""
    if approval.audit_id != audit_id:
        raise HTTPException(status_code=400, detail="Audit ID mismatch")
    
    if approval.decision != "reject":
        raise HTTPException(status_code=400, detail="Use /approve endpoint for approvals")
    
    pending = load_pending()
    audit = next((x for x in pending if x.get("audit_id") == audit_id), None)
    
    if audit is None:
        raise HTTPException(status_code=404, detail="Pending audit not found")
    
    # Blockchain: Record HITL decision
    bc = get_blockchain_client()
    hitl_record = bc.record_hitl_decision(
        supplier_name=audit["supplier_name"],
        score_anchor_tx=audit.get("blockchain", {}).get("score_tx"),
        approved=False,
        risk_score=audit["risk_score"],
        decision=audit["policy_decision"],
        reason=audit["policy_reason"],
        recommended_action=audit["recommended_action"]
    )
    
    # Update audit with rejection info
    audit["status"] = "rejected"
    audit["approval_status"] = "rejected"
    audit["approver_name"] = approval.approver_name
    audit["approval_notes"] = approval.approval_notes
    audit["approval_timestamp"] = datetime.now(timezone.utc).isoformat()
    if "blockchain" not in audit:
        audit["blockchain"] = {}
    audit["blockchain"]["hitl_tx"] = hitl_record.get("tx_id") or hitl_record.get("local_id")
    
    # Remove from pending and add to history (with rejected status)
    pending = [x for x in pending if x.get("audit_id") != audit_id]
    save_pending(pending)
    
    history = load_history()
    history.insert(0, audit)
    save_history(history[:500])
    
    return {"status": "rejected", "audit": audit}


@app.delete("/api/audits")
def clear_audits() -> Dict[str, Any]:
    save_history([])
    return {"status": "ok"}


@app.delete("/api/approvals")
def clear_pending_approvals() -> Dict[str, Any]:
    """Clear all pending approvals"""
    save_pending([])
    return {"status": "ok"}


@app.get("/api/metrics")
def metrics() -> Dict[str, Any]:
    history = load_history()
    if not history:
        return {
            "total_audits": 0,
            "avg_risk_score": 0,
            "critical_rate": 0,
            "classifications": {"Low Risk": 0, "Moderate Risk": 0, "Critical Risk": 0},
        }

    total = len(history)
    avg_score = sum(item["risk_score"] for item in history) / total
    critical = sum(1 for item in history if item["classification"] == "Critical Risk")
    counts = {"Low Risk": 0, "Moderate Risk": 0, "Critical Risk": 0}
    for item in history:
        counts[item["classification"]] = counts.get(item["classification"], 0) + 1

    return {
        "total_audits": total,
        "avg_risk_score": round(avg_score, 3),
        "critical_rate": round((critical / total) * 100, 1),
        "classifications": counts,
    }


@app.get("/api/audits/{audit_id}/pdf/view")
def view_pdf(audit_id: str) -> FileResponse:
    history = load_history()
    item = next((x for x in history if x.get("audit_id") == audit_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Audit not found")

    job_id = item.get("job_id", "")
    if not job_id:
        raise HTTPException(status_code=404, detail="Job export not found")

    pdf_name = f"{audit_id.lower()}.pdf"
    pdf_path = OUTPUT_DIR / job_id.lower() / pdf_name
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")

    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={pdf_name}"},
    )


@app.get("/api/audits/{audit_id}/pdf/download")
def download_pdf(audit_id: str) -> FileResponse:
    history = load_history()
    item = next((x for x in history if x.get("audit_id") == audit_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Audit not found")

    job_id = item.get("job_id", "")
    if not job_id:
        raise HTTPException(status_code=404, detail="Job export not found")

    pdf_name = f"{audit_id.lower()}.pdf"
    pdf_path = OUTPUT_DIR / job_id.lower() / pdf_name
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")

    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        filename=pdf_name,
        headers={"Content-Disposition": f"attachment; filename={pdf_name}"},
    )


@app.get("/api/blockchain/status")
def blockchain_status() -> Dict[str, Any]:
    """Get blockchain connection status and statistics"""
    bc = get_blockchain_client()
    tm = get_token_manager()
    
    # Force refresh connection to ensure we have latest wallet info
    if not bc.connected:
        bc.connect()
    
    # Re-check wallet connection from .env if not already connected
    if not bc.wallet_connected:
        import os
        from algosdk import account
        env_key = os.getenv("ALGORAND_PRIVATE_KEY")
        if env_key:
            try:
                bc.address = account.address_from_private_key(env_key)
                bc.private_key = env_key
                bc.wallet_connected = True
            except Exception:
                pass
    
    balance_info = bc.get_balance()
    history = bc.get_audit_history()
    
    # Show full address if wallet connected, otherwise show N/A
    display_address = bc.address if bc.wallet_connected else "N/A"
    
    # Get token information
    total_issued = sum(r["carbon_credits"] for r in tm.issued_credits)
    total_retired = sum(r["carbon_credits"] for r in tm.retired_credits)
    
    # Get token balance (returns dict with tokens and carbon_credits)
    token_balance_info = tm.get_credit_balance(bc.address) if bc.address else {"tokens": 0.0, "carbon_credits": 0.0}
    
    # Determine overall connection status
    is_connected = bc.wallet_connected  # Show connected if wallet is connected
    network_status = "Algorand Testnet" if bc.connected else "Offline"
    
    return {
        "connected": is_connected,
        "address": display_address,
        "balance": balance_info.get("balance_algo", 0),
        "network": network_status,
        "wallet": _wallet_state,
        "wallet_connected": bc.wallet_connected,
        "token_id": tm.carbon_credit_asset_id,
        "token_balance": token_balance_info.get("tokens", 0),
        "token_supply": total_issued - total_retired,
        "credits_issued": total_issued,
        "credits_retired": total_retired,
    }



@app.get("/api/registry/validate/{registry_id}")
def validate_registry(registry_id: str) -> Dict[str, Any]:
    """Validate entity registry ID"""
    return validate_registry_id(registry_id)


@app.get("/api/registry/entity/{registry_id}")
def get_entity(registry_id: str) -> Dict[str, Any]:
    """Get entity information by registry ID"""
    entity = get_entity_info(registry_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@app.get("/api/trajectory/{supplier_name}")
def get_trajectory(supplier_name: str) -> Dict[str, Any]:
    """Get multi-year compliance trajectory for a supplier"""
    history = load_history()
    return calculate_trajectory(supplier_name, history)


@app.get("/api/trajectory/{supplier_name}/compliance")
def get_compliance_trajectory(supplier_name: str, baseline_year: int = 2023, target_year: int = 2027) -> Dict[str, Any]:
    """Check if supplier is on track to meet compliance goals"""
    history = load_history()
    return check_compliance_trajectory(supplier_name, history, baseline_year, target_year)


# ── Carbon Credit endpoints ──────────────────────────────────────

@app.get("/api/credits/{supplier_id}")
def get_credits(supplier_id: str) -> Dict[str, Any]:
    """Return the full carbon credit history for a supplier."""
    data = get_supplier_credits(supplier_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Supplier not found in credit ledger")
    return data


@app.get("/api/credits/{supplier_id}/history")
def get_credit_history(supplier_id: str) -> Dict[str, Any]:
    """Return rich credit history for charts and timelines:
    credits per audit (sparkline), badge timeline, streak history,
    and ESG score trend."""
    data = get_supplier_credit_history(supplier_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Supplier not found in credit ledger")
    return data


@app.get("/api/leaderboard")
def leaderboard() -> Dict[str, Any]:
    """Return all suppliers sorted by total credits descending,
    with their badges and latest ESG score."""
    board = get_leaderboard()
    return {"items": board, "count": len(board)}


# ── Wallet endpoints ──────────────────────────────────────────────

_wallet_state: Dict[str, Any] = {"connected": False, "address": None}


class WalletConnectRequest(BaseModel):
    address: str = Field(min_length=1, max_length=128)


@app.get("/api/wallet/status")
def wallet_status() -> Dict[str, Any]:
    """Return the current wallet connection state."""
    return _wallet_state


@app.post("/api/wallet/connect")
def wallet_connect(payload: WalletConnectRequest) -> Dict[str, Any]:
    """Register a wallet address from the frontend."""
    _wallet_state["connected"] = True
    _wallet_state["address"] = payload.address
    
    # Connect wallet to blockchain client
    bc = get_blockchain_client()
    bc.set_wallet_address(payload.address)
    
    return {"status": "ok", "address": payload.address}


@app.post("/api/wallet/disconnect")
def wallet_disconnect() -> Dict[str, Any]:
    """Clear the wallet connection."""
    _wallet_state["connected"] = False
    _wallet_state["address"] = None
    
    # Disconnect wallet from blockchain client
    bc = get_blockchain_client()
    bc.disconnect_wallet()
    
    return {"status": "ok"}


# ── Carbon Credit Token endpoints ─────────────────────────────────

class TokenCreateRequest(BaseModel):
    total_credits: int = Field(default=10_000_000, ge=1000)
    unit_name: str = Field(default="CCT", max_length=8)
    asset_name: str = Field(default="CfoE Carbon Credit", max_length=32)


class CreditIssueRequest(BaseModel):
    recipient_address: str = Field(min_length=58, max_length=58)
    amount: float = Field(gt=0)
    reason: str = Field(max_length=200)
    audit_id: Optional[str] = None


class TokenOptInRequest(BaseModel):
    asset_id: int = Field(gt=0)


class CreditRetireRequest(BaseModel):
    amount: float = Field(gt=0)
    reason: str = Field(max_length=200)
    beneficiary: str = Field(max_length=100)


class CreditTransferRequest(BaseModel):
    recipient_address: str = Field(min_length=58, max_length=58)
    amount: float = Field(gt=0)
    reason: str = Field(max_length=200)
    audit_id: Optional[str] = None


class NFTCreateRequest(BaseModel):
    supplier_name: str
    audit_id: str
    risk_score: float
    classification: str
    emissions: float
    metadata_url: str = ""


@app.post("/api/tokens/optin")
def optin_to_token(payload: TokenOptInRequest) -> Dict[str, Any]:
    """Opt-in the server wallet to receive carbon credit tokens."""
    tm = get_token_manager()
    bc = get_blockchain_client()
    
    if not bc.connected or not bc.wallet_connected:
        raise HTTPException(status_code=400, detail="Wallet not connected")
    
    try:
        tx_id = tm.optin_to_asset(payload.asset_id)
        
        if tx_id:
            return {
                "status": "success",
                "tx_id": tx_id,
                "message": f"Successfully opted-in to asset {payload.asset_id}"
            }
        else:
            raise HTTPException(status_code=500, detail="Opt-in transaction failed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Opt-in failed: {str(e)}")


@app.post("/api/tokens/create")
def create_carbon_token(payload: TokenCreateRequest) -> Dict[str, Any]:
    """Create a new carbon credit token (ASA)."""
    tm = get_token_manager()
    asset_id = tm.create_carbon_credit_token(
        total_credits=payload.total_credits,
        unit_name=payload.unit_name,
        asset_name=payload.asset_name,
    )
    
    if asset_id:
        return {
            "status": "success",
            "asset_id": asset_id,
            "message": f"Carbon credit token created: {asset_id}"
        }
    else:
        raise HTTPException(status_code=500, detail="Token creation failed")


@app.post("/api/tokens/issue")
def issue_carbon_credits(payload: CreditIssueRequest) -> Dict[str, Any]:
    """Issue carbon credits to a recipient."""
    tm = get_token_manager()
    
    if not tm.carbon_credit_asset_id:
        raise HTTPException(
            status_code=400,
            detail="No carbon credit token exists yet. Create one first via POST /api/tokens/create"
        )
    
    tx_id = tm.issue_credits(
        recipient_address=payload.recipient_address,
        carbon_credits=payload.amount,
        reason=payload.reason,
        audit_id=payload.audit_id,
    )
    
    if tx_id:
        return {
            "status": "success",
            "tx_id": tx_id,
            "amount": payload.amount,
            "message": f"Issued {payload.amount} tons CO2eq"
        }
    else:
        raise HTTPException(status_code=500, detail="Credit issuance failed")


@app.post("/api/tokens/retire")
def retire_carbon_credits(payload: CreditRetireRequest) -> Dict[str, Any]:
    """Retire (burn) carbon credits permanently."""
    tm = get_token_manager()
    tx_id = tm.retire_credits(
        carbon_credits=payload.amount,
        reason=payload.reason,
        beneficiary=payload.beneficiary,
    )
    
    if tx_id:
        return {
            "status": "success",
            "tx_id": tx_id,
            "amount": payload.amount,
            "message": f"Retired {payload.amount} tons CO2eq permanently"
        }
    else:
        raise HTTPException(status_code=500, detail="Credit retirement failed")


@app.post("/api/tokens/transfer")
def transfer_carbon_credits(payload: CreditTransferRequest) -> Dict[str, Any]:
    """Transfer carbon credits to another address."""
    tm = get_token_manager()

    if not tm.carbon_credit_asset_id:
        raise HTTPException(
            status_code=400,
            detail="No carbon credit token exists yet. Create one first via POST /api/tokens/create"
        )

    tx_id = tm.transfer_credits(
        recipient_address=payload.recipient_address,
        carbon_credits=payload.amount,
        reason=payload.reason,
        audit_id=payload.audit_id,
    )
    
    if tx_id:
        return {
            "status": "success",
            "tx_id": tx_id,
            "amount": payload.amount,
            "recipient": payload.recipient_address,
            "message": f"Transferred {payload.amount} tons CO2eq"
        }
    else:
        raise HTTPException(status_code=500, detail="Credit transfer failed")


@app.post("/api/tokens/nft/create")
def create_audit_nft(payload: NFTCreateRequest) -> Dict[str, Any]:
    """Create an audit certificate NFT."""
    tm = get_token_manager()
    asset_id = tm.create_audit_certificate_nft(
        supplier_name=payload.supplier_name,
        audit_id=payload.audit_id,
        risk_score=payload.risk_score,
        classification=payload.classification,
        emissions=payload.emissions,
        metadata_url=payload.metadata_url,
    )
    
    if asset_id:
        return {
            "status": "success",
            "asset_id": asset_id,
            "message": f"Audit certificate NFT created: {asset_id}"
        }
    else:
        raise HTTPException(status_code=500, detail="NFT creation failed")


@app.get("/api/tokens/balance/{address}")
def get_token_balance(address: str) -> Dict[str, Any]:
    """Get carbon credit balance for an address."""
    tm = get_token_manager()
    balance = tm.get_credit_balance(address)
    
    return {
        "address": address,
        "balance": balance,
        "asset_id": tm.carbon_credit_asset_id,
    }


@app.get("/api/tokens/summary")
def get_token_summary() -> Dict[str, Any]:
    """Get summary of all token operations."""
    tm = get_token_manager()
    
    total_issued = sum(r.get("carbon_credits", 0) for r in tm.issued_credits)
    total_retired = sum(r.get("carbon_credits", 0) for r in tm.retired_credits)
    
    return {
        "asset_id": tm.carbon_credit_asset_id,
        "total_issued": total_issued,
        "total_retired": total_retired,
        "circulating_supply": total_issued - total_retired,
        "issuance_count": len(tm.issued_credits),
        "retirement_count": len(tm.retired_credits),
        "nft_count": len(tm.audit_nfts),
        "issued_credits": tm.issued_credits,
        "retired_credits": tm.retired_credits,
        "audit_nfts": tm.audit_nfts,
    }


# Store active WebSocket connections
active_websockets: List[WebSocket] = []

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    try:
        while True:
            # Check for new log messages
            if not log_queue.empty():
                log_msg = log_queue.get()
                await websocket.send_json(log_msg)
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        if websocket in active_websockets:
            active_websockets.remove(websocket)
    except Exception:
        if websocket in active_websockets:
            active_websockets.remove(websocket)


# ── Simulator Integration ─────────────────────────────────────────────

from simulator.simulator import (
    state as sim_state,
    manager as sim_manager,
    _build_snapshot,
    _current_shift,
    _compute_esg_score,
    PROCESSES,
    VIOLATION_TYPES,
    TICK_INTERVAL,
    MAX_HISTORY
)


@app.websocket("/ws/simulator")
async def ws_simulator(websocket: WebSocket) -> None:
    await sim_manager.connect(websocket)
    await websocket.send_json(_build_snapshot())
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        sim_manager.disconnect(websocket)


@app.post("/simulation/start")
async def start_simulation() -> Dict[str, Any]:
    sim_state.running = True
    return {"status": "running"}


@app.post("/simulation/stop")
async def stop_simulation() -> Dict[str, Any]:
    sim_state.running = False
    return {"status": "stopped"}


@app.post("/simulation/reset")
async def reset_simulation() -> Dict[str, Any]:
    sim_state.reset()
    await sim_manager.broadcast(_build_snapshot())
    return {"status": "reset"}


@app.post("/simulation/trigger-spike")
async def trigger_spike() -> Dict[str, Any]:
    sim_state.spike_active = True
    sim_state.spike_remaining = 6
    sim_state.spike_multiplier = round(__import__("random").uniform(1.4, 2.1), 2)
    return {"status": "spike_triggered", "multiplier": sim_state.spike_multiplier, "ticks": 6}


@app.post("/simulation/trigger-violation")
async def trigger_violation() -> Dict[str, Any]:
    entry = {"type": "EPA_FINE", "severity": "HIGH", "description": "EPA emission limit fine", "fine": 250_000, "id": f"VIO-{uuid4().hex[:8].upper()}", "timestamp": datetime.now(timezone.utc).isoformat()}
    sim_state.active_violations.append(entry)
    if len(sim_state.active_violations) > 10:
        sim_state.active_violations = sim_state.active_violations[-10:]
    sim_state.cumulative_violations += 3
    sim_state.esg_score = _compute_esg_score()
    await sim_manager.broadcast(_build_snapshot())
    return {"status": "violation_injected", "violation": entry}


@app.get("/simulation/snapshot")
async def snapshot() -> Dict[str, Any]:
    return _build_snapshot()


@app.post("/audit/run")
async def run_audit_from_simulator() -> Dict[str, Any]:
    snap = _build_snapshot()
    payload = {"supplier_name": snap["supplier_name"], "emissions": snap["estimated_annual_co2"], "violations": snap["cumulative_violations"], "notes": f"Simulator audit", "sector": "default"}
    try:
        result = run_audit(AuditRequest(**payload))
        result["download_links"] = export_audit_files(result)
        if result.get("human_approval_required", False):
            pending = load_pending()
            pending.insert(0, result)
            save_pending(pending)
        else:
            history = load_history()
            history.insert(0, result)
            save_history(history[:500])
        sim_state.last_audit_result = result
        await sim_manager.broadcast({"type": "audit_result", "result": result})
        return result
    except Exception as exc:
        error_msg = {"type": "audit_error", "error": str(exc)}
        await sim_manager.broadcast(error_msg)
        return error_msg


async def _simulation_loop() -> None:
    import random
    while True:
        if not sim_state.running:
            await asyncio.sleep(0.5)
            continue
        sim_state.tick_count += 1
        shift_name, shift_mult = _current_shift()
        tick_co2 = 0.0
        for proc in PROCESSES:
            noise = random.gauss(1.0, 0.06)
            daily_rate = proc["base_co2"] * shift_mult * noise
            if sim_state.spike_active:
                daily_rate *= sim_state.spike_multiplier
            per_tick = daily_rate / (86400 / TICK_INTERVAL)
            sim_state.process_emissions[proc["name"]] = daily_rate
            tick_co2 += per_tick
        sim_state.total_co2_today += tick_co2
        if sim_state.spike_active:
            sim_state.spike_remaining -= 1
            if sim_state.spike_remaining <= 0:
                sim_state.spike_active = False
                sim_state.spike_multiplier = 1.0
        else:
            if random.random() < 0.08:
                sim_state.spike_active = True
                sim_state.spike_remaining = random.randint(3, 8)
                sim_state.spike_multiplier = round(random.uniform(1.4, 2.1), 2)
        if random.random() < 0.05:
            viol = random.choice(VIOLATION_TYPES)
            entry = {**viol, "id": f"VIO-{uuid4().hex[:8].upper()}", "timestamp": datetime.now(timezone.utc).isoformat()}
            sim_state.active_violations.append(entry)
            if len(sim_state.active_violations) > 10:
                sim_state.active_violations = sim_state.active_violations[-10:]
            sim_state.cumulative_violations += 1
        sim_state.esg_score = _compute_esg_score()
        snap = _build_snapshot()
        sim_state.history.append(snap)
        if len(sim_state.history) > MAX_HISTORY:
            sim_state.history = sim_state.history[-MAX_HISTORY:]
        await sim_manager.broadcast(snap)
        await asyncio.sleep(TICK_INTERVAL)


@app.on_event("startup")
async def startup_simulator() -> None:
    asyncio.create_task(_simulation_loop())
