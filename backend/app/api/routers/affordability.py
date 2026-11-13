from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel
from decimal import Decimal

from backend.app.database.connection import get_db
from backend.app.models.entities import AffordabilityCheck, LoanApplication
from backend.app.calculations.financial import (
    calculate_existing_dti, calculate_total_dti, calculate_foir,
    calculate_disposable_income, calculate_reducing_emi
)

router = APIRouter(prefix="/affordability", tags=["Affordability & Debt Calculations"])

class AffordabilityCalculateRequest(BaseModel):
    monthly_gross_income: float
    monthly_net_income: float
    existing_monthly_debt: float
    requested_principal: float
    annual_interest_rate: float
    requested_term_months: int

@router.get("/{application_id}", response_model=Dict[str, Any])
def get_application_affordability(application_id: str, db: Session = Depends(get_db)):
    """Retrieve persisted affordability assessment record for an application."""
    aff = db.query(AffordabilityCheck).filter(AffordabilityCheck.application_id == application_id).first()
    if not aff:
        raise HTTPException(status_code=404, detail="Affordability check not found")
    return {
        "affordability_check_id": aff.affordability_check_id,
        "application_id": aff.application_id,
        "monthly_net_income": float(aff.monthly_net_income),
        "existing_monthly_debt": float(aff.existing_monthly_debt),
        "proposed_monthly_emi": float(aff.proposed_monthly_emi),
        "debt_to_income_ratio": float(aff.debt_to_income_ratio),
        "fixed_obligation_ratio": float(aff.fixed_obligation_ratio),
        "disposable_income": float(aff.disposable_income),
        "affordability_status": aff.affordability_status,
        "assessment_timestamp": aff.assessment_timestamp
    }

@router.post("/calculate", response_model=Dict[str, Any])
def calculate_live_affordability(payload: AffordabilityCalculateRequest):
    """
    Live pure financial calculator:
    Calculates Existing DTI, Total DTI, FOIR, Disposable Income, and reducing-balance Monthly EMI.
    """
    emi = calculate_reducing_emi(payload.requested_principal, payload.annual_interest_rate, payload.requested_term_months)
    existing_dti = calculate_existing_dti(payload.existing_monthly_debt, payload.monthly_gross_income)
    total_dti = calculate_total_dti(payload.existing_monthly_debt, emi, payload.monthly_gross_income)
    foir = calculate_foir(payload.existing_monthly_debt, emi, payload.monthly_net_income)
    disposable = calculate_disposable_income(payload.monthly_net_income, payload.existing_monthly_debt, emi)

    return {
        "proposed_monthly_emi": float(emi),
        "existing_dti_ratio": float(existing_dti),
        "total_dti_ratio": float(total_dti),
        "fixed_obligation_ratio": float(foir),
        "disposable_income": float(disposable)
    }

