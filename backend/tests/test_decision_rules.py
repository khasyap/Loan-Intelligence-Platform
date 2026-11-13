import pytest
from decimal import Decimal
from backend.app.rules_engine.engine import evaluate_application

@pytest.fixture
def base_context():
    product = {
        "product_id": "PROD-001",
        "min_principal": 50000.0,
        "max_principal": 1000000.0,
        "min_term_months": 12,
        "max_term_months": 60,
        "minimum_credit_score": 650,
        "maximum_dti": 45.0,
        "maximum_foir": 55.0
    }
    applicant = {
        "applicant_id": "APP-2026-000001",
        "credit_score": 750
    }
    application = {
        "application_id": "LOAN-2026-000001",
        "requested_principal": 300000.0,
        "requested_term_months": 36
    }
    affordability = {
        "debt_to_income_ratio": Decimal("20.00"),
        "fixed_obligation_ratio": Decimal("35.00"),
        "disposable_income": Decimal("40000.00")
    }
    documents = [
        {"document_type": "IDENTITY_PROOF", "verification_status": "VERIFIED"},
        {"document_type": "INCOME_PROOF", "verification_status": "VERIFIED"}
    ]
    employments = [
        {"employment_status": "CURRENT", "employment_type": "SALARIED"}
    ]
    return {
        "product": product,
        "applicant": applicant,
        "application": application,
        "affordability": affordability,
        "documents": documents,
        "employments": employments
    }


def test_clean_application_approval(base_context):
    res = evaluate_application(**base_context)
    assert res.status == "APPROVED"
    assert res.reason_code == "APP_CLEAN_APPROVAL"
    assert "RULE_10" in res.rules_triggered


def test_rule_01_principal_out_of_bounds(base_context):
    base_context["application"]["requested_principal"] = 2500000.0  # Max is 1,000,000
    res = evaluate_application(**base_context)
    assert res.status == "REJECT"
    assert res.reason_code == "REJ_PRODUCT_LIMITS_BREACH"
    assert "RULE_01" in res.rules_triggered


def test_rule_02_credit_score_below_cutoff(base_context):
    base_context["applicant"]["credit_score"] = 580  # Min is 650
    res = evaluate_application(**base_context)
    assert res.status == "REJECT"
    assert res.reason_code == "REJ_CREDIT_SCORE_BELOW_MIN"
    assert "RULE_02" in res.rules_triggered


def test_rule_03_dti_severe_overburden(base_context):
    base_context["affordability"]["debt_to_income_ratio"] = Decimal("65.00")  # Max is 45, 1.25x is 56.25
    res = evaluate_application(**base_context)
    assert res.status == "REJECT"
    assert res.reason_code == "REJ_DTI_EXCEEDED"
    assert "RULE_03" in res.rules_triggered


def test_rule_03_dti_borderline(base_context):
    base_context["affordability"]["debt_to_income_ratio"] = Decimal("48.00")  # Max is 45, < 56.25
    res = evaluate_application(**base_context)
    assert res.status == "MANUAL_REVIEW"
    assert res.reason_code == "REV_DTI_BORDERLINE"
    assert "RULE_03" in res.rules_triggered


def test_rule_05_missing_income_proof(base_context):
    base_context["documents"] = [
        {"document_type": "IDENTITY_PROOF", "verification_status": "VERIFIED"}
    ]
    res = evaluate_application(**base_context)
    assert res.status == "PENDING_INFORMATION"
    assert res.reason_code == "REV_INCOME_PROOF_MISSING"
    assert "RULE_05" in res.rules_triggered


def test_rule_08_borderline_credit_score(base_context):
    base_context["applicant"]["credit_score"] = 660  # Min is 650, 660 is within [650, 675)
    res = evaluate_application(**base_context)
    assert res.status == "MANUAL_REVIEW"
    assert res.reason_code == "REV_CREDIT_SCORE_BORDERLINE"
    assert "RULE_08" in res.rules_triggered

