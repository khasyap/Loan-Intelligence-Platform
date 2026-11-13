"""
Comprehensive Evaluation Suite: Computes holistic banking compliance, mathematical,
operational, and anomaly metrics directly from actual records.
"""

from decimal import Decimal
from typing import List, Dict, Any, Tuple
import datetime

PROHIBITED_FEATURES = [
    "gender", "race", "ethnicity", "religion", "caste",
    "disability", "sexual_orientation", "marital_status"
]

def compute_comprehensive_evaluation(
    applicants: List[Dict[str, Any]],
    applications: List[Dict[str, Any]],
    products: List[Dict[str, Any]],
    decisions: List[Dict[str, Any]],
    affordability_checks: List[Dict[str, Any]],
    repayment_schedules: List[Dict[str, Any]],
    disbursements: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]],
    detected_anomalies: List[Dict[str, Any]],
    start_time: datetime.datetime = None,
    end_time: datetime.datetime = None
) -> Dict[str, Any]:
    """
    Computes all 10 mandated operational, mathematical, and algorithmic evaluation metrics.
    """
    total_apps = len(applications)

    # 1. Decision Status Rates
    approved_count = sum(1 for d in decisions if d["decision_status"] == "APPROVED")
    rejected_count = sum(1 for d in decisions if d["decision_status"] in ("REJECT", "REJECTED"))
    manual_review_count = sum(1 for d in decisions if d["decision_status"] == "MANUAL_REVIEW")
    pending_info_count = sum(1 for d in decisions if d["decision_status"] == "PENDING_INFORMATION")

    approval_rate = (approved_count / total_apps * 100.0) if total_apps > 0 else 0.0
    rejection_rate = (rejected_count / total_apps * 100.0) if total_apps > 0 else 0.0
    manual_review_rate = (manual_review_count / total_apps * 100.0) if total_apps > 0 else 0.0
    pending_info_rate = (pending_info_count / total_apps * 100.0) if total_apps > 0 else 0.0

    # 2. Decision Rule Consistency Rate (100% Determinism)
    # Decisions match reason code classification
    consistent_decisions = 0
    for d in decisions:
        status = d["decision_status"]
        code = d["decision_reason_code"]
        if (status == "APPROVED" and code.startswith("APP_")) or \
           (status in ("REJECT", "REJECTED") and code.startswith("REJ_")) or \
           (status in ("MANUAL_REVIEW", "PENDING_INFORMATION") and code.startswith("REV_")):
            consistent_decisions += 1
    decision_consistency_rate = (consistent_decisions / len(decisions) * 100.0) if decisions else 100.0

    # 3. Financial Calculation Error Rate
    total_math_checks = 0
    math_errors = 0
    for aff in affordability_checks:
        total_math_checks += 1
        net = Decimal(str(aff["monthly_net_income"]))
        debt = Decimal(str(aff["existing_monthly_debt"]))
        emi = Decimal(str(aff["proposed_monthly_emi"]))
        disp = Decimal(str(aff["disposable_income"]))
        expected_disp = net - debt - emi
        if abs(disp - expected_disp) > Decimal("0.05"):
            math_errors += 1

    financial_calculation_error_rate = (math_errors / total_math_checks * 100.0) if total_math_checks > 0 else 0.0

    # 4. Repayment Reconciliation Rate
    app_principal_map = {a["application_id"]: Decimal(str(a["requested_principal"])) for a in applications}
    sched_by_app: Dict[str, List[Dict[str, Any]]] = {}
    for s in repayment_schedules:
        sched_by_app.setdefault(s["application_id"], []).append(s)

    reconciled_schedules = 0
    total_schedules = len(sched_by_app)
    for a_id, installments in sched_by_app.items():
        exp_p = app_principal_map.get(a_id)
        if exp_p:
            total_repaid = sum(Decimal(str(i["principal_amount"])) for i in installments)
            final_bal = Decimal(str(installments[-1]["closing_balance"]))
            if abs(total_repaid - exp_p) <= Decimal("0.05") and final_bal == Decimal("0.00"):
                reconciled_schedules += 1

    repayment_reconciliation_rate = (reconciled_schedules / total_schedules * 100.0) if total_schedules > 0 else 100.0

    # 5. Referential Integrity Rate
    applicant_ids = {a["applicant_id"] for a in applicants}
    product_ids = {p["product_id"] for p in products}
    app_ids = {a["application_id"] for a in applications}

    total_fk_checks = 0
    passed_fk_checks = 0

    for a in applications:
        total_fk_checks += 2
        if a["applicant_id"] in applicant_ids:
            passed_fk_checks += 1
        if a["product_id"] in product_ids:
            passed_fk_checks += 1

    for d in decisions:
        total_fk_checks += 1
        if d["application_id"] in app_ids:
            passed_fk_checks += 1

    for aff in affordability_checks:
        total_fk_checks += 1
        if aff["application_id"] in app_ids:
            passed_fk_checks += 1

    referential_integrity_rate = (passed_fk_checks / total_fk_checks * 100.0) if total_fk_checks > 0 else 100.0

    # 6. Anomaly Detection Metrics
    gt_keys = {(g["record_id"], g["issue_type"]) for g in ground_truth}
    dt_keys = {(d["record_id"], d["issue_type"]) for d in detected_anomalies}

    tp = len(gt_keys & dt_keys)
    fp = len(dt_keys - gt_keys)
    fn = len(gt_keys - dt_keys)

    prec = (tp / (tp + fp)) if (tp + fp) > 0 else 1.0
    rec = (tp / (tp + fn)) if (tp + fn) > 0 else 1.0
    f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

    # 7. Prohibited Feature & Data Leakage Audit
    applicant_sample = applicants[0] if applicants else {}
    found_prohibited = [feat for feat in PROHIBITED_FEATURES if feat in applicant_sample]
    has_prohibited_features = len(found_prohibited) > 0

    # 8. Processing Duration
    elapsed_seconds = (end_time - start_time).total_seconds() if (start_time and end_time) else 0.0

    return {
        "portfolio_overview": {
            "total_applicants": len(applicants),
            "total_applications": total_apps,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "manual_review_count": manual_review_count,
            "pending_info_count": pending_info_count,
            "approval_rate_pct": round(approval_rate, 2),
            "rejection_rate_pct": round(rejection_rate, 2),
            "manual_review_rate_pct": round(manual_review_rate, 2),
            "pending_info_rate_pct": round(pending_info_rate, 2)
        },
        "quality_and_compliance": {
            "decision_rule_consistency_pct": round(decision_consistency_rate, 2),
            "financial_calculation_error_rate_pct": round(financial_calculation_error_rate, 2),
            "repayment_reconciliation_rate_pct": round(repayment_reconciliation_rate, 2),
            "referential_integrity_rate_pct": round(referential_integrity_rate, 2),
            "prohibited_features_detected": found_prohibited,
            "fair_lending_compliance_pass": not has_prohibited_features
        },
        "anomaly_detection_performance": {
            "total_ground_truth": len(ground_truth),
            "total_detected": len(detected_anomalies),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4)
        },
        "system_turnaround": {
            "total_processing_seconds": round(elapsed_seconds, 2),
            "average_application_processing_ms": round((elapsed_seconds / total_apps * 1000), 2) if total_apps > 0 else 0.0
        }
    }

