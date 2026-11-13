from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from decimal import Decimal
import datetime

from backend.app.database.connection import get_db
from backend.app.models.entities import (
    Disbursement, DisbursementEvent, LoanApplication, Decision, Document, AffordabilityCheck
)
from backend.app.services.security import require_role
from backend.app.services.lifecycle import evaluate_disbursement_prerequisites

router = APIRouter(prefix="/disbursements", tags=["Disbursement Payouts & Events"])

@router.get("", response_model=List[Dict[str, Any]])
def list_disbursements(db: Session = Depends(get_db)):
    """List completed and pending disbursements."""
    records = db.query(Disbursement).all()
    return [
        {
            "disbursement_id": d.disbursement_id,
            "application_id": d.application_id,
            "disbursed_amount": float(d.disbursed_amount),
            "disbursement_date": str(d.disbursement_date),
            "disbursement_status": d.disbursement_status,
            "bank_reference": d.bank_reference,
            "created_at": d.created_at
        } for d in records
    ]

@router.post("/{application_id}/check-eligibility", response_model=Dict[str, Any])
@router.get("/{application_id}/eligibility", response_model=Dict[str, Any])
def check_eligibility_gate(application_id: str, db: Session = Depends(get_db)):
    """
    Evaluates all strict prerequisite criteria before allowing loan disbursement:
    1. Approved decision exists
    2. All mandatory documents verified
    3. Affordability check passed
    4. Zero prior successful disbursement
    """
    app = db.query(LoanApplication).filter(LoanApplication.application_id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    decision = db.query(Decision).filter(Decision.application_id == application_id).order_by(Decision.decision_sequence.desc()).first()
    docs = db.query(Document).filter(Document.application_id == application_id).all()
    aff = db.query(AffordabilityCheck).filter(AffordabilityCheck.application_id == application_id).first()
    existing_disbs = db.query(Disbursement).filter(Disbursement.application_id == application_id).all()

    app_dict = {"application_id": app.application_id}
    dec_dict = {"decision_status": decision.decision_status} if decision else None
    doc_dicts = [{"verification_status": d.verification_status} for d in docs]
    aff_dict = {"affordability_status": aff.affordability_status} if aff else None
    disb_dicts = [{"application_id": d.application_id, "disbursement_status": d.disbursement_status} for d in existing_disbs]

    is_eligible, failure_reasons = evaluate_disbursement_prerequisites(
        app_dict, dec_dict, doc_dicts, aff_dict, disb_dicts
    )

    return {
        "application_id": application_id,
        "is_disbursement_eligible": is_eligible,
        "reasons": failure_reasons if not is_eligible else ["All disbursement prerequisites verified."]
    }

