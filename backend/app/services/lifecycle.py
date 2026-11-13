"""
Lifecycle State Machine Service: Enforces formal, independent state machines for:
1. Loan Application
2. Underwriting Decision
3. Document Verification
4. Disbursement Payout
5. Repayment Servicing

Strictly prevents unauthorized auto-disbursements and decouples approval from payout eligibility.
"""

from typing import Set, Dict, Any, List, Tuple, Optional

# ------------------------------------------------------------------------------
# 1. Loan Application State Machine
# ------------------------------------------------------------------------------
class ApplicationStateMachine:
    VALID_TRANSITIONS: Dict[str, Set[str]] = {
        "DRAFT": {"SUBMITTED", "CANCELLED"},
        "SUBMITTED": {"UNDER_REVIEW", "DOCUMENT_PENDING", "CANCELLED"},
        "DOCUMENT_PENDING": {"UNDER_REVIEW", "CANCELLED"},
        "UNDER_REVIEW": {"APPROVED", "REJECT", "REJECTED", "MANUAL_REVIEW", "DOCUMENT_PENDING", "PENDING_INFORMATION"},
        "PENDING_INFORMATION": {"UNDER_REVIEW", "CANCELLED"},
        "MANUAL_REVIEW": {"APPROVED", "REJECT", "REJECTED", "PENDING_INFORMATION"},
        "APPROVED": {"DISBURSED", "CANCELLED"},
        "DISBURSED": set(),  # Terminal state
        "REJECT": set(),     # Terminal state
        "REJECTED": set(),   # Terminal state
        "CANCELLED": set()   # Terminal state
    }

    @classmethod
    def can_transition(cls, current_state: str, target_state: str) -> bool:
        allowed = cls.VALID_TRANSITIONS.get(current_state, set())
        return target_state in allowed


# ------------------------------------------------------------------------------
# 2. Decision State Machine
# ------------------------------------------------------------------------------
class DecisionStateMachine:
    VALID_TRANSITIONS: Dict[str, Set[str]] = {
        "PENDING": {"EVALUATED"},
        "EVALUATED": {"UNDERWRITER_REVIEW", "FINALIZED", "OVERRIDDEN"},
        "UNDERWRITER_REVIEW": {"OVERRIDDEN", "FINALIZED"},
        "OVERRIDDEN": {"FINALIZED"},
        "FINALIZED": set()
    }

    @classmethod
    def can_transition(cls, current_state: str, target_state: str) -> bool:
        allowed = cls.VALID_TRANSITIONS.get(current_state, set())
        return target_state in allowed


# ------------------------------------------------------------------------------
# 3. Document Verification State Machine
# ------------------------------------------------------------------------------
class DocumentStateMachine:
    VALID_TRANSITIONS: Dict[str, Set[str]] = {
        "NOT_SUBMITTED": {"SUBMITTED"},
        "SUBMITTED": {"UNDER_REVIEW"},
        "UNDER_REVIEW": {"VERIFIED", "REJECTED", "EXPIRED"},
        "REJECTED": {"SUBMITTED"},  # Allow resubmission
        "EXPIRED": {"SUBMITTED"},   # Allow resubmission
        "VERIFIED": {"EXPIRED"}
    }

    @classmethod
    def can_transition(cls, current_state: str, target_state: str) -> bool:
        allowed = cls.VALID_TRANSITIONS.get(current_state, set())
        return target_state in allowed


# ------------------------------------------------------------------------------
# 4. Disbursement State Machine
# ------------------------------------------------------------------------------
class DisbursementStateMachine:
    VALID_TRANSITIONS: Dict[str, Set[str]] = {
        "NOT_ELIGIBLE": {"ELIGIBILITY_CHECKED"},
        "ELIGIBILITY_CHECKED": {"ELIGIBLE", "NOT_ELIGIBLE"},
        "ELIGIBLE": {"DISBURSEMENT_INITIATED", "NOT_ELIGIBLE"},
        "DISBURSEMENT_INITIATED": {"DISBURSED", "FAILED"},
        "FAILED": {"DISBURSEMENT_INITIATED", "REVERSED"},
        "DISBURSED": {"REVERSED"},
        "REVERSED": set()
    }

    @classmethod
    def can_transition(cls, current_state: str, target_state: str) -> bool:
        allowed = cls.VALID_TRANSITIONS.get(current_state, set())
        return target_state in allowed


# ------------------------------------------------------------------------------
# 5. Repayment State Machine
# ------------------------------------------------------------------------------
class RepaymentStateMachine:
    VALID_TRANSITIONS: Dict[str, Set[str]] = {
        "PENDING_DISBURSEMENT": {"ACTIVE"},
        "ACTIVE": {"PAID_OFF", "DELINQUENT"},
        "DELINQUENT": {"ACTIVE", "DEFAULTED", "PAID_OFF"},
        "DEFAULTED": {"PAID_OFF"},
        "PAID_OFF": set()
    }

    @classmethod
    def can_transition(cls, current_state: str, target_state: str) -> bool:
        allowed = cls.VALID_TRANSITIONS.get(current_state, set())
        return target_state in allowed


# ------------------------------------------------------------------------------
# Comprehensive Disbursement Prerequisite Gate
# ------------------------------------------------------------------------------
def evaluate_disbursement_prerequisites(
    application: Dict[str, Any],
    decision: Optional[Dict[str, Any]],
    documents: List[Dict[str, Any]],
    affordability: Optional[Dict[str, Any]],
    existing_disbursements: List[Dict[str, Any]]
) -> Tuple[bool, List[str]]:
    """
    Evaluates all strict prerequisite criteria before allowing loan disbursement.
    Returns: (is_eligible, list_of_failure_reasons)
    """
    reasons: List[str] = []

    # 1. Decision must exist and be APPROVED
    if not decision:
        reasons.append("No decision record exists for this application.")
    elif decision.get("decision_status") != "APPROVED":
        reasons.append(f"Decision is '{decision.get('decision_status')}', not APPROVED.")

    # 2. Mandatory documents must all be VERIFIED
    if not documents:
        reasons.append("Zero supporting documents submitted.")
    else:
        unverified = [d for d in documents if d.get("verification_status") != "VERIFIED"]
        if unverified:
            reasons.append(f"{len(unverified)} documents are unverified, rejected, or expired.")

    # 3. Affordability must be PASSED
    if not affordability:
        reasons.append("No affordability assessment record found.")
    elif affordability.get("affordability_status") != "PASSED":
        reasons.append(f"Affordability status is '{affordability.get('affordability_status')}', not PASSED.")

    # 4. Zero prior successful disbursement
    successful_prior = [
        d for d in existing_disbursements
        if d.get("application_id") == application.get("application_id")
        and d.get("disbursement_status") == "DISBURSED"
    ]
    if len(successful_prior) > 0:
        reasons.append("A completed successful disbursement already exists for this application.")

    is_eligible = (len(reasons) == 0)
    return is_eligible, reasons
