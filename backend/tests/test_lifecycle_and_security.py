"""
Unit & Integration Tests: Lifecycle State Machines & RBAC Security Services.
Verifies strict state transitions, disbursement prerequisite validation,
underwriter override workflows, PBKDF2 password hashing, and token authentication.
"""

import pytest
import datetime
from decimal import Decimal
from fastapi import HTTPException

from backend.app.services.lifecycle import (
    ApplicationStateMachine,
    DecisionStateMachine,
    DocumentStateMachine,
    DisbursementStateMachine,
    RepaymentStateMachine,
    evaluate_disbursement_prerequisites
)
from backend.app.services.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    get_current_user,
    DEMO_USERS
)
from backend.app.rules_engine.engine import apply_underwriter_override


# ------------------------------------------------------------------------------
# 1. State Machine Tests
# ------------------------------------------------------------------------------
def test_application_state_machine_valid_and_invalid():
    # Valid transitions
    assert ApplicationStateMachine.can_transition("DRAFT", "SUBMITTED") is True
    assert ApplicationStateMachine.can_transition("SUBMITTED", "UNDER_REVIEW") is True
    assert ApplicationStateMachine.can_transition("UNDER_REVIEW", "APPROVED") is True
    assert ApplicationStateMachine.can_transition("APPROVED", "DISBURSED") is True

    # Invalid transitions (Terminal state violation / skipping stages)
    assert ApplicationStateMachine.can_transition("REJECTED", "APPROVED") is False
    assert ApplicationStateMachine.can_transition("DISBURSED", "UNDER_REVIEW") is False
    assert ApplicationStateMachine.can_transition("DRAFT", "DISBURSED") is False


def test_disbursement_state_machine():
    assert DisbursementStateMachine.can_transition("NOT_ELIGIBLE", "ELIGIBILITY_CHECKED") is True
    assert DisbursementStateMachine.can_transition("ELIGIBLE", "DISBURSEMENT_INITIATED") is True
    assert DisbursementStateMachine.can_transition("DISBURSEMENT_INITIATED", "DISBURSED") is True
    # Can't directly jump from NOT_ELIGIBLE to DISBURSED
    assert DisbursementStateMachine.can_transition("NOT_ELIGIBLE", "DISBURSED") is False


def test_repayment_state_machine():
    assert RepaymentStateMachine.can_transition("PENDING_DISBURSEMENT", "ACTIVE") is True
    assert RepaymentStateMachine.can_transition("ACTIVE", "PAID_OFF") is True
    assert RepaymentStateMachine.can_transition("ACTIVE", "DELINQUENT") is True
    assert RepaymentStateMachine.can_transition("DELINQUENT", "DEFAULTED") is True
    assert RepaymentStateMachine.can_transition("PAID_OFF", "ACTIVE") is False


# ------------------------------------------------------------------------------
# 2. Disbursement Prerequisite Gate Tests
# ------------------------------------------------------------------------------
def test_disbursement_prerequisites_all_passing():
    app = {"application_id": "APP-001"}
    decision = {"decision_status": "APPROVED"}
    documents = [{"verification_status": "VERIFIED"}]
    affordability = {"affordability_status": "PASSED"}
    disbursements = []

    is_eligible, reasons = evaluate_disbursement_prerequisites(app, decision, documents, affordability, disbursements)
    assert is_eligible is True
    assert len(reasons) == 0


def test_disbursement_prerequisites_blocked_by_rejection():
    app = {"application_id": "APP-002"}
    decision = {"decision_status": "REJECT"}
    documents = [{"verification_status": "VERIFIED"}]
    affordability = {"affordability_status": "PASSED"}
    disbursements = []

    is_eligible, reasons = evaluate_disbursement_prerequisites(app, decision, documents, affordability, disbursements)
    assert is_eligible is False
    assert any("REJECT" in r for r in reasons)


def test_disbursement_prerequisites_blocked_by_pending_docs():
    app = {"application_id": "APP-003"}
    decision = {"decision_status": "APPROVED"}
    documents = [{"verification_status": "PENDING"}]
    affordability = {"affordability_status": "PASSED"}
    disbursements = []

    is_eligible, reasons = evaluate_disbursement_prerequisites(app, decision, documents, affordability, disbursements)
    assert is_eligible is False
    assert any("documents are unverified" in r for r in reasons)


def test_disbursement_prerequisites_blocked_by_prior_disbursement():
    app = {"application_id": "APP-004"}
    decision = {"decision_status": "APPROVED"}
    documents = [{"verification_status": "VERIFIED"}]
    affordability = {"affordability_status": "PASSED"}
    disbursements = [{"application_id": "APP-004", "disbursement_status": "DISBURSED"}]

    is_eligible, reasons = evaluate_disbursement_prerequisites(app, decision, documents, affordability, disbursements)
    assert is_eligible is False
    assert any("already exists" in r for r in reasons)


