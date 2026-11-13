"""
Master Test Suite: 22 Mandatory Requirements Test Suite
Covers all unit, integration, mathematical, decision, anomaly, lifecycle, and reproducibility criteria.
"""

import pytest
from decimal import Decimal
import datetime

from backend.app.calculations.financial import (
    calculate_dti, calculate_foir, calculate_disposable_income,
    calculate_reducing_emi, generate_amortization_schedule,
    verify_schedule_reconciliation
)
from backend.app.rules_engine.engine import evaluate_application
from backend.app.anomaly_detection.detector import detect_operational_anomalies
from generator.anomaly_injection.injector import inject_anomalies
from generator.master_data.applicants import generate_applicants
from generator.master_data.products import get_loan_products
from generator.transaction_data.applications import generate_applications
from generator.transaction_data.documents import generate_documents
from generator.transaction_data.affordability import generate_affordability_checks
from generator.transaction_data.decisions import generate_decisions
from generator.transaction_data.repayments import generate_repayment_schedules
from generator.transaction_data.disbursements import generate_disbursements


# 1. Deterministic ID generation
def test_01_deterministic_id_generation():
    apps1 = generate_applicants(10, seed=20261022)
    apps2 = generate_applicants(10, seed=20261022)
    for a1, a2 in zip(apps1, apps2):
        assert a1["applicant_id"] == a2["applicant_id"]
        assert a1["applicant_id"].startswith("APP-2026-")


# 2. Primary-key uniqueness
def test_02_primary_key_uniqueness():
    applicants = generate_applicants(100, seed=20261022)
    ids = [a["applicant_id"] for a in applicants]
    assert len(ids) == len(set(ids))


# 3. Foreign-key validation
def test_03_foreign_key_validation():
    products = get_loan_products("config/business_rules.yaml")
    applicants = generate_applicants(20, seed=20261022)
    applications = generate_applications(15, applicants, products, seed=20261022)
    app_ids = {a["applicant_id"] for a in applicants}
    prod_ids = {p["product_id"] for p in products}
    for app in applications:
        assert app["applicant_id"] in app_ids
        assert app["product_id"] in prod_ids


# 4. Product eligibility (RULE_01)
def test_04_product_eligibility():
    product = {"min_principal": 50000, "max_principal": 500000, "min_term_months": 12, "max_term_months": 60, "minimum_credit_score": 650, "maximum_dti": 50, "maximum_foir": 60}
    app = {"requested_principal": 900000, "requested_term_months": 24}
    res = evaluate_application(app, product, {"credit_score": 750}, {"debt_to_income_ratio": 20, "fixed_obligation_ratio": 30}, [], [])
    assert res.status == "REJECT"
    assert "RULE_01" in res.rules_triggered


# 5. DTI calculation
def test_05_dti_calculation():
    dti = calculate_dti(20000, 80000)
    assert dti == Decimal("25.00")


# 6. FOIR calculation
def test_06_foir_calculation():
    foir = calculate_foir(10000, 15000, 50000)
    assert foir == Decimal("50.00")


# 7. EMI calculation (reducing-balance)
def test_07_emi_calculation():
    emi = calculate_reducing_emi(100000, 12.0, 12)
    assert emi == Decimal("8884.88")


# 8. Zero-interest loan handling
def test_08_zero_interest_loan_handling():
    emi = calculate_reducing_emi(120000, 0.0, 12)
    assert emi == Decimal("10000.00")


# 9. Repayment reconciliation
def test_09_repayment_reconciliation():
    schedule = generate_amortization_schedule(
        application_id="LOAN-2026-TEST",
        principal=Decimal("500000.00"),
        annual_interest_rate=Decimal("10.50"),
        term_months=24,
        disbursement_date=datetime.date(2026, 1, 15)
    )
    reconciled, details = verify_schedule_reconciliation(Decimal("500000.00"), schedule)
    assert reconciled is True
    assert details["final_closing_balance"] == Decimal("0.00")


