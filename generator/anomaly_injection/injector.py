"""
Anomaly Injection Framework: Separate Anomaly Staging / Exception Layer.
Preserves operational database constraints while staging deliberate malformed records
for independent audit and anomaly detection.
Zero ground-truth leakage into detector inputs.
"""

from decimal import Decimal
import datetime
import copy
from typing import List, Dict, Any, Tuple
import numpy as np

# Deterministic simulation timestamp for anomaly injection
SIMULATION_INJECTION_TIME = datetime.datetime(2026, 1, 20, 12, 0, 0, tzinfo=datetime.timezone.utc)

def inject_anomalies_to_staging(
    applications: List[Dict[str, Any]],
    products: List[Dict[str, Any]],
    decisions: List[Dict[str, Any]],
    affordability_checks: List[Dict[str, Any]],
    repayment_schedules: List[Dict[str, Any]],
    income_records: List[Dict[str, Any]],
    employments: List[Dict[str, Any]],
    disbursements: List[Dict[str, Any]],
    anomaly_target_count: int = 25,
    seed: int = 20261022
) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]], Dict[str, Any]]:
    """
    Creates staged malformed records in an isolated exception layer.
    Preserves pristine baseline records for operational DB.

    Returns:
    1. ground_truth_records: Isolated ground-truth labels for evaluation only.
    2. staged_anomalies: Dictionary of staged malformed records by entity.
    3. injection_stats: Summary counts per category.
    """
    rng = np.random.default_rng(seed + 99)
    prod_map = {p["product_id"]: p for p in products}

    per_category = max(1, anomaly_target_count // 5)
    ground_truth = []
    anom_counter = 1

    staged_records: Dict[str, List[Dict[str, Any]]] = {
        "loan_applications": [],
        "repayment_schedules": [],
        "decisions": [],
        "income_records": [],
        "disbursements": []
    }

    # --------------------------------------------------------------------------
    # 1. INVALID_TERM: Cloned application with out-of-boundary term
    # --------------------------------------------------------------------------
    injected_terms = 0
    for app in applications:
        if injected_terms >= per_category:
            break
        product = prod_map[app["product_id"]]
        bad_app = copy.deepcopy(app)
        bad_term = product["max_term_months"] + 24
        bad_app["requested_term_months"] = bad_term
        staged_records["loan_applications"].append(bad_app)

        anom_id = f"ANOM-2026-{anom_counter:06d}"
        anom_counter += 1
        ground_truth.append({
            "anomaly_id": anom_id,
            "entity_name": "loan_applications",
            "record_id": bad_app["application_id"],
            "issue_type": "INVALID_TERM",
            "expected_label": "ANOMALY",
            "severity": "HIGH",
            "expected_detection": True,
            "expected_decision": "REJECT",
            "explanation": f"Requested term {bad_term} months exceeds product maximum allowable term {product['max_term_months']} months.",
            "injection_timestamp": SIMULATION_INJECTION_TIME
        })
        injected_terms += 1

    # --------------------------------------------------------------------------
    # 2. SCHEDULE_RECONCILIATION_FAILURE: Cloned schedule with corrupted installment
    # --------------------------------------------------------------------------
    injected_reconcil = 0
    app_ids_in_sched = sorted(list({s["application_id"] for s in repayment_schedules}))
    for a_id in app_ids_in_sched:
        if injected_reconcil >= per_category:
            break
        target_installments = [copy.deepcopy(s) for s in repayment_schedules if s["application_id"] == a_id]
        if target_installments:
            target_inst = target_installments[0]
            orig_p = target_inst["principal_amount"]
            target_inst["principal_amount"] = (orig_p + Decimal("250.00")).quantize(Decimal("0.01"))
            staged_records["repayment_schedules"].extend(target_installments)

            anom_id = f"ANOM-2026-{anom_counter:06d}"
            anom_counter += 1
            ground_truth.append({
                "anomaly_id": anom_id,
                "entity_name": "repayment_schedules",
                "record_id": target_inst["schedule_id"],
                "issue_type": "SCHEDULE_RECONCILIATION_FAILURE",
                "expected_label": "ANOMALY",
                "severity": "CRITICAL",
                "expected_detection": True,
                "expected_decision": "AUDIT_FAILURE",
                "explanation": f"Sum of principal installments diverges from loan principal by ₹250.00 on {target_inst['schedule_id']}.",
                "injection_timestamp": SIMULATION_INJECTION_TIME
            })
            injected_reconcil += 1

    # --------------------------------------------------------------------------
    # 3. DECISION_BEFORE_CHECKS: Cloned decision backdated prior to checks
    # --------------------------------------------------------------------------
    injected_ts = 0
    aff_map = {c["application_id"]: c for c in affordability_checks}
    for dec in decisions:
        if injected_ts >= per_category:
            break
        a_id = dec["application_id"]
        aff = aff_map.get(a_id)
        if aff:
            bad_dec = copy.deepcopy(dec)
            bad_dec["decision_timestamp"] = aff["assessment_timestamp"] - datetime.timedelta(hours=4)
            staged_records["decisions"].append(bad_dec)

            anom_id = f"ANOM-2026-{anom_counter:06d}"
            anom_counter += 1
            ground_truth.append({
                "anomaly_id": anom_id,
                "entity_name": "decisions",
                "record_id": bad_dec["decision_id"],
                "issue_type": "DECISION_BEFORE_CHECKS",
                "expected_label": "ANOMALY",
                "severity": "CRITICAL",
                "expected_detection": True,
                "expected_decision": "LIFECYCLE_VIOLATION",
                "explanation": f"Decision timestamp {bad_dec['decision_timestamp']} precedes affordability assessment {aff['assessment_timestamp']}.",
                "injection_timestamp": SIMULATION_INJECTION_TIME
            })
            injected_ts += 1

    # --------------------------------------------------------------------------
    # 4. INCOME_SOURCE_CONFLICT: Cloned income record with inflated gross
    # --------------------------------------------------------------------------
    injected_conflict = 0
    emp_map = {e["applicant_id"]: e for e in employments if e.get("employment_type") == "SALARIED"}
    for inc in income_records:
        if injected_conflict >= per_category:
            break
        a_id = inc["applicant_id"]
        emp = emp_map.get(a_id)
        if emp and inc["income_source"] == "PRIMARY_SALARY":
            bad_inc = copy.deepcopy(inc)
            corrupted_gross = (emp["monthly_salary"] * Decimal("3.50")).quantize(Decimal("0.01"))
            bad_inc["gross_monthly_income"] = corrupted_gross
            staged_records["income_records"].append(bad_inc)

            anom_id = f"ANOM-2026-{anom_counter:06d}"
            anom_counter += 1
            ground_truth.append({
                "anomaly_id": anom_id,
                "entity_name": "income_records",
                "record_id": bad_inc["income_record_id"],
                "issue_type": "INCOME_SOURCE_CONFLICT",
                "expected_label": "ANOMALY",
                "severity": "MEDIUM",
                "expected_detection": True,
                "expected_decision": "MANUAL_REVIEW",
                "explanation": f"Income record gross ₹{corrupted_gross} diverges by >200% from employer salary ₹{emp['monthly_salary']}.",
                "injection_timestamp": SIMULATION_INJECTION_TIME
            })
            injected_conflict += 1

    # --------------------------------------------------------------------------
    # 5. DUPLICATE_DISBURSEMENT: Duplicate disbursement record in staged payouts
    # --------------------------------------------------------------------------
    injected_dup_disb = 0
    disb_apps = [d["application_id"] for d in disbursements]
    for a_id in disb_apps:
        if injected_dup_disb >= per_category:
            break
        orig_disb = next(d for d in disbursements if d["application_id"] == a_id)
        dup_disb_id = f"DISB-DUP-{orig_disb['disbursement_id']}"
        dup_record = {
            "disbursement_id": dup_disb_id,
            "application_id": a_id,
            "disbursed_amount": orig_disb["disbursed_amount"],
            "disbursement_date": orig_disb["disbursement_date"],
            "disbursement_status": "DISBURSED",
            "bank_reference": f"NEFT-DUP-{a_id[-6:]}",
            "created_at": orig_disb["created_at"] + datetime.timedelta(hours=2)
        }
        # Stage the duplicate record in the payout auditor queue
        staged_records["disbursements"].append(dup_record)

        anom_id = f"ANOM-2026-{anom_counter:06d}"
        anom_counter += 1
        ground_truth.append({
            "anomaly_id": anom_id,
            "entity_name": "disbursements",
            "record_id": dup_disb_id,
            "issue_type": "DUPLICATE_DISBURSEMENT",
            "expected_label": "ANOMALY",
            "severity": "CRITICAL",
            "expected_detection": True,
            "expected_decision": "PREVENT_PAYOUT",
            "explanation": f"Multiple successful disbursement records staged for application {a_id}.",
            "injection_timestamp": SIMULATION_INJECTION_TIME
        })
        injected_dup_disb += 1

    stats = {
        "total_anomalies": len(ground_truth),
        "invalid_term_count": injected_terms,
        "schedule_reconciliation_count": injected_reconcil,
        "decision_before_checks_count": injected_ts,
        "income_conflict_count": injected_conflict,
        "duplicate_disbursement_count": injected_dup_disb
    }

    return ground_truth, staged_records, stats

# Backward compatibility alias
inject_anomalies = inject_anomalies_to_staging

