"""
Explainable Decision Rules Engine: Deterministic Underwriting Rules with
Formal Precedence, Tiered Severity, Conflict Resolution, and Human Override Support.
Strictly excludes protected attributes.
"""

from decimal import Decimal
from typing import Dict, Any, List, Optional
import json
import datetime

class DecisionResult:
    def __init__(
        self,
        status: str,
        reason_code: str,
        explanation: str,
        risk_score: int,
        rules_triggered: List[str],
        rule_executions: List[Dict[str, Any]],
        rule_version: str = "v1.0.0",
        requires_manual_review: bool = False
    ):
        self.status = status
        self.reason_code = reason_code
        self.explanation = explanation
        self.risk_score = risk_score
        self.rules_triggered = rules_triggered
        self.rule_executions = rule_executions
        self.rule_version = rule_version
        self.requires_manual_review = requires_manual_review

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_status": self.status,
            "decision_reason_code": self.reason_code,
            "decision_explanation": self.explanation,
            "risk_score": self.risk_score,
            "rules_triggered": json.dumps(self.rules_triggered),
            "rule_version": self.rule_version,
            "requires_manual_review": self.requires_manual_review,
            "rule_executions": self.rule_executions
        }


def evaluate_application(
    application: Dict[str, Any],
    product: Dict[str, Any],
    applicant: Dict[str, Any],
    affordability: Dict[str, Any],
    documents: List[Dict[str, Any]],
    employments: List[Dict[str, Any]],
    active_application_count: int = 1
) -> DecisionResult:
    """
    Evaluates an application against the 10 deterministic underwriting rules
    using formal severity precedence:
    1. HARD_FAIL (Strict Block -> REJECT)
    2. SOFT_FAIL_PENDING (Missing Documentation -> PENDING_INFORMATION)
    3. SOFT_FAIL_REVIEW (Discretionary Exception -> MANUAL_REVIEW)
    4. PASS (Full Compliance -> APPROVED)
    """
    rule_version = "v1.0.0"
    executions: List[Dict[str, Any]] = []
    triggered_rules: List[str] = []

    req_principal = Decimal(str(application.get("requested_principal", 0)))
    req_term = int(application.get("requested_term_months", 0))

    prod_min_p = Decimal(str(product.get("min_principal", 0)))
    prod_max_p = Decimal(str(product.get("max_principal", 0)))
    prod_min_term = int(product.get("min_term_months", 0))
    prod_max_term = int(product.get("max_term_months", 0))
    prod_min_score = int(product.get("minimum_credit_score", 650))
    prod_max_dti = Decimal(str(product.get("maximum_dti", 50.0)))
    prod_max_foir = Decimal(str(product.get("maximum_foir", 60.0)))

    credit_score = int(applicant.get("credit_score", 300))
    dti = Decimal(str(affordability.get("debt_to_income_ratio", 0)))
    foir = Decimal(str(affordability.get("fixed_obligation_ratio", 0)))

    risk_score = credit_score

    hard_fails: List[Dict[str, str]] = []
    pending_fails: List[Dict[str, str]] = []
    review_fails: List[Dict[str, str]] = []

    # --------------------------------------------------------------------------
    # RULE 01: Product Eligibility Limits (Priority 1 - HARD_FAIL)
    # --------------------------------------------------------------------------
    r1_triggered = False
    r1_msg = ""
    if req_principal < prod_min_p or req_principal > prod_max_p:
        r1_triggered = True
        r1_msg = f"Requested principal ₹{req_principal:,.2f} is outside product range [₹{prod_min_p:,.2f}, ₹{prod_max_p:,.2f}]."
    elif req_term < prod_min_term or req_term > prod_max_term:
        r1_triggered = True
        r1_msg = f"Requested tenure {req_term} months is outside product range [{prod_min_term}, {prod_max_term}] months."

    executions.append({
        "rule_id": "RULE_01",
        "rule_version": rule_version,
        "evaluated_values": json.dumps({"principal": str(req_principal), "term": req_term}),
        "is_triggered": r1_triggered,
        "triggered_action": "REJECT" if r1_triggered else None
    })
    if r1_triggered:
        triggered_rules.append("RULE_01")
        hard_fails.append({"code": "REJ_PRODUCT_LIMITS_BREACH", "msg": r1_msg})

    # --------------------------------------------------------------------------
    # RULE 02: Minimum Credit Score (Priority 2 - HARD_FAIL)
    # --------------------------------------------------------------------------
    r2_triggered = credit_score < prod_min_score
    executions.append({
        "rule_id": "RULE_02",
        "rule_version": rule_version,
        "evaluated_values": json.dumps({"credit_score": credit_score, "min_score": prod_min_score}),
        "is_triggered": r2_triggered,
        "triggered_action": "REJECT" if r2_triggered else None
    })
    if r2_triggered:
        triggered_rules.append("RULE_02")
        hard_fails.append({
            "code": "REJ_CREDIT_SCORE_BELOW_MIN",
            "msg": f"Credit bureau score {credit_score} is below product cutoff of {prod_min_score}."
        })

    # --------------------------------------------------------------------------
    # RULE 03: Debt-to-Income (DTI) Limit (Priority 3 - HARD/SOFT FAIL)
    # --------------------------------------------------------------------------
    r3_hard = dti > (prod_max_dti * Decimal("1.25"))
    r3_soft = dti > prod_max_dti
    executions.append({
        "rule_id": "RULE_03",
        "rule_version": rule_version,
        "evaluated_values": json.dumps({"dti": str(dti), "max_dti": str(prod_max_dti)}),
        "is_triggered": r3_soft or r3_hard,
        "triggered_action": "REJECT" if r3_hard else ("MANUAL_REVIEW" if r3_soft else None)
    })
    if r3_hard:
        triggered_rules.append("RULE_03")
        hard_fails.append({
            "code": "REJ_DTI_EXCEEDED",
            "msg": f"DTI {dti:.2f}% severely exceeds allowable threshold of {prod_max_dti:.2f}%."
        })
    elif r3_soft:
        triggered_rules.append("RULE_03")
        review_fails.append({
            "code": "REV_DTI_BORDERLINE",
            "msg": f"DTI {dti:.2f}% exceeds product benchmark of {prod_max_dti:.2f}%; underwriter review required."
        })

    # --------------------------------------------------------------------------
    # RULE 04: Fixed Obligation to Income Ratio (FOIR) (Priority 4 - HARD/SOFT)
    # --------------------------------------------------------------------------
    r4_hard = foir > (prod_max_foir * Decimal("1.15"))
    r4_soft = foir > prod_max_foir
    executions.append({
        "rule_id": "RULE_04",
        "rule_version": rule_version,
        "evaluated_values": json.dumps({"foir": str(foir), "max_foir": str(prod_max_foir)}),
        "is_triggered": r4_soft or r4_hard,
        "triggered_action": "REJECT" if r4_hard else ("MANUAL_REVIEW" if r4_soft else None)
    })
    if r4_hard:
        triggered_rules.append("RULE_04")
        hard_fails.append({
            "code": "REJ_FOIR_EXCEEDED",
            "msg": f"FOIR {foir:.2f}% severely breaches repayment capacity limit of {prod_max_foir:.2f}%."
        })
    elif r4_soft:
        triggered_rules.append("RULE_04")
        review_fails.append({
            "code": "REV_FOIR_BORDERLINE",
            "msg": f"FOIR {foir:.2f}% exceeds guideline of {prod_max_foir:.2f}%; underwriter review required."
        })

    # --------------------------------------------------------------------------
    # RULE 05: Mandatory Income Proof (Priority 5 - SOFT_FAIL)
    # --------------------------------------------------------------------------
    has_income_doc = any(
        d.get("document_type") in ("INCOME_PROOF", "BANK_STATEMENT") and d.get("verification_status") == "VERIFIED"
        for d in documents
    )
    executions.append({
        "rule_id": "RULE_05",
        "rule_version": rule_version,
        "evaluated_values": json.dumps({"has_verified_income_doc": has_income_doc}),
        "is_triggered": not has_income_doc,
        "triggered_action": "PENDING_INFORMATION" if not has_income_doc else None
    })
    if not has_income_doc:
        triggered_rules.append("RULE_05")
        pending_fails.append({
            "code": "REV_INCOME_PROOF_MISSING",
            "msg": "Mandatory income proof or bank statement is unverified or missing."
        })

    # --------------------------------------------------------------------------
    # RULE 06: Employment Stability (Priority 6 - SOFT_FAIL)
    # --------------------------------------------------------------------------
    is_unemployed = any(e.get("employment_type") == "UNEMPLOYED" for e in employments)
    has_active_emp = any(e.get("employment_status") == "CURRENT" for e in employments)
    r6_triggered = is_unemployed or (not has_active_emp and len(employments) > 0)
    executions.append({
        "rule_id": "RULE_06",
        "rule_version": rule_version,
        "evaluated_values": json.dumps({"is_unemployed": is_unemployed, "has_active_emp": has_active_emp}),
        "is_triggered": r6_triggered,
        "triggered_action": "MANUAL_REVIEW" if r6_triggered else None
    })
    if r6_triggered:
        triggered_rules.append("RULE_06")
        review_fails.append({
            "code": "REV_EMPLOYMENT_UNSTABLE",
            "msg": "Employment status indicates unemployed or discontinuous tenure."
        })

    # --------------------------------------------------------------------------
    # RULE 07: Duplicate Active Application (Priority 7 - SOFT_FAIL)
    # --------------------------------------------------------------------------
    r7_triggered = active_application_count > 1
    executions.append({
        "rule_id": "RULE_07",
        "rule_version": rule_version,
        "evaluated_values": json.dumps({"active_application_count": active_application_count}),
        "is_triggered": r7_triggered,
        "triggered_action": "MANUAL_REVIEW" if r7_triggered else None
    })
    if r7_triggered:
        triggered_rules.append("RULE_07")
        review_fails.append({
            "code": "REV_DUPLICATE_APPLICATION",
            "msg": f"Applicant has {active_application_count} concurrent active applications."
        })

    # --------------------------------------------------------------------------
    # RULE 08: Borderline Credit Score (Priority 8 - SOFT_FAIL)
    # --------------------------------------------------------------------------
    r8_triggered = (prod_min_score <= credit_score < (prod_min_score + 25))
    executions.append({
        "rule_id": "RULE_08",
        "rule_version": rule_version,
        "evaluated_values": json.dumps({"credit_score": credit_score, "cutoff": prod_min_score}),
        "is_triggered": r8_triggered,
        "triggered_action": "MANUAL_REVIEW" if r8_triggered else None
    })
    if r8_triggered:
        triggered_rules.append("RULE_08")
        review_fails.append({
            "code": "REV_CREDIT_SCORE_BORDERLINE",
            "msg": f"Credit score {credit_score} is borderline (within 25 points of cutoff {prod_min_score})."
        })

    # --------------------------------------------------------------------------
    # RULE 09: Document Verification Failure (Priority 9 - HARD/SOFT FAIL)
    # --------------------------------------------------------------------------
    has_rejected_doc = any(d.get("verification_status") == "REJECTED" for d in documents)
    has_expired_doc = any(d.get("verification_status") == "EXPIRED" for d in documents)
    executions.append({
        "rule_id": "RULE_09",
        "rule_version": rule_version,
        "evaluated_values": json.dumps({"has_rejected_doc": has_rejected_doc, "has_expired_doc": has_expired_doc}),
        "is_triggered": has_rejected_doc or has_expired_doc,
        "triggered_action": "REJECT" if has_rejected_doc else ("PENDING_INFORMATION" if has_expired_doc else None)
    })
    if has_rejected_doc:
        triggered_rules.append("RULE_09")
        hard_fails.append({
            "code": "REJ_DOC_VERIF_FAILED",
            "msg": "One or more mandatory documents failed verification."
        })
    elif has_expired_doc:
        triggered_rules.append("RULE_09")
        pending_fails.append({
            "code": "REV_DOC_EXPIRED",
            "msg": "One or more submitted documents have expired."
        })

    # --------------------------------------------------------------------------
    # RULE 10: Clean Application Approval (Priority 10 - PASS)
    # --------------------------------------------------------------------------
    is_clean = len(hard_fails) == 0 and len(pending_fails) == 0 and len(review_fails) == 0
    executions.append({
        "rule_id": "RULE_10",
        "rule_version": rule_version,
        "evaluated_values": json.dumps({"all_checks_passed": is_clean}),
        "is_triggered": is_clean,
        "triggered_action": "APPROVED" if is_clean else None
    })

    # --------------------------------------------------------------------------
    # Final Decision Aggregation & Conflict Resolution
    # --------------------------------------------------------------------------
    if len(hard_fails) > 0:
        # Hard fail always dominates
        primary_fail = hard_fails[0]
        return DecisionResult(
            status="REJECT",
            reason_code=primary_fail["code"],
            explanation=primary_fail["msg"],
            risk_score=risk_score,
            rules_triggered=triggered_rules,
            rule_executions=executions,
            rule_version=rule_version,
            requires_manual_review=False
        )
    elif len(pending_fails) > 0:
        # Missing documentation
        primary_pending = pending_fails[0]
        return DecisionResult(
            status="PENDING_INFORMATION",
            reason_code=primary_pending["code"],
            explanation=primary_pending["msg"],
            risk_score=risk_score,
            rules_triggered=triggered_rules,
            rule_executions=executions,
            rule_version=rule_version,
            requires_manual_review=False
        )
    elif len(review_fails) > 0:
        # Discretionary manual review
        primary_review = review_fails[0]
        return DecisionResult(
            status="MANUAL_REVIEW",
            reason_code=primary_review["code"],
            explanation=primary_review["msg"],
            risk_score=risk_score,
            rules_triggered=triggered_rules,
            rule_executions=executions,
            rule_version=rule_version,
            requires_manual_review=True
        )
    else:
        triggered_rules.append("RULE_10")
        return DecisionResult(
            status="APPROVED",
            reason_code="APP_CLEAN_APPROVAL",
            explanation="All eligibility, credit score, document, and affordability checks passed cleanly.",
            risk_score=risk_score,
            rules_triggered=triggered_rules,
            rule_executions=executions,
            rule_version=rule_version,
            requires_manual_review=False
        )