# 10. Missing income proof (RULE_05)
def test_10_missing_income_proof():
    product = {"min_principal": 50000, "max_principal": 500000, "min_term_months": 12, "max_term_months": 60, "minimum_credit_score": 650, "maximum_dti": 50, "maximum_foir": 60}
    app = {"requested_principal": 100000, "requested_term_months": 24}
    docs = [{"document_type": "IDENTITY_PROOF", "verification_status": "VERIFIED"}]
    res = evaluate_application(app, product, {"credit_score": 750}, {"debt_to_income_ratio": 20, "fixed_obligation_ratio": 30}, docs, [])
    assert res.status == "PENDING_INFORMATION"
    assert "RULE_05" in res.rules_triggered


# 11. High debt burden (RULE_03 & RULE_04)
def test_11_high_debt_burden():
    product = {"min_principal": 50000, "max_principal": 500000, "min_term_months": 12, "max_term_months": 60, "minimum_credit_score": 650, "maximum_dti": 40, "maximum_foir": 50}
    app = {"requested_principal": 100000, "requested_term_months": 24}
    res = evaluate_application(app, product, {"credit_score": 750}, {"debt_to_income_ratio": 65, "fixed_obligation_ratio": 75}, [], [])
    assert res.status == "REJECT"
    assert ("RULE_03" in res.rules_triggered) or ("RULE_04" in res.rules_triggered)


# 12. Unstable employment (RULE_06)
def test_12_unstable_employment():
    product = {"min_principal": 50000, "max_principal": 500000, "min_term_months": 12, "max_term_months": 60, "minimum_credit_score": 650, "maximum_dti": 50, "maximum_foir": 60}
    app = {"requested_principal": 100000, "requested_term_months": 24}
    docs = [{"document_type": "INCOME_PROOF", "verification_status": "VERIFIED"}]
    emps = [{"employment_type": "UNEMPLOYED", "employment_status": "TERMINATED"}]
    res = evaluate_application(app, product, {"credit_score": 750}, {"debt_to_income_ratio": 20, "fixed_obligation_ratio": 30}, docs, emps)
    assert res.status == "MANUAL_REVIEW"
    assert "RULE_06" in res.rules_triggered


# 13. Duplicate application (RULE_07)
def test_13_duplicate_application():
    product = {"min_principal": 50000, "max_principal": 500000, "min_term_months": 12, "max_term_months": 60, "minimum_credit_score": 650, "maximum_dti": 50, "maximum_foir": 60}
    app = {"requested_principal": 100000, "requested_term_months": 24}
    docs = [{"document_type": "INCOME_PROOF", "verification_status": "VERIFIED"}]
    res = evaluate_application(app, product, {"credit_score": 750}, {"debt_to_income_ratio": 20, "fixed_obligation_ratio": 30}, docs, [], active_application_count=2)
    assert res.status == "MANUAL_REVIEW"
    assert "RULE_07" in res.rules_triggered


# 14. Borderline credit score (RULE_08)
def test_14_borderline_credit_score():
    product = {"min_principal": 50000, "max_principal": 500000, "min_term_months": 12, "max_term_months": 60, "minimum_credit_score": 650, "maximum_dti": 50, "maximum_foir": 60}
    app = {"requested_principal": 100000, "requested_term_months": 24}
    docs = [{"document_type": "INCOME_PROOF", "verification_status": "VERIFIED"}]
    res = evaluate_application(app, product, {"credit_score": 660}, {"debt_to_income_ratio": 20, "fixed_obligation_ratio": 30}, docs, [])
    assert res.status == "MANUAL_REVIEW"
    assert "RULE_08" in res.rules_triggered


