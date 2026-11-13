"""
Exports Router: Exposes secured, performant Excel (.xlsx) and PDF (.pdf) file downloads
for Executive Portfolios, Application Registries, Detailed Loan Dossiers,
Amortization Schedules, Risk Reports, Operations Queues, and Anomaly Audits.

Implements strict Role-Based Access Control (RBAC), customer data boundary enforcement,
audit logging, and streaming HTTP attachment responses.
"""

import io
import json
import datetime
import openpyxl
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.models.entities import (
    LoanApplication, Applicant, LoanProduct, AffordabilityCheck, Decision,
    CreditProfile, Document, Disbursement, RepaymentSchedule, AuditLog,
    GroundTruthAnomaly
)
from backend.app.services.security import get_current_user, require_role
from backend.app.services.export_service import (
    ExportEngine, apply_excel_sheet_styling, get_pdf_styles, NumberedCanvas
)
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from backend.app.api.routers.analytics import (
    get_executive_kpis, get_risk_analytics, get_operations_analytics
)
from backend.app.api.routers.repayments import get_repayment_schedule

router = APIRouter(prefix="/exports", tags=["Data Export & Reporting"])

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PDF_MIME = "application/pdf"
CSV_MIME = "text/csv; charset=utf-8"


def log_export_audit(db: Session, user: Dict[str, Any], report_type: str, file_format: str, extra: str = ""):
    """Records an audit log entry for every file download."""
    try:
        now = datetime.datetime.now(datetime.timezone.utc)
        count = db.query(AuditLog).count()
        log_entry = AuditLog(
            log_id=f"AUD-EXP-{count + 1:07d}",
            entity_name="REPORT_EXPORT",
            record_id=f"{report_type}:{file_format}",
            action="EXPORT",
            actor_id=user.get("email", "anonymous"),
            timestamp=now,
            diff=json.dumps({"format": file_format, "role": user.get("role"), "metadata": extra})
        )
        db.add(log_entry)
        db.commit()
    except Exception:
        db.rollback()


