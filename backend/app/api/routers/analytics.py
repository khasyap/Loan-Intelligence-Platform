from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List
from decimal import Decimal

from backend.app.database.connection import get_db
from backend.app.models.entities import (
    Applicant, LoanApplication, LoanProduct, Decision,
    AffordabilityCheck, Document, Disbursement
)

router = APIRouter(prefix="/analytics", tags=["Analytics & KPIs"])

@router.get("/executive", response_model=Dict[str, Any])
def get_executive_kpis(db: Session = Depends(get_db)):
    """Executive Dashboard KPIs: Portfolio volume, status breakdown, volumes and rates."""
    total_applicants = db.query(Applicant).count()
    total_applications = db.query(LoanApplication).count()

    approved_count = db.query(Decision).filter(Decision.decision_status == "APPROVED").count()
    rejected_count = db.query(Decision).filter(Decision.decision_status == "REJECT").count()
    manual_review_count = db.query(Decision).filter(Decision.decision_status == "MANUAL_REVIEW").count()
    pending_info_count = db.query(Decision).filter(Decision.decision_status == "PENDING_INFORMATION").count()

    total_requested_principal = db.query(func.sum(LoanApplication.requested_principal)).scalar() or Decimal("0.00")
    
    # Approved principal
    approved_principal = db.query(func.sum(LoanApplication.requested_principal)).join(
        Decision, Decision.application_id == LoanApplication.application_id
    ).filter(Decision.decision_status == "APPROVED").scalar() or Decimal("0.00")

    # Disbursed principal
    disbursed_principal = db.query(func.sum(Disbursement.disbursed_amount)).scalar() or Decimal("0.00")

    approval_rate = (approved_count / total_applications * 100) if total_applications > 0 else 0.0
    rejection_rate = (rejected_count / total_applications * 100) if total_applications > 0 else 0.0

    return {
        "total_applicants": total_applicants,
        "total_applications": total_applications,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "manual_review_count": manual_review_count,
        "pending_info_count": pending_info_count,
        "approval_rate": round(approval_rate, 2),
        "rejection_rate": round(rejection_rate, 2),
        "total_requested_principal": float(total_requested_principal),
        "total_approved_principal": float(approved_principal),
        "total_disbursed_principal": float(disbursed_principal)
    }


@router.get("/risk", response_model=Dict[str, Any])
def get_risk_analytics(db: Session = Depends(get_db)):
    """Risk & Compliance Dashboard: Credit score, DTI, and FOIR distributions."""
    # 1. Credit Score distribution
    applicants = db.query(Applicant.credit_score).all()
    score_bins = {"<600 (Subprime)": 0, "600-699 (Near Prime)": 0, "700-799 (Prime)": 0, "800+ (Super Prime)": 0}
    for (score,) in applicants:
        if score < 600:
            score_bins["<600 (Subprime)"] += 1
        elif score < 700:
            score_bins["600-699 (Near Prime)"] += 1
        elif score < 800:
            score_bins["700-799 (Prime)"] += 1
        else:
            score_bins["800+ (Super Prime)"] += 1

    # 2. DTI Distribution
    aff_checks = db.query(AffordabilityCheck.debt_to_income_ratio, AffordabilityCheck.fixed_obligation_ratio).all()
    dti_bins = {"0-25% (Low)": 0, "25-45% (Moderate)": 0, "45-60% (High)": 0, ">60% (Severe)": 0}
    foir_bins = {"0-35% (Comfortable)": 0, "35-50% (Standard)": 0, "50-65% (Stretched)": 0, ">65% (Critical)": 0}

    for dti, foir in aff_checks:
        d_val = float(dti)
        f_val = float(foir)
        if d_val < 25.0:
            dti_bins["0-25% (Low)"] += 1
        elif d_val < 45.0:
            dti_bins["25-45% (Moderate)"] += 1
        elif d_val < 60.0:
            dti_bins["45-60% (High)"] += 1
        else:
            dti_bins[">60% (Severe)"] += 1

        if f_val < 35.0:
            foir_bins["0-35% (Comfortable)"] += 1
        elif f_val < 50.0:
            foir_bins["35-50% (Standard)"] += 1
        elif f_val < 65.0:
            foir_bins["50-65% (Stretched)"] += 1
        else:
            foir_bins[">65% (Critical)"] += 1

    # 3. Decision Reason Codes
    reason_counts = db.query(
        Decision.decision_reason_code, func.count(Decision.decision_id)
    ).group_by(Decision.decision_reason_code).all()

    return {
        "credit_score_distribution": [{"range": k, "count": v} for k, v in score_bins.items()],
        "dti_distribution": [{"range": k, "count": v} for k, v in dti_bins.items()],
        "foir_distribution": [{"range": k, "count": v} for k, v in foir_bins.items()],
        "reason_code_distribution": [{"code": r[0], "count": r[1]} for r in reason_counts]
    }


@router.get("/operations", response_model=Dict[str, Any])
def get_operations_analytics(db: Session = Depends(get_db)):
    """Operations Funnel: Application lifecycle stages and document verification backlog."""
    # Lifecycle funnel
    status_counts = db.query(
        LoanApplication.application_status, func.count(LoanApplication.application_id)
    ).group_by(LoanApplication.application_status).all()

    # Document verification breakdown
    doc_counts = db.query(
        Document.verification_status, func.count(Document.document_id)
    ).group_by(Document.verification_status).all()

    return {
        "lifecycle_funnel": [{"status": s[0], "count": s[1]} for s in status_counts],
        "document_verification_summary": [{"status": d[0], "count": d[1]} for d in doc_counts]
    }