# 15. Invalid loan term anomaly
def test_15_invalid_loan_term():
    product = {"product_id": "P1", "min_principal": 50000, "max_principal": 500000, "min_term_months": 12, "max_term_months": 60}
    app = {"application_id": "APP_BAD_TERM", "product_id": "P1", "requested_term_months": 120, "requested_principal": 100000}
    detected = detect_operational_anomalies([app], [product], [], [], [], [], [], [], [])
    assert any(d.issue_type == "INVALID_TERM" for d in detected)


# 16. Decision-before-checks anomaly
def test_16_decision_before_checks_anomaly():
    now = datetime.datetime.now(datetime.timezone.utc)
    dec = {"decision_id": "D1", "application_id": "A1", "decision_timestamp": now - datetime.timedelta(hours=2)}
    aff = {"application_id": "A1", "assessment_timestamp": now}
    detected = detect_operational_anomalies([], [], [dec], [aff], [], [], [], [], [])
    assert any(d.issue_type == "DECISION_BEFORE_CHECKS" for d in detected)


# 17. Income-source conflict anomaly
def test_17_income_source_conflict_anomaly():
    emp = {"applicant_id": "APP1", "employment_type": "SALARIED", "monthly_salary": Decimal("50000.00")}
    inc = {"applicant_id": "APP1", "income_record_id": "INC1", "income_source": "PRIMARY_SALARY", "gross_monthly_income": Decimal("180000.00")}
    detected = detect_operational_anomalies([], [], [], [], [], [inc], [emp], [], [])
    assert any(d.issue_type == "INCOME_SOURCE_CONFLICT" for d in detected)


# 18. Duplicate disbursement anomaly
def test_18_duplicate_disbursement_anomaly():
    d1 = {"disbursement_id": "D1", "application_id": "APP_X", "disbursement_status": "DISBURSED"}
    d2 = {"disbursement_id": "D2", "application_id": "APP_X", "disbursement_status": "DISBURSED"}
    detected = detect_operational_anomalies([], [], [], [], [], [], [], [d1, d2], [])
    assert any(d.issue_type == "DUPLICATE_DISBURSEMENT" for d in detected)


# 19. No disbursement after rejection
def test_19_no_disbursement_after_rejection():
    apps = [{"application_id": "A1", "requested_principal": Decimal("100000.00")}]
    decs = [{"application_id": "A1", "decision_status": "REJECT"}]
    docs = [{"application_id": "A1", "verification_status": "VERIFIED"}]
    affs = [{"application_id": "A1", "affordability_status": "PASSED"}]
    disb, _ = generate_disbursements(apps, decs, docs, affs)
    assert len(disb) == 0


# 20. No disbursement before document verification
def test_20_no_disbursement_before_doc_verification():
    apps = [{"application_id": "A1", "requested_principal": Decimal("100000.00")}]
    decs = [{"application_id": "A1", "decision_status": "APPROVED", "decision_timestamp": datetime.datetime.now(datetime.timezone.utc)}]
    docs = [{"application_id": "A1", "verification_status": "PENDING"}]
    affs = [{"application_id": "A1", "affordability_status": "PASSED"}]
    disb, _ = generate_disbursements(apps, decs, docs, affs)
    assert len(disb) == 0


# 21. Ground-truth data leakage prevention
def test_21_ground_truth_data_leakage_prevention():
    # Verify AnomalyDetector signature doesn't take ground truth
    import inspect
    sig = inspect.signature(detect_operational_anomalies)
    param_names = list(sig.parameters.keys())
    assert "ground_truth" not in param_names
    assert "ground_truth_records" not in param_names
    assert "labels" not in param_names


# 22. Fixed-seed reproducibility
def test_22_fixed_seed_reproducibility():
    a1 = generate_applicants(50, seed=20261022)
    a2 = generate_applicants(50, seed=20261022)
    for x, y in zip(a1, a2):
        assert x["applicant_id"] == y["applicant_id"]
        assert x["email"] == y["email"]
        assert x["credit_score"] == y["credit_score"]

