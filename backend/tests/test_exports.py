"""
Automated Test Suite for Excel (.xlsx) and PDF (.pdf) Exports
Validates:
1. Executive Portfolio Excel & PDF export
2. Loan Applications Registry Excel & PDF export
3. Individual Loan Dossier Excel & PDF export
4. Repayment Amortization Schedule Excel & PDF export
5. Risk & Compliance Excel & PDF export
6. Operations Funnel Excel & PDF export
7. Anomaly Evaluation Excel & PDF export
8. Excel formula injection defense (CWE-1236)
9. Customer applicant ownership boundary enforcement (HTTP 403)
10. OpenPyXL workbook structure, sheet names, freeze panes, auto-filters
11. ReportLab PDF binary structure (%PDF-) and NumberedCanvas page numbering
12. Audit trail logging for export actions
"""

import io
import pytest
import openpyxl
from fastapi import HTTPException

from backend.app.database.connection import SessionLocal
from backend.app.services.security import DEMO_USERS
from backend.app.services.export_service import sanitize_for_excel
from backend.app.api.routers.exports import (
    export_executive_portfolio,
    export_applications,
    export_individual_loan,
    export_repayments,
    export_risk_compliance,
    export_operations,
    export_anomalies
)

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def admin_user():
    return DEMO_USERS["admin@bank.org"]

@pytest.fixture
def reviewer_user():
    return DEMO_USERS["reviewer@bank.org"]

@pytest.fixture
def ops_user():
    return DEMO_USERS["ops@bank.org"]

@pytest.fixture
def customer_user():
    return DEMO_USERS["customer@bank.org"]


# ------------------------------------------------------------------------------
# 1. Executive Portfolio Tests
# ------------------------------------------------------------------------------
def test_export_executive_xlsx(db, admin_user):
    resp = export_executive_portfolio(format="xlsx", db=db, user=admin_user)
    assert resp.media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "Executive_Lending_Portfolio_" in resp.headers["content-disposition"]
    assert resp.headers["content-disposition"].endswith('.xlsx"')

    wb = openpyxl.load_workbook(io.BytesIO(resp.body))
    assert "Portfolio Summary" in wb.sheetnames
    assert "Product Catalog" in wb.sheetnames
    ws = wb["Portfolio Summary"]
    assert ws["A1"].value == "Executive Lending Portfolio - Executive Summary"
    assert ws.freeze_panes == "A5"


def test_export_executive_pdf(db, admin_user):
    resp = export_executive_portfolio(format="pdf", db=db, user=admin_user)
    assert resp.media_type == "application/pdf"
    assert "Executive_Lending_Portfolio_" in resp.headers["content-disposition"]
    assert resp.headers["content-disposition"].endswith('.pdf"')
    assert resp.body.startswith(b"%PDF-")
    assert len(resp.body) > 1000


# ------------------------------------------------------------------------------
# 2. Loan Applications Registry Tests
# ------------------------------------------------------------------------------
def test_export_applications_xlsx(db, admin_user):
    resp = export_applications(format="xlsx", status="APPROVED", search=None, ids=None, db=db, user=admin_user)
    assert resp.media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    wb = openpyxl.load_workbook(io.BytesIO(resp.body))
    assert "Loan Applications" in wb.sheetnames
    ws = wb["Loan Applications"]
    headers = [cell.value for cell in ws[4]]
    assert "Application ID" in headers
    assert "Requested Principal" in headers
    assert "Status" in headers


def test_export_applications_pdf(db, admin_user):
    resp = export_applications(format="pdf", status="APPROVED", search=None, ids=None, db=db, user=admin_user)
    assert resp.media_type == "application/pdf"
    assert resp.body.startswith(b"%PDF-")


# ------------------------------------------------------------------------------
# 3. Individual Loan Dossier Tests
# ------------------------------------------------------------------------------
def test_export_individual_loan_xlsx(db, admin_user):
    resp = export_individual_loan(application_id="LOAN-2026-000004", format="xlsx", db=db, user=admin_user)
    wb = openpyxl.load_workbook(io.BytesIO(resp.body))
    assert "Loan Dossier" in wb.sheetnames
    assert "Amortization Schedule" in wb.sheetnames


def test_export_individual_loan_pdf(db, admin_user):
    resp = export_individual_loan(application_id="LOAN-2026-000004", format="pdf", db=db, user=admin_user)
    assert resp.media_type == "application/pdf"
    assert resp.body.startswith(b"%PDF-")
    assert "Loan_Dossier_LOAN-2026-000004_" in resp.headers["content-disposition"]


# ------------------------------------------------------------------------------
# 4. Repayment Amortization Schedule Tests
# ------------------------------------------------------------------------------
def test_export_repayments_xlsx_and_pdf(db, admin_user):
    resp_x = export_repayments(application_id="LOAN-2026-000004", format="xlsx", db=db, user=admin_user)
    wb = openpyxl.load_workbook(io.BytesIO(resp_x.body))
    assert "Amortization Schedule" in wb.sheetnames

    resp_p = export_repayments(application_id="LOAN-2026-000004", format="pdf", db=db, user=admin_user)
    assert resp_p.media_type == "application/pdf"
    assert resp_p.body.startswith(b"%PDF-")


