from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from decimal import Decimal
from backend.app.database.connection import get_db
from backend.app.models.entities import RepaymentSchedule, LoanApplication
from backend.app.schemas.pydantic_models import InstallmentSchema
from backend.app.calculations.financial import verify_schedule_reconciliation

router = APIRouter(prefix="/repayments", tags=["Repayment Schedules"])

@router.get("/{application_id}", response_model=Dict[str, Any])
def get_repayment_schedule(application_id: str, db: Session = Depends(get_db)):
    """Retrieve full repayment amortization schedule and reconciliation audit for an application."""
    app = db.query(LoanApplication).filter(LoanApplication.application_id == application_id).first()
    if not app:
        raise HTTPException(
            status_code=404, 
            detail=f"Application '{application_id}' does not exist in the platform repository."
        )

    installments = db.query(RepaymentSchedule).filter(
        RepaymentSchedule.application_id == application_id
    ).order_by(RepaymentSchedule.installment_number.asc()).all()

    if not installments:
        if app.application_status == "REJECT":
            raise HTTPException(
                status_code=404,
                detail=f"Loan '{application_id}' was REJECTED during underwriting. Underwriting credit policy does not generate repayment amortization schedules or disburse funds for rejected applications."
            )
        elif app.application_status in ("PENDING_INFORMATION", "MANUAL_REVIEW", "SUBMITTED"):
            raise HTTPException(
                status_code=404,
                detail=f"Loan '{application_id}' is currently in '{app.application_status}' status. Repayment amortization schedules are generated once the facility reaches APPROVED or DISBURSED status."
            )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No repayment schedule found for application '{application_id}'."
            )

    inst_dicts = [
        {
            "schedule_id": i.schedule_id,
            "application_id": i.application_id,
            "installment_number": i.installment_number,
            "due_date": i.due_date,
            "opening_balance": i.opening_balance,
            "principal_amount": i.principal_amount,
            "interest_amount": i.interest_amount,
            "installment_amount": i.installment_amount,
            "closing_balance": i.closing_balance,
            "payment_status": i.payment_status,
            "paid_amount": i.paid_amount,
            "paid_date": i.paid_date
        } for i in installments
    ]

    reconciled, audit_details = verify_schedule_reconciliation(app.requested_principal, inst_dicts)

    return {
        "application_id": application_id,
        "disbursed_principal": float(app.requested_principal),
        "total_installments": len(installments),
        "is_reconciled": reconciled,
        "audit_details": {
            k: (float(v) if isinstance(v, Decimal) else v) for k, v in audit_details.items()
        },
        "installments": [InstallmentSchema.model_validate(i) for i in installments]
    }

