import pytest
from backend.app.database.connection import SessionLocal
from backend.app.api.routers.products import list_products
from backend.app.api.routers.applicants import list_applicants, get_applicant_detail
from backend.app.api.routers.applications import list_applications, get_application_detail, submit_new_application
from backend.app.api.routers.analytics import get_executive_kpis, get_risk_analytics, get_operations_analytics
from backend.app.api.routers.repayments import get_repayment_schedule
from backend.app.schemas.pydantic_models import ApplicationCreate

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()

def test_list_products(db):
    products = list_products(db=db)
    assert len(products) == 4
    prod_ids = [p.product_id for p in products]
    assert "PROD-001" in prod_ids
    assert "PROD-004" in prod_ids

def test_list_applicants(db):
    apps = list_applicants(skip=0, limit=10, search=None, db=db)
    assert len(apps) <= 10
    assert len(apps) > 0
    assert "APP-2026-" in apps[0].applicant_id

def test_list_applications(db):
    app_list = list_applications(status=None, product_id=None, skip=0, limit=10, db=db)
    assert len(app_list) <= 10
    assert len(app_list) > 0
    assert "LOAN-2026-" in app_list[0].application_id

def test_get_application_detail(db):
    app_list = list_applications(status=None, product_id=None, skip=0, limit=1, db=db)
    target_id = app_list[0].application_id
    detail = get_application_detail(target_id, db=db)
    assert detail["application_id"] == target_id
    assert "applicant" in detail
    assert "product" in detail
    assert "documents" in detail

def test_live_loan_application_submission(db):
    apps = list_applicants(skip=0, limit=1, search=None, db=db)
    applicant_id = apps[0].applicant_id

    payload = ApplicationCreate(
        applicant_id=applicant_id,
        product_id="PROD-001",
        requested_principal=200000.0,
        requested_term_months=24,
        submission_channel="ONLINE_PORTAL"
    )
    result = submit_new_application(payload, db=db)
    app_id = result.get("application_id")
    try:
        assert "application_id" in result
        assert result["decision_status"] in ("APPROVED", "REJECT", "MANUAL_REVIEW", "PENDING_INFORMATION")
    finally:
        if app_id:
            from backend.app.models.entities import (
                LoanApplication, Document, AffordabilityCheck, Decision, RepaymentSchedule
            )
            db.query(RepaymentSchedule).filter(RepaymentSchedule.application_id == app_id).delete()
            db.query(Decision).filter(Decision.application_id == app_id).delete()
            db.query(AffordabilityCheck).filter(AffordabilityCheck.application_id == app_id).delete()
            db.query(Document).filter(Document.application_id == app_id).delete()
            db.query(LoanApplication).filter(LoanApplication.application_id == app_id).delete()
            db.commit()


def test_analytics_executive(db):
    kpis = get_executive_kpis(db=db)
    assert "total_applicants" in kpis
    assert "approval_rate" in kpis
    assert kpis["total_applications"] > 0

def test_analytics_risk(db):
    risk = get_risk_analytics(db=db)
    assert "credit_score_distribution" in risk
    assert "dti_distribution" in risk
    assert "foir_distribution" in risk
    assert len(risk["credit_score_distribution"]) > 0

def test_analytics_operations(db):
    ops = get_operations_analytics(db=db)
    assert "lifecycle_funnel" in ops
    assert "document_verification_summary" in ops