# ------------------------------------------------------------------------------
# 1. EXECUTIVE PORTFOLIO EXPORT
# ------------------------------------------------------------------------------
@router.get("/executive")
def export_executive_portfolio(
    format: str = Query("xlsx", pattern="^(xlsx|pdf|csv)$"),
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(require_role(["ADMIN", "RISK_REVIEWER"]))
):
    """Download executive lending volume, approval ratios, and product specifications."""
    kpis = get_executive_kpis(db=db)
    products = [
        {
            "product_id": p.product_id,
            "product_name": p.product_name,
            "product_type": p.product_type,
            "min_principal": float(p.min_principal),
            "max_principal": float(p.max_principal),
            "min_term_months": p.min_term_months,
            "max_term_months": p.max_term_months,
            "annual_interest_rate": float(p.annual_interest_rate),
            "processing_fee_rate": float(p.processing_fee_rate),
            "maximum_dti": float(p.maximum_dti),
            "maximum_foir": float(p.maximum_foir),
            "minimum_credit_score": p.minimum_credit_score,
            "product_status": p.product_status
        }
        for p in db.query(LoanProduct).all()
    ]

    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    log_export_audit(db, user, "EXECUTIVE_PORTFOLIO", format)

    if format == "xlsx":
        buffer = ExportEngine.generate_executive_excel(kpis, products)
        filename = f"Executive_Lending_Portfolio_{date_str}.xlsx"
        return Response(
            content=buffer.getvalue(),
            media_type=XLSX_MIME,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    elif format == "csv":
        buffer = ExportEngine.generate_executive_csv(kpis, products)
        filename = f"Executive_Lending_Portfolio_{date_str}.csv"
        return Response(
            content=buffer.getvalue(),
            media_type=CSV_MIME,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    else:
        buffer = ExportEngine.generate_executive_pdf(kpis, products)
        filename = f"Executive_Lending_Portfolio_{date_str}.pdf"
        return Response(
            content=buffer.getvalue(),
            media_type=PDF_MIME,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )


# ------------------------------------------------------------------------------
# 2. LOAN APPLICATIONS REGISTRY EXPORT
# ------------------------------------------------------------------------------
@router.get("/applications")
def export_applications(
    format: str = Query("xlsx", pattern="^(xlsx|pdf|csv)$"),
    status: Optional[str] = None,
    search: Optional[str] = None,
    ids: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Download filtered or selected loan applications.
    Enforces customer boundary: Customers can ONLY download their own applications.
    """
    q = db.query(LoanApplication)

    # RBAC Customer Boundary
    if user.get("role") == "CUSTOMER":
        cust_app_id = user.get("applicant_id") or "APP-2026-000001"
        q = q.filter(LoanApplication.applicant_id == cust_app_id)
    elif status:
        q = q.filter(LoanApplication.application_status == status)

    if ids:
        id_list = [i.strip() for i in ids.split(",") if i.strip()]
        q = q.filter(LoanApplication.application_id.in_(id_list))

    if search:
        search_filter = f"%{search.strip()}%"
        q = q.filter(
            (LoanApplication.application_id.ilike(search_filter)) |
            (LoanApplication.applicant_id.ilike(search_filter)) |
            (LoanApplication.product_id.ilike(search_filter))
        )

    # Limit to top 2,000 records for performance safety
    records = q.order_by(LoanApplication.application_id.asc()).limit(2000).all()

    app_dicts = [
        {
            "application_id": r.application_id,
            "applicant_id": r.applicant_id,
            "product_id": r.product_id,
            "requested_principal": float(r.requested_principal),
            "requested_term_months": r.requested_term_months,
            "application_date": str(r.application_date),
            "application_status": r.application_status,
            "submission_channel": r.submission_channel
        }
        for r in records
    ]

    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    log_export_audit(db, user, "APPLICATIONS", format, f"count={len(app_dicts)}")

    if format == "xlsx":
        buffer = ExportEngine.generate_applications_excel(app_dicts)
        filename = f"Loan_Applications_{date_str}.xlsx"
        return Response(
            content=buffer.getvalue(),
            media_type=XLSX_MIME,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    elif format == "csv":
        buffer = ExportEngine.generate_applications_csv(records)
        filename = f"Loan_Applications_{date_str}.csv"
        return Response(
            content=buffer.getvalue(),
            media_type=CSV_MIME,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    else:
        filter_label = status or search or ("Selected Records" if ids else "Authorized Portfolio")
        buffer = ExportEngine.generate_applications_pdf(app_dicts, filter_desc=filter_label)
        filename = f"Loan_Applications_{date_str}.pdf"
        return Response(
            content=buffer.getvalue(),
            media_type=PDF_MIME,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )


# ------------------------------------------------------------------------------
# 3. INDIVIDUAL LOAN APPLICATION DOSSIER EXPORT
# ------------------------------------------------------------------------------
@router.get("/loans/{application_id}")
def export_individual_loan(
    application_id: str,
    format: str = Query("xlsx", pattern="^(xlsx|pdf|csv)$"),
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Download complete individual loan underwriting dossier:
    Application, Applicant, Product, Affordability, Decision, CreditProfile, Docs, Disbursement, Repayments.
    Enforces customer ownership verification.
    """
    app = db.query(LoanApplication).filter(LoanApplication.application_id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Loan application not found")

    # Customer boundary check
    if user.get("role") == "CUSTOMER":
        cust_app_id = user.get("applicant_id") or "APP-2026-000001"
        if app.applicant_id != cust_app_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Cannot access dossiers belonging to other applicants."
            )

    applicant = db.query(Applicant).filter(Applicant.applicant_id == app.applicant_id).first()
    product = db.query(LoanProduct).filter(LoanProduct.product_id == app.product_id).first()
    affordability = db.query(AffordabilityCheck).filter(AffordabilityCheck.application_id == application_id).first()
    decision = db.query(Decision).filter(Decision.application_id == application_id).order_by(Decision.decision_sequence.desc()).first()
    credit_profile = db.query(CreditProfile).filter(CreditProfile.applicant_id == app.applicant_id).order_by(CreditProfile.assessment_date.desc()).first()
    documents = db.query(Document).filter(Document.application_id == application_id).all()
    disbursement = db.query(Disbursement).filter(Disbursement.application_id == application_id).first()

    # Repayment schedule
    repayment_dict = {}
    try:
        repayment_dict = get_repayment_schedule(application_id, db=db)
    except Exception:
        pass

    dossier_data = {
        "application": {
            "application_id": app.application_id,
            "applicant_id": app.applicant_id,
            "product_id": app.product_id,
            "requested_principal": float(app.requested_principal),
            "requested_term_months": app.requested_term_months,
            "application_date": str(app.application_date),
            "application_status": app.application_status,
            "submission_channel": app.submission_channel
        },
        "applicant": {
            "applicant_id": applicant.applicant_id if applicant else "",
            "first_name": applicant.first_name if applicant else "",
            "last_name": applicant.last_name if applicant else "",
            "email": applicant.email if applicant else ""
        },
        "product": {
            "product_id": product.product_id if product else "",
            "product_name": product.product_name if product else "",
            "annual_interest_rate": float(product.annual_interest_rate) if product else 0
        },
        "affordability": {
            "monthly_net_income": float(affordability.monthly_net_income) if affordability else 0,
            "existing_monthly_debt": float(affordability.existing_monthly_debt) if affordability else 0,
            "proposed_monthly_emi": float(affordability.proposed_monthly_emi) if affordability else 0,
            "debt_to_income_ratio": float(affordability.debt_to_income_ratio) if affordability else 0,
            "fixed_obligation_ratio": float(affordability.fixed_obligation_ratio) if affordability else 0,
            "disposable_income": float(affordability.disposable_income) if affordability else 0
        },
        "decision": {
            "decision_id": decision.decision_id if decision else "",
            "decision_status": decision.decision_status if decision else "PENDING",
            "decision_reason_code": decision.decision_reason_code if decision else "UNDER_REVIEW",
            "decision_explanation": decision.decision_explanation if decision else "Evaluation in progress",
            "reviewer_id": decision.reviewer_id if decision else "AUTOMATED_RULE_ENGINE"
        },
        "credit_profile": {
            "synthetic_credit_score": credit_profile.synthetic_credit_score if credit_profile else 700,
            "score_band": credit_profile.score_band if credit_profile else "GOOD",
            "credit_utilization": float(credit_profile.credit_utilization) if credit_profile else 0.25,
            "active_facility_count": credit_profile.active_facility_count if credit_profile else 1
        },
        "documents": [
            {
                "document_id": d.document_id,
                "document_type": d.document_type,
                "verification_status": d.verification_status,
                "document_reference": d.document_reference
            }
            for d in documents
        ],
        "disbursement": {
            "disbursement_id": disbursement.disbursement_id if disbursement else "PENDING_RELEASE",
            "disbursed_amount": float(disbursement.disbursed_amount) if disbursement else float(app.requested_principal),
            "disbursement_date": str(disbursement.disbursement_date) if disbursement else "Pending Gate Release"
        },
        "repayments": repayment_dict
    }

    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    log_export_audit(db, user, "LOAN_DOSSIER", format, application_id)

    if format == "xlsx":
        buffer = ExportEngine.generate_individual_loan_excel(dossier_data)
        filename = f"Loan_Dossier_{application_id}_{date_str}.xlsx"
        return Response(
            content=buffer.getvalue(),
            media_type=XLSX_MIME,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    elif format == "csv":
        buffer = ExportEngine.generate_individual_loan_csv(dossier_data)
        filename = f"Loan_Dossier_{application_id}_{date_str}.csv"
        return Response(
            content=buffer.getvalue(),
            media_type=CSV_MIME,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    else:
        buffer = ExportEngine.generate_individual_loan_pdf(dossier_data)
        filename = f"Loan_Dossier_{application_id}_{date_str}.pdf"
        return Response(
            content=buffer.getvalue(),
            media_type=PDF_MIME,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )


# ------------------------------------------------------------------------------
# 4. REPAYMENT AMORTIZATION SCHEDULE EXPORT
# ------------------------------------------------------------------------------
@router.get("/repayments/{application_id}")
def export_repayments(
    application_id: str,
    format: str = Query("xlsx", pattern="^(xlsx|pdf|csv)$"),
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Download full reducing-balance repayment schedule with penny reconciliation.
    Enforces customer ownership check.
    """
    app = db.query(LoanApplication).filter(LoanApplication.application_id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if user.get("role") == "CUSTOMER":
        cust_app_id = user.get("applicant_id") or "APP-2026-000001"
        if app.applicant_id != cust_app_id:
            raise HTTPException(status_code=403, detail="Forbidden: Cannot access other borrower schedules")

    schedule_data = get_repayment_schedule(application_id, db=db)
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    log_export_audit(db, user, "REPAYMENTS", format, application_id)

    if format == "xlsx":
        buffer = ExportEngine.generate_repayments_excel(schedule_data)
        filename = f"Repayment_Schedule_{application_id}_{date_str}.xlsx"
        return Response(
            content=buffer.getvalue(),
            media_type=XLSX_MIME,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    elif format == "csv":
        buffer = ExportEngine.generate_repayments_csv(schedule_data)
        filename = f"Repayment_Schedule_{application_id}_{date_str}.csv"
        return Response(
            content=buffer.getvalue(),
            media_type=CSV_MIME,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    else:
        buffer = ExportEngine.generate_repayments_pdf(schedule_data)
        filename = f"Repayment_Schedule_{application_id}_{date_str}.pdf"
        return Response(
            content=buffer.getvalue(),
            media_type=PDF_MIME,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )


# ------------------------------------------------------------------------------
# 5. RISK & FAIR LENDING COMPLIANCE EXPORT
# ------------------------------------------------------------------------------
@router.get("/risk")
def export_risk_compliance(
    format: str = Query("xlsx", pattern="^(xlsx|pdf|csv)$"),
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(require_role(["ADMIN", "RISK_REVIEWER"]))
):
    """Download credit score distribution, DTI/FOIR metrics, and decision reason codes."""
    risk_data = get_risk_analytics(db=db)
    reason_codes = risk_data.get("reason_code_distribution", [])

    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    log_export_audit(db, user, "RISK_COMPLIANCE", format)

    headers1 = ["Reason Code", "Classification", "Count", "Engine Action"]
    rows1 = [
        [
            r.get("code"),
            "Policy Pass" if str(r.get("code")).startswith("APP_") else "Hard Rule Breach" if str(r.get("code")).startswith("REJ_") else "Discretionary Exception",
            r.get("count"),
            "APPROVED" if str(r.get("code")).startswith("APP_") else "REJECT" if str(r.get("code")).startswith("REJ_") else "MANUAL_REVIEW"
        ]
        for r in reason_codes
    ]

    if format == "csv":
        buffer = ExportEngine.generate_csv(headers1, rows1)
        filename = f"Risk_Compliance_Report_{date_str}.csv"
        return Response(content=buffer.getvalue(), media_type=CSV_MIME, headers={"Content-Disposition": f'attachment; filename="{filename}"'})

    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "Decision Reason Codes"
    apply_excel_sheet_styling(ws1, "Fair Lending Engine - Underwriting Reason Codes", headers1, rows1)

    ws2 = wb.create_sheet(title="Credit Score Distribution")
    headers2 = ["Score Range", "Applicant Count", "Risk Band"]
    rows2 = [[d.get("range"), d.get("count"), "Prime / Near-Prime"] for d in risk_data.get("credit_score_distribution", [])]
    apply_excel_sheet_styling(ws2, "Bureau Score Band Distribution", headers2, rows2)

    if format == "xlsx":
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        filename = f"Risk_Compliance_Report_{date_str}.xlsx"
        return Response(content=output.getvalue(), media_type=XLSX_MIME, headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    else:
        # Generate PDF using applications engine structure with risk tables
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=40, bottomMargin=40)
        styles = get_pdf_styles()
        story = [
            Paragraph("Risk & Regulatory Compliance Report", styles["DocTitle"]),
            Paragraph(f"Fair Lending Audit & Reason Code Hierarchy  |  Generated on: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}", styles["DocSub"]),
            Paragraph("Decision Reason Code Frequency", styles["SectionHead"])
        ]
        t_data = [[Paragraph("Reason Code", styles["CellHeader"]), Paragraph("Classification", styles["CellHeader"]), Paragraph("Count", styles["CellHeader"]), Paragraph("Action", styles["CellHeader"])]]
        for r in rows1:
            t_data.append([
                Paragraph(str(r[0]), styles["CellBold"]),
                Paragraph(str(r[1]), styles["CellText"]),
                Paragraph(str(r[2]), styles["CellBold"]),
                Paragraph(str(r[3]), styles["CellBold"])
            ])
        t = Table(t_data, colWidths=[150, 150, 100, 140], repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        doc.build(story, canvasmaker=NumberedCanvas)
        buf.seek(0)
        filename = f"Risk_Compliance_Report_{date_str}.pdf"
        return Response(content=buf.getvalue(), media_type=PDF_MIME, headers={"Content-Disposition": f'attachment; filename="{filename}"'})


# ------------------------------------------------------------------------------
# 6. OPERATIONS FUNNEL & QUEUES EXPORT
# ------------------------------------------------------------------------------
@router.get("/operations")
def export_operations(
    format: str = Query("xlsx", pattern="^(xlsx|pdf|csv)$"),
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(require_role(["ADMIN", "RISK_REVIEWER", "OPERATIONS_ANALYST"]))
):
    """Download lifecycle funnel counts and document verification summaries."""
    ops = get_operations_analytics(db=db)
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    log_export_audit(db, user, "OPERATIONS_FUNNEL", format)

    headers1 = ["Lifecycle Stage", "Application Volume", "Status Category"]
    rows1 = [[f.get("status"), f.get("count"), "Operational Funnel"] for f in ops.get("lifecycle_funnel", [])]

    if format == "csv":
        buffer = ExportEngine.generate_csv(headers1, rows1)
        filename = f"Operations_Funnel_Report_{date_str}.csv"
        return Response(content=buffer.getvalue(), media_type=CSV_MIME, headers={"Content-Disposition": f'attachment; filename="{filename}"'})

    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "Lifecycle Funnel"
    apply_excel_sheet_styling(ws1, "Operational Application Lifecycle Funnel", headers1, rows1)

    ws2 = wb.create_sheet(title="Document Verification")
    headers2 = ["Document Status", "Count", "Queue Priority"]
    rows2 = [[d.get("status"), d.get("count"), "High Priority" if d.get("status") == "PENDING" else "Processed"] for d in ops.get("document_verification_summary", [])]
    apply_excel_sheet_styling(ws2, "Document Verification Health & Backlog", headers2, rows2)

    if format == "xlsx":
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        filename = f"Operations_Funnel_Report_{date_str}.xlsx"
        return Response(content=output.getvalue(), media_type=XLSX_MIME, headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    else:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=40, bottomMargin=40)
        styles = get_pdf_styles()
        story = [
            Paragraph("Operations Funnel & Document Queue Report", styles["DocTitle"]),
            Paragraph(f"Application Processing Funnel & Verification Queues  |  Generated on: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}", styles["DocSub"]),
            Paragraph("Lifecycle Funnel Distribution", styles["SectionHead"])
        ]
        t_data = [[Paragraph("Lifecycle Stage", styles["CellHeader"]), Paragraph("Volume", styles["CellHeader"])]]
        for f in rows1:
            t_data.append([Paragraph(str(f[0]), styles["CellBold"]), Paragraph(str(f[1]), styles["CellBold"])])
        t = Table(t_data, colWidths=[300, 240])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        doc.build(story, canvasmaker=NumberedCanvas)
        buf.seek(0)
        filename = f"Operations_Funnel_Report_{date_str}.pdf"
        return Response(content=buf.getvalue(), media_type=PDF_MIME, headers={"Content-Disposition": f'attachment; filename="{filename}"'})


# ------------------------------------------------------------------------------
# 7. ANOMALY DETECTION EVALUATION EXPORT (ADMIN ONLY)
# ------------------------------------------------------------------------------
@router.get("/anomalies")
def export_anomalies(
    format: str = Query("xlsx", pattern="^(xlsx|pdf|csv)$"),
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(require_role(["ADMIN"]))
):
    """
    Download isolated anomaly evaluation results & segregated ground-truth registry.
    Strictly restricted to ADMIN to avoid ground-truth operational leakage.
    """
    import json
    import os

    eval_path = "reports/anomaly_evaluation.json"
    eval_data = {}
    if os.path.exists(eval_path):
        with open(eval_path, "r", encoding="utf-8") as f:
            eval_data = json.load(f)

    # Fetch ground truth
    gt_records = db.query(GroundTruthAnomaly).all()
    gt_dicts = [
        {
            "anomaly_id": g.anomaly_id,
            "entity_name": g.entity_name,
            "record_id": g.record_id,
            "issue_type": g.issue_type,
            "severity": g.severity,
            "expected_decision": g.expected_decision,
            "explanation": g.explanation
        }
        for g in gt_records
    ]

    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    log_export_audit(db, user, "ANOMALY_LAB", format)

    if format == "xlsx":
        buffer = ExportEngine.generate_anomalies_excel(eval_data, gt_dicts)
        filename = f"Anomaly_Evaluation_Report_{date_str}.xlsx"
        return Response(
            content=buffer.getvalue(),
            media_type=XLSX_MIME,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    elif format == "csv":
        buffer = ExportEngine.generate_anomalies_csv(eval_data, gt_dicts)
        filename = f"Anomaly_Evaluation_Report_{date_str}.csv"
        return Response(
            content=buffer.getvalue(),
            media_type=CSV_MIME,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    else:
        buffer = ExportEngine.generate_anomalies_pdf(eval_data, gt_dicts)
        filename = f"Anomaly_Evaluation_Report_{date_str}.pdf"
        return Response(
            content=buffer.getvalue(),
            media_type=PDF_MIME,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
