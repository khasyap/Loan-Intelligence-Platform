from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import datetime
import json

from backend.app.database.connection import get_db
from backend.app.models.entities import (
    Decision, DecisionOverrideHistory, DecisionRuleExecution, LoanApplication
)
from backend.app.services.security import require_role
from backend.app.rules_engine.engine import apply_underwriter_override

router = APIRouter(prefix="/decisions", tags=["Decisions & Underwriter Overrides"])

class UnderwriterOverrideRequest(BaseModel):
    new_status: str  # APPROVED or REJECT
    reason: str

@router.get("", response_model=List[Dict[str, Any]])
def list_decisions(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Query underwriting decisions with status filter."""
    q = db.query(Decision)
    if status:
        q = q.filter(Decision.decision_status == status)
    records = q.order_by(Decision.decision_timestamp.desc()).limit(limit).all()
    return [
        {
            "decision_id": d.decision_id,
            "application_id": d.application_id,
            "decision_status": d.decision_status,
            "decision_reason_code": d.decision_reason_code,
            "decision_explanation": d.decision_explanation,
            "risk_score": d.risk_score,
            "decision_timestamp": d.decision_timestamp,
            "reviewer_id": d.reviewer_id
        } for d in records
    ]

@router.get("/{decision_id}", response_model=Dict[str, Any])
def get_decision_detail(decision_id: str, db: Session = Depends(get_db)):
    """Retrieve decision record by decision_id or application_id."""
    decision = db.query(Decision).filter(
        (Decision.decision_id == decision_id) | (Decision.application_id == decision_id)
    ).order_by(Decision.decision_timestamp.desc()).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return {
        "decision_id": decision.decision_id,
        "application_id": decision.application_id,
        "decision_status": decision.decision_status,
        "decision_reason_code": decision.decision_reason_code,
        "decision_explanation": decision.decision_explanation,
        "risk_score": decision.risk_score,
        "rules_triggered": decision.rules_triggered,
        "decision_timestamp": decision.decision_timestamp,
        "reviewer_id": decision.reviewer_id,
        "rule_version": decision.rule_version
    }

@router.post("/{decision_id}/override", response_model=Dict[str, Any])
def submit_underwriter_override(
    decision_id: str,
    payload: UnderwriterOverrideRequest,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(require_role(["RISK_REVIEWER", "ADMIN"]))
):
    """
    Risk Reviewer or Admin applies an authorized human underwriter override,
    recording an immutable audit record in decision_override_history.
    """
    decision = db.query(Decision).filter(Decision.decision_id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    app = db.query(LoanApplication).filter(LoanApplication.application_id == decision.application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    dec_dict = {
        "decision_id": decision.decision_id,
        "application_id": decision.application_id,
        "decision_status": decision.decision_status
    }
    reviewer_name = user.get("name", "Senior Underwriter")
    override_log = apply_underwriter_override(dec_dict, reviewer_name, payload.new_status, payload.reason)

    # Persist decision update
    decision.decision_status = dec_dict["decision_status"]
    decision.decision_reason_code = dec_dict["decision_reason_code"]
    decision.decision_explanation = dec_dict["decision_explanation"]
    decision.reviewer_id = reviewer_name

    # Update application status
    app.application_status = payload.new_status

    # Record in history
    override_rec = DecisionOverrideHistory(**override_log)
    db.add(override_rec)
    db.commit()

    return {
        "decision_id": decision.decision_id,
        "application_id": decision.application_id,
        "overridden_status": decision.decision_status,
        "reviewer_id": reviewer_name,
        "reason": payload.reason,
        "override_id": override_log["override_id"]
    }

