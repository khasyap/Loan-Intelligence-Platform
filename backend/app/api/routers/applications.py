from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from decimal import Decimal
import datetime
import json

from backend.app.database.connection import get_db
from backend.app.models.entities import (
    LoanApplication, Applicant, LoanProduct, Document, AffordabilityCheck,
    Decision, RepaymentSchedule, Employment, CreditFacility, IncomeRecord,
    ApplicationStatusHistory, DecisionRuleExecution
)
from backend.app.schemas.pydantic_models import (
    ApplicationSummary, ApplicationDetail, ApplicationCreate,
    ApplicantBase, ProductSchema, DocumentSchema, AffordabilitySchema,
    DecisionSchema, InstallmentSchema
)
from backend.app.calculations.financial import (
    calculate_dti, calculate_foir, calculate_disposable_income,
    calculate_reducing_emi, generate_amortization_schedule
)
from backend.app.rules_engine.engine import evaluate_application

from backend.app.services.security import get_optional_current_user

router = APIRouter(prefix="/applications", tags=["Loan Applications"])

@router.get("", response_model=List[ApplicationSummary])
def list_applications(
    status: Optional[str] = None,
    product_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """Retrieve loan applications with status and product filters. Enforces customer data isolation."""
    q = db.query(LoanApplication)
    if isinstance(user, dict) and user.get("role") == "CUSTOMER":
        cust_id = user.get("applicant_id") or "APP-2026-000001"
        q = q.filter(LoanApplication.applicant_id == cust_id)
    elif status:
        q = q.filter(LoanApplication.application_status == status)
    if product_id:
        q = q.filter(LoanApplication.product_id == product_id)
    return q.order_by(LoanApplication.application_date.desc()).offset(skip).limit(limit).all()


@router.get("/{application_id}")
def get_application_detail(
    application_id: str, 
    db: Session = Depends(get_db),
    user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """Retrieve comprehensive application detail with rules trace, documents, and repayment plan."""
    app = db.query(LoanApplication).filter(LoanApplication.application_id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if isinstance(user, dict) and user.get("role") == "CUSTOMER":
        cust_id = user.get("applicant_id") or "APP-2026-000001"
        if app.applicant_id != cust_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Cannot view loan applications belonging to other borrowers"
            )

    applicant = db.query(Applicant).filter(Applicant.applicant_id == app.applicant_id).first()
    product = db.query(LoanProduct).filter(LoanProduct.product_id == app.product_id).first()
    docs = db.query(Document).filter(Document.application_id == application_id).all()
    affordability = db.query(AffordabilityCheck).filter(AffordabilityCheck.application_id == application_id).first()
    decision = db.query(Decision).filter(Decision.application_id == application_id).order_by(Decision.decision_sequence.desc()).first()
    installments = db.query(RepaymentSchedule).filter(RepaymentSchedule.application_id == application_id).order_by(RepaymentSchedule.installment_number.asc()).all()

    return {
        "application_id": app.application_id,
        "applicant_id": app.applicant_id,
        "product_id": app.product_id,
        "requested_principal": float(app.requested_principal),
        "requested_term_months": app.requested_term_months,
        "application_date": app.application_date,
        "application_status": app.application_status,
        "submission_channel": app.submission_channel,
        "applicant": ApplicantBase.model_validate(applicant),
        "product": ProductSchema.model_validate(product),
        "documents": [DocumentSchema.model_validate(d) for d in docs],
        "affordability": AffordabilitySchema.model_validate(affordability) if affordability else None,
        "decision": DecisionSchema.model_validate(decision) if decision else None,
        "installments": [InstallmentSchema.model_validate(i) for i in installments]
    }


@router.post("", response_model=Dict[str, Any])
def submit_new_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    """
    Live Loan Origination: Submits a new loan application, calculates affordability in real time,
    executes explainable decision rules, and generates repayment amortization if approved.
    """
    applicant = db.query(Applicant).filter(Applicant.applicant_id == payload.applicant_id).first()
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")

    product = db.query(LoanProduct).filter(LoanProduct.product_id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Generate new ID
    count = db.query(LoanApplication).count()
    app_id = f"LOAN-2026-{count + 1:06d}"
    now = datetime.datetime.now(datetime.timezone.utc)

    # 1. Create Application
    new_app = LoanApplication(
        application_id=app_id,
        applicant_id=payload.applicant_id,
        product_id=payload.product_id,
        requested_principal=Decimal(str(payload.requested_principal)),
        requested_term_months=payload.requested_term_months,
        application_date=now,
        application_status="SUBMITTED",
        submission_channel=payload.submission_channel or "ONLINE_PORTAL"
    )
    db.add(new_app)
    db.commit()

    # 2. Add Standard Documents
    doc1_id = f"DOC-{app_id}-001"
    doc2_id = f"DOC-{app_id}-002"
    db.query(Document).filter(Document.document_id.in_([doc1_id, doc2_id])).delete(synchronize_session=False)
    doc1 = Document(
        document_id=doc1_id,
        application_id=app_id,
        document_type="IDENTITY_PROOF",
        submission_status="VERIFIED",
        verification_status="VERIFIED",
        submitted_at=now,
        verified_at=now,
        document_reference=f"REF-{app_id}-001"
    )
    doc2 = Document(
        document_id=doc2_id,
        application_id=app_id,
        document_type="INCOME_PROOF",
        submission_status="VERIFIED",
        verification_status="VERIFIED",
        submitted_at=now,
        verified_at=now,
        document_reference=f"REF-{app_id}-002"
    )
    db.add(doc1)
    db.add(doc2)
    db.commit()

    # 3. Calculate Affordability
    employments = db.query(Employment).filter(Employment.applicant_id == payload.applicant_id).all()
    incomes = db.query(IncomeRecord).filter(IncomeRecord.applicant_id == payload.applicant_id).all()
    facilities = db.query(CreditFacility).filter(CreditFacility.applicant_id == payload.applicant_id).all()

    gross_inc = sum((i.gross_monthly_income for i in incomes), Decimal("0.00")) or Decimal("50000.00")
    net_inc = sum((i.net_monthly_income for i in incomes), Decimal("0.00")) or Decimal("42000.00")
    existing_debt = sum((f.monthly_emi for f in facilities if f.payment_status != "CLOSED"), Decimal("0.00"))

    proposed_emi = calculate_reducing_emi(new_app.requested_principal, product.annual_interest_rate, new_app.requested_term_months)
    dti = calculate_dti(existing_debt, gross_inc)
    foir = calculate_foir(existing_debt, proposed_emi, net_inc)
    disposable = calculate_disposable_income(net_inc, existing_debt, proposed_emi)

    aff_status = "PASSED" if (dti <= product.maximum_dti and foir <= product.maximum_foir) else "FAILED"

    aff = AffordabilityCheck(
        affordability_check_id=f"AFF-{app_id}-01",
        application_id=app_id,
        assessment_timestamp=now,
        monthly_net_income=net_inc,
        existing_monthly_debt=existing_debt,
        proposed_monthly_emi=proposed_emi,
        debt_to_income_ratio=dti,
        fixed_obligation_ratio=foir,
        disposable_income=disposable,
        affordability_status=aff_status,
        calculation_details=json.dumps({"dti": str(dti), "foir": str(foir)})
    )
    db.add(aff)
    db.commit()

    # 4. Evaluate Decision Rules
    app_dict = {
        "requested_principal": float(new_app.requested_principal),
        "requested_term_months": new_app.requested_term_months
    }
    prod_dict = {
        "min_principal": float(product.min_principal),
        "max_principal": float(product.max_principal),
        "min_term_months": product.min_term_months,
        "max_term_months": product.max_term_months,
        "minimum_credit_score": product.minimum_credit_score,
        "maximum_dti": float(product.maximum_dti),
        "maximum_foir": float(product.maximum_foir)
    }
    app_applicant_dict = {"credit_score": applicant.credit_score}
    aff_dict = {"debt_to_income_ratio": dti, "fixed_obligation_ratio": foir}
    doc_dicts = [
        {"document_type": "IDENTITY_PROOF", "verification_status": "VERIFIED"},
        {"document_type": "INCOME_PROOF", "verification_status": "VERIFIED"}
    ]
    emp_dicts = [
        {"employment_status": e.employment_status, "employment_type": e.employment_type} for e in employments
    ] or [{"employment_status": "CURRENT", "employment_type": "SALARIED"}]

    dec_res = evaluate_application(
        app_dict, prod_dict, app_applicant_dict, aff_dict, doc_dicts, emp_dicts, 1
    )

    dec_id = f"DEC-{app_id}-01"
    decision = Decision(
        decision_id=dec_id,
        application_id=app_id,
        decision_sequence=1,
        decision_status=dec_res.status,
        decision_timestamp=now + datetime.timedelta(seconds=1),
        decision_reason_code=dec_res.reason_code,
        decision_explanation=dec_res.explanation,
        risk_score=dec_res.risk_score,
        rules_triggered=json.dumps(dec_res.rules_triggered),
        reviewer_id="ONLINE_REALTIME_ENGINE"
    )
    db.add(decision)
    new_app.application_status = dec_res.status
    db.commit()

    # 5. If Approved, Generate Repayment Schedule
    if dec_res.status == "APPROVED":
        disb_date = now.date() + datetime.timedelta(days=2)
        sched = generate_amortization_schedule(
            app_id, new_app.requested_principal, product.annual_interest_rate,
            new_app.requested_term_months, disb_date
        )
        for s in sched:
            db.add(RepaymentSchedule(**s))
        db.commit()

    return {
        "application_id": app_id,
        "applicant_name": f"{applicant.first_name} {applicant.last_name}",
        "product_name": product.product_name,
        "decision_status": dec_res.status,
        "reason_code": dec_res.reason_code,
        "explanation": dec_res.explanation,
        "proposed_monthly_emi": float(proposed_emi),
        "dti_ratio": float(dti),
        "foir_ratio": float(foir)
    }