# ------------------------------------------------------------------------------
# 3. Underwriter Override Tests
# ------------------------------------------------------------------------------
def test_underwriter_override_workflow():
    dec = {
        "decision_id": "DEC-2026-000001",
        "application_id": "APP-2026-000001",
        "decision_status": "MANUAL_REVIEW",
        "decision_reason_code": "BORDERLINE_CREDIT_SCORE",
        "decision_explanation": "Credit score in review band."
    }

    override_record = apply_underwriter_override(
        decision=dec,
        underwriter_id="UW-OFFICER-7",
        new_status="APPROVED",
        reason="Compensating factors: verified liquid reserves exceeding 12 months debt service."
    )

    assert dec["decision_status"] == "APPROVED"
    assert dec["decision_reason_code"] == "OVERRIDE_APPROVED"
    assert "UW-OFFICER-7" in dec["decision_explanation"]

    assert override_record["decision_id"] == "DEC-2026-000001"
    assert override_record["previous_status"] == "MANUAL_REVIEW"
    assert override_record["overridden_status"] == "APPROVED"
    assert override_record["underwriter_id"] == "UW-OFFICER-7"


# ------------------------------------------------------------------------------
# 4. Security & PBKDF2 Password Hashing Tests
# ------------------------------------------------------------------------------
def test_password_hashing_and_verification():
    pwd = "SecureBankingPassword@2026"
    stored_hash = hash_password(pwd)
    assert verify_password(stored_hash, pwd) is True
    assert verify_password(stored_hash, "WrongPassword") is False


def test_jwt_token_creation_and_validation():
    user = DEMO_USERS["reviewer@bank.org"]
    token = create_access_token(user)
    payload = decode_access_token(token)

    assert payload["sub"] == "reviewer@bank.org"
    assert payload["role"] == "RISK_REVIEWER"

    # Tampered token test
    tampered = token[:-4] + "xxxx"
    with pytest.raises(HTTPException):
        decode_access_token(tampered)


def test_expired_token_rejection():
    user = DEMO_USERS["customer@bank.org"]
    # Create expired token 1 hour in the past
    expired_token = create_access_token(user, expires_delta=datetime.timedelta(hours=-1))
    with pytest.raises(HTTPException) as excinfo:
        decode_access_token(expired_token)
    assert excinfo.value.status_code == 401
    assert "Invalid or expired" in excinfo.value.detail


def test_unauthenticated_request_rejected():
    with pytest.raises(HTTPException) as excinfo:
        get_current_user(credentials=None)
    assert excinfo.value.status_code == 401
    assert "not provided" in excinfo.value.detail


def test_auth_me_sanitizes_credentials():
    from backend.app.api.routers.auth import get_current_profile
    user = DEMO_USERS["admin@bank.org"]
    profile = get_current_profile(user=user)
    profile_dict = profile.model_dump() if hasattr(profile, "model_dump") else (profile if isinstance(profile, dict) else profile.__dict__)
    assert "password_hash" not in profile_dict
    assert "password" not in profile_dict
    assert "secret" not in profile_dict
    assert (profile.email if hasattr(profile, "email") else profile_dict["email"]) == "admin@bank.org"
    assert (profile.role if hasattr(profile, "role") else profile_dict["role"]) == "ADMIN"


def test_all_demo_users_exclude_password_and_hash():
    from backend.app.api.routers.auth import get_current_profile
    for email, user in DEMO_USERS.items():
        profile = get_current_profile(user=user)
        p_dict = profile.model_dump() if hasattr(profile, "model_dump") else (profile if isinstance(profile, dict) else profile.__dict__)
        assert "password_hash" not in p_dict
        assert "password" not in p_dict
        assert "secret_key" not in p_dict
        assert p_dict["role"] in ["ADMIN", "RISK_REVIEWER", "OPERATIONS_ANALYST", "CUSTOMER"]
        assert len(p_dict["email"]) > 0


def test_profile_aware_anomaly_evaluation_regression():
    from backend.app.evaluation.evaluator import evaluate_anomalies
    gt = [
        {"record_id": "REC-1", "issue_type": "INVALID_TERM"},
        {"record_id": "REC-2", "issue_type": "SCHEDULE_RECONCILIATION_FAILURE"}
    ]
    det = [
        {"record_id": "REC-1", "issue_type": "INVALID_TERM"},
        {"record_id": "REC-2", "issue_type": "SCHEDULE_RECONCILIATION_FAILURE"}
    ]
    res = evaluate_anomalies(gt, det, profile="starter", seed=20261022)
    assert res["metadata"]["profile"] == "starter"
    assert res["summary"]["precision"] == 1.0
    assert res["summary"]["recall"] == 1.0
    assert res["summary"]["f1_score"] == 1.0


def test_customer_data_boundary_enforcement():
    import pytest
    from fastapi import HTTPException
    from backend.app.database.connection import SessionLocal
    from backend.app.api.routers.applications import get_application_detail
    from backend.app.services.security import DEMO_USERS

    db = SessionLocal()
    try:
        cust_user = DEMO_USERS["customer@bank.org"]
        # 1. Customer accessing own application LOAN-2026-000001 -> 200 OK
        detail = get_application_detail("LOAN-2026-000001", db=db, user=cust_user)
        assert detail["application_id"] == "LOAN-2026-000001"

        # 2. Customer accessing other borrower LOAN-2026-000002 -> HTTPException 403 Forbidden
        with pytest.raises(HTTPException) as exc_info:
            get_application_detail("LOAN-2026-000002", db=db, user=cust_user)
        assert exc_info.value.status_code == 403
        assert "Forbidden" in exc_info.value.detail
    finally:
        db.close()



