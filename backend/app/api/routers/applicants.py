from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from backend.app.database.connection import get_db
from backend.app.models.entities import Applicant, Employment, CreditFacility, IncomeRecord
from backend.app.schemas.pydantic_models import ApplicantBase
from backend.app.services.security import get_optional_current_user

router = APIRouter(prefix="/applicants", tags=["Applicants"])

@router.get("", response_model=List[ApplicantBase])
def list_applicants(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """List synthesized applicants with pagination and search. Restricts customers to their own record."""
    q = db.query(Applicant)
    if isinstance(user, dict) and user.get("role") == "CUSTOMER":
        cust_id = user.get("applicant_id") or "APP-2026-000001"
        q = q.filter(Applicant.applicant_id == cust_id)
    elif search:
        q = q.filter(
            (Applicant.first_name.ilike(f"%{search}%")) |
            (Applicant.last_name.ilike(f"%{search}%")) |
            (Applicant.applicant_id.ilike(f"%{search}%"))
        )
    return q.offset(skip).limit(limit).all()

@router.get("/{applicant_id}")
def get_applicant_detail(
    applicant_id: str, 
    db: Session = Depends(get_db),
    user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """Retrieve complete profile of an applicant including employment and credit facilities."""
    if isinstance(user, dict) and user.get("role") == "CUSTOMER":
        cust_id = user.get("applicant_id") or "APP-2026-000001"
        if applicant_id != cust_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Cannot view other borrowers' personal applicant records"
            )

    applicant = db.query(Applicant).filter(Applicant.applicant_id == applicant_id).first()
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    
    employments = db.query(Employment).filter(Employment.applicant_id == applicant_id).all()
    incomes = db.query(IncomeRecord).filter(IncomeRecord.applicant_id == applicant_id).all()
    facilities = db.query(CreditFacility).filter(CreditFacility.applicant_id == applicant_id).all()

    return {
        "applicant": ApplicantBase.model_validate(applicant),
        "employments": [
            {
                "employer_name": e.employer_name,
                "employment_type": e.employment_type,
                "industry": e.industry,
                "job_title": e.job_title,
                "monthly_salary": float(e.monthly_salary),
                "verification_status": e.verification_status
            } for e in employments
        ],
        "incomes": [
            {
                "income_source": i.income_source,
                "gross_monthly_income": float(i.gross_monthly_income),
                "net_monthly_income": float(i.net_monthly_income),
                "verification_status": i.verification_status
            } for i in incomes
        ],
        "credit_facilities": [
            {
                "facility_type": f.facility_type,
                "lender_reference": f.lender_reference,
                "credit_limit": float(f.credit_limit),
                "outstanding_balance": float(f.outstanding_balance),
                "monthly_emi": float(f.monthly_emi),
                "payment_status": f.payment_status
            } for f in facilities
        ]
    }