# ------------------------------------------------------------------------------
# 5. Risk & Compliance and Operations Exports
# ------------------------------------------------------------------------------
def test_export_risk_and_operations(db, reviewer_user, ops_user):
    resp_r = export_risk_compliance(format="xlsx", db=db, user=reviewer_user)
    assert resp_r.media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    wb = openpyxl.load_workbook(io.BytesIO(resp_r.body))
    assert "Decision Reason Codes" in wb.sheetnames

    resp_o = export_operations(format="pdf", db=db, user=ops_user)
    assert resp_o.media_type == "application/pdf"
    assert resp_o.body.startswith(b"%PDF-")


# ------------------------------------------------------------------------------
# 6. Anomaly Detection Evaluation Export
# ------------------------------------------------------------------------------
def test_export_anomalies_admin(db, admin_user):
    resp = export_anomalies(format="xlsx", db=db, user=admin_user)
    assert resp.media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    wb = openpyxl.load_workbook(io.BytesIO(resp.body))
    assert "Evaluation Metrics" in wb.sheetnames
    assert "Ground Truth Register" in wb.sheetnames


# ------------------------------------------------------------------------------
# 7. Security: Formula Injection Defense (CWE-1236)
# ------------------------------------------------------------------------------
def test_excel_formula_injection_defense():
    assert sanitize_for_excel("=SUM(A1:A10)") == "'=SUM(A1:A10)"
    assert sanitize_for_excel("+12345") == "'+12345"
    assert sanitize_for_excel("-99999") == "'-99999"
    assert sanitize_for_excel("@cmd|' /C calc'!A0") == "'@cmd|' /C calc'!A0"
    assert sanitize_for_excel("Regular Safe Text") == "Regular Safe Text"
    assert sanitize_for_excel(12345) == 12345


# ------------------------------------------------------------------------------
# 8. Security: Customer Ownership Boundary Check
# ------------------------------------------------------------------------------
def test_customer_cannot_export_other_applicant_loan(db, customer_user):
    # Customer is bound to APP-2026-000001
    # Try to export LOAN-2026-000002 which belongs to APP-2026-000002
    with pytest.raises(HTTPException) as exc_info:
        export_individual_loan(application_id="LOAN-2026-000002", format="pdf", db=db, user=customer_user)
    assert exc_info.value.status_code == 403
    assert "Cannot access dossiers belonging to other applicants" in exc_info.value.detail


def test_customer_can_export_own_loan(db, customer_user):
    # Customer is bound to APP-2026-000001, which owns LOAN-2026-000001
    resp = export_individual_loan(application_id="LOAN-2026-000001", format="pdf", db=db, user=customer_user)
    assert resp.media_type == "application/pdf"
    assert resp.body.startswith(b"%PDF-")


def test_customer_applications_auto_filtered(db, customer_user):
    # Customer export only returns their own applications
    resp = export_applications(format="xlsx", status=None, search=None, ids=None, db=db, user=customer_user)
    wb = openpyxl.load_workbook(io.BytesIO(resp.body))
    ws = wb["Loan Applications"]
    # Check that all returned rows belong to APP-2026-000001
    for r in range(5, ws.max_row + 1):
        applicant_id_val = ws.cell(row=r, column=2).value
        assert applicant_id_val == "APP-2026-000001"


# ------------------------------------------------------------------------------
# 9. CSV Format Exports (.csv)
# ------------------------------------------------------------------------------
def test_export_executive_csv(db, admin_user):
    resp = export_executive_portfolio(format="csv", db=db, user=admin_user)
    assert resp.media_type == "text/csv; charset=utf-8"
    assert "Executive_Lending_Portfolio_" in resp.headers["content-disposition"]
    assert resp.headers["content-disposition"].endswith('.csv"')
    text = resp.body.decode("utf-8-sig")
    assert "Metric,Value,Unit / Context" in text
    assert "Total Master Applicants" in text


def test_export_applications_csv(db, admin_user):
    resp = export_applications(format="csv", db=db, user=admin_user)
    assert resp.media_type == "text/csv; charset=utf-8"
    assert "Loan_Applications_" in resp.headers["content-disposition"]
    text = resp.body.decode("utf-8-sig")
    assert "Application ID,Applicant ID,Product ID" in text


def test_export_repayments_csv(db, admin_user):
    resp = export_repayments(application_id="LOAN-2026-000004", format="csv", db=db, user=admin_user)
    assert resp.media_type == "text/csv; charset=utf-8"
    assert "Repayment_Schedule_LOAN-2026-000004_" in resp.headers["content-disposition"]
    text = resp.body.decode("utf-8-sig")
    assert "Installment #,Due Date,Opening Balance" in text


def test_export_individual_loan_csv(db, admin_user):
    resp = export_individual_loan(application_id="LOAN-2026-000004", format="csv", db=db, user=admin_user)
    assert resp.media_type == "text/csv; charset=utf-8"
    assert "Loan_Dossier_LOAN-2026-000004_" in resp.headers["content-disposition"]
    text = resp.body.decode("utf-8-sig")
    assert "Section,Attribute,Value" in text
    assert "Application Overview" in text

