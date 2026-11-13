"""
Validation Engine: Automated structural, relational, lifecycle, and arithmetic validation.
Generates comprehensive validation reports in JSON and CSV formats.
"""

from decimal import Decimal
import json
import csv
import os
from typing import List, Dict, Any, Tuple

def run_system_validation(
    applicants: List[Dict[str, Any]],
    employments: List[Dict[str, Any]],
    income_records: List[Dict[str, Any]],
    credit_facilities: List[Dict[str, Any]],
    loan_products: List[Dict[str, Any]],
    loan_applications: List[Dict[str, Any]],
    documents: List[Dict[str, Any]],
    affordability_checks: List[Dict[str, Any]],
    decisions: List[Dict[str, Any]],
    repayment_schedules: List[Dict[str, Any]],
    disbursements: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Executes all validation suites and compiles summary metrics.
    """
    total_checks = 0
    passed_checks = 0
    failed_checks = 0
    warnings = 0

    fk_failures = 0
    arithmetic_failures = 0
    lifecycle_violations = 0

    issues: List[Dict[str, Any]] = []

    # 1. Structural & PK Uniqueness
    applicant_ids = {a["applicant_id"] for a in applicants}
    total_checks += 1
    if len(applicant_ids) == len(applicants):
        passed_checks += 1
    else:
        failed_checks += 1
        issues.append({"check": "applicant_pk_uniqueness", "error": "Duplicate applicant IDs found"})

    app_ids = {a["application_id"] for a in loan_applications}
    total_checks += 1
    if len(app_ids) == len(loan_applications):
        passed_checks += 1
    else:
        failed_checks += 1
        issues.append({"check": "application_pk_uniqueness", "error": "Duplicate application IDs found"})

    prod_ids = {p["product_id"] for p in loan_products}
    total_checks += 1
    if len(prod_ids) == len(loan_products):
        passed_checks += 1
    else:
        failed_checks += 1
        issues.append({"check": "product_pk_uniqueness", "error": "Duplicate product IDs found"})

    # 2. Foreign Key Integrity
    # Applications -> Applicants & Products
    for app in loan_applications:
        total_checks += 1
        if app["applicant_id"] not in applicant_ids:
            fk_failures += 1
            failed_checks += 1
            issues.append({"check": "fk_app_applicant", "id": app["application_id"]})
        else:
            passed_checks += 1

        total_checks += 1
        if app["product_id"] not in prod_ids:
            fk_failures += 1
            failed_checks += 1
            issues.append({"check": "fk_app_product", "id": app["application_id"]})
        else:
            passed_checks += 1

    # Documents -> Applications
    for doc in documents:
        total_checks += 1
        if doc["application_id"] not in app_ids:
            fk_failures += 1
            failed_checks += 1
            issues.append({"check": "fk_doc_application", "id": doc["document_id"]})
        else:
            passed_checks += 1

    # Decisions -> Applications
    for dec in decisions:
        total_checks += 1
        if dec["application_id"] not in app_ids:
            fk_failures += 1
            failed_checks += 1
            issues.append({"check": "fk_dec_application", "id": dec["decision_id"]})
        else:
            passed_checks += 1

    # 3. Lifecycle Validation
    dec_by_app = {d["application_id"]: d for d in decisions}
    for disb in disbursements:
        total_checks += 1
        dec = dec_by_app.get(disb["application_id"])
        if not dec or dec["decision_status"] == "REJECTED":
            lifecycle_violations += 1
            failed_checks += 1
            issues.append({"check": "lifecycle_disb_after_rejection", "id": disb["disbursement_id"]})
        else:
            passed_checks += 1

    # 4. Arithmetic Validation
    for aff in affordability_checks:
        total_checks += 1
        # Check that Disposable Income = Net - Debt - Proposed EMI
        net = Decimal(str(aff["monthly_net_income"]))
        debt = Decimal(str(aff["existing_monthly_debt"]))
        emi = Decimal(str(aff["proposed_monthly_emi"]))
        disp = Decimal(str(aff["disposable_income"]))
        expected_disp = (net - debt - emi).quantize(Decimal("0.01"))
        if abs(disp - expected_disp) > Decimal("0.05"):
            arithmetic_failures += 1
            failed_checks += 1
            issues.append({"check": "arithmetic_disposable_income", "id": aff["affordability_check_id"]})
        else:
            passed_checks += 1

    summary = {
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "warnings": warnings,
        "referential_integrity_failures": fk_failures,
        "arithmetic_failures": arithmetic_failures,
        "lifecycle_violations": lifecycle_violations,
        "issues_sample": issues[:10]
    }
    return summary


def write_validation_reports(summary: Dict[str, Any], output_dir: str = "reports"):
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "validation_summary.json")
    csv_path = os.path.join(output_dir, "validation_summary.csv")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        for k, v in summary.items():
            if k != "issues_sample":
                writer.writerow([k, v])