def apply_underwriter_override(
    decision: Dict[str, Any],
    underwriter_id: str,
    new_status: str,
    reason: str
) -> Dict[str, Any]:
    """
    Applies an authorized human underwriter override to a decision.
    Valid new_status: 'APPROVED' or 'REJECT'.
    Returns updated decision dictionary and override audit log payload.
    """
    if new_status not in ("APPROVED", "REJECT"):
        raise ValueError("Underwriter override must resolve to 'APPROVED' or 'REJECT'.")

    prev_status = decision.get("decision_status", "MANUAL_REVIEW")
    now = datetime.datetime.now(datetime.timezone.utc)
    override_id = f"OVR-{decision['decision_id']}-{int(now.timestamp())}"

    decision["decision_status"] = new_status
    decision["decision_reason_code"] = f"OVERRIDE_{new_status}"
    decision["decision_explanation"] = f"Manual underwriter override by {underwriter_id}: {reason}"
    decision["reviewer_id"] = underwriter_id

    override_record = {
        "override_id": override_id,
        "decision_id": decision["decision_id"],
        "application_id": decision["application_id"],
        "previous_status": prev_status,
        "overridden_status": new_status,
        "underwriter_id": underwriter_id,
        "override_reason": reason,
        "overridden_at": now
    }

    return override_record
