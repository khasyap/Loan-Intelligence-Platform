"""
Independent Anomaly Detector: Audits records across operational and staging stores
using deterministic business logic, mathematical reconciliation, and temporal verifications.
STRICT AUDIT RULE: Zero access to ground truth labels or exception registers.
"""

from decimal import Decimal
from typing import List, Dict, Any

class DetectedAnomaly:
    def __init__(
        self,
        entity_name: str,
        record_id: str,
        issue_type: str,
        severity: str,
        description: str
    ):
        self.entity_name = entity_name
        self.record_id = record_id
        self.issue_type = issue_type
        self.severity = severity
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_name": self.entity_name,
            "record_id": self.record_id,
            "issue_type": self.issue_type,
            "severity": self.severity,
            "description": self.description
        }


def detect_operational_anomalies(
    applications: List[Dict[str, Any]],
    products: List[Dict[str, Any]],
    decisions: List[Dict[str, Any]],
    affordability_checks: List[Dict[str, Any]],
    repayment_schedules: List[Dict[str, Any]],
    income_records: List[Dict[str, Any]],
    employments: List[Dict[str, Any]],
    disbursements: List[Dict[str, Any]],
    documents: List[Dict[str, Any]],
    staged_records: Dict[str, List[Dict[str, Any]]] = None
) -> List[DetectedAnomaly]:
    """
    Audits loan records across operational and staging registers.
    """
    detected: List[DetectedAnomaly] = []
    prod_map = {p["product_id"]: p for p in products}

    # Combine operational with staged inspection pool
    staged = staged_records or {}
    all_apps = applications + staged.get("loan_applications", [])
    all_schedules = repayment_schedules + staged.get("repayment_schedules", [])
    all_decisions = decisions + staged.get("decisions", [])
    all_incomes = income_records + staged.get("income_records", [])
    all_disbursements = disbursements + staged.get("disbursements", [])

    # --------------------------------------------------------------------------
    # 1. Detect INVALID_TERM
    # --------------------------------------------------------------------------
    for app in all_apps:
        prod = prod_map.get(app["product_id"])
        if prod:
            term = int(app["requested_term_months"])
            min_t = int(prod["min_term_months"])
            max_t = int(prod["max_term_months"])
            if term < min_t or term > max_t:
                detected.append(DetectedAnomaly(
                    entity_name="loan_applications",
                    record_id=app["application_id"],
                    issue_type="INVALID_TERM",
                    severity="HIGH",
                    description=f"Requested term {term} months breaches product boundary [{min_t}, {max_t}] months."
                ))

    # --------------------------------------------------------------------------
    # 2. Detect SCHEDULE_RECONCILIATION_FAILURE
    # --------------------------------------------------------------------------
    app_principal_map = {a["application_id"]: Decimal(str(a["requested_principal"])) for a in all_apps}
    sched_by_app: Dict[str, List[Dict[str, Any]]] = {}
    for s in all_schedules:
        sched_by_app.setdefault(s["application_id"], []).append(s)

    for app_id, installments in sched_by_app.items():
        expected_p = app_principal_map.get(app_id)
        if expected_p:
            total_repaid = sum(Decimal(str(inst["principal_amount"])) for inst in installments)
            diff = abs(total_repaid - expected_p)
            if diff > Decimal("0.05"):
                inst_id = installments[0]["schedule_id"]
                detected.append(DetectedAnomaly(
                    entity_name="repayment_schedules",
                    record_id=inst_id,
                    issue_type="SCHEDULE_RECONCILIATION_FAILURE",
                    severity="CRITICAL",
                    description=f"Repayment schedule for {app_id} diverges from principal ₹{expected_p} by ₹{diff}."
                ))

    # --------------------------------------------------------------------------
    # 3. Detect DECISION_BEFORE_CHECKS
    # --------------------------------------------------------------------------
    aff_ts_map = {a["application_id"]: a["assessment_timestamp"] for a in affordability_checks}
    for dec in all_decisions:
        app_id = dec["application_id"]
        aff_ts = aff_ts_map.get(app_id)
        if aff_ts and dec["decision_timestamp"] < aff_ts:
            detected.append(DetectedAnomaly(
                entity_name="decisions",
                record_id=dec["decision_id"],
                issue_type="DECISION_BEFORE_CHECKS",
                severity="CRITICAL",
                description=f"Decision {dec['decision_id']} timestamp ({dec['decision_timestamp']}) precedes affordability assessment ({aff_ts})."
            ))

    # --------------------------------------------------------------------------
    # 4. Detect INCOME_SOURCE_CONFLICT
    # --------------------------------------------------------------------------
    emp_salary_map = {e["applicant_id"]: Decimal(str(e["monthly_salary"])) for e in employments if e.get("employment_type") == "SALARIED"}
    for inc in all_incomes:
        if inc.get("income_source") == "PRIMARY_SALARY":
            app_id = inc["applicant_id"]
            emp_sal = emp_salary_map.get(app_id)
            if emp_sal and emp_sal > Decimal("0.00"):
                inc_gross = Decimal(str(inc["gross_monthly_income"]))
                diff_pct = abs(inc_gross - emp_sal) / emp_sal
                if diff_pct > Decimal("0.30"):
                    detected.append(DetectedAnomaly(
                        entity_name="income_records",
                        record_id=inc["income_record_id"],
                        issue_type="INCOME_SOURCE_CONFLICT",
                        severity="MEDIUM",
                        description=f"Income record gross ₹{inc_gross} conflicts with employer salary ₹{emp_sal} (variance: {diff_pct*100:.1f}%)."
                    ))

    # --------------------------------------------------------------------------
    # 5. Detect DUPLICATE_DISBURSEMENT
    # --------------------------------------------------------------------------
    disb_counts: Dict[str, List[Dict[str, Any]]] = {}
    for d in all_disbursements:
        if d.get("disbursement_status") == "DISBURSED":
            disb_counts.setdefault(d["application_id"], []).append(d)

    for app_id, d_list in disb_counts.items():
        if len(d_list) > 1:
            for extra_d in d_list[1:]:
                detected.append(DetectedAnomaly(
                    entity_name="disbursements",
                    record_id=extra_d["disbursement_id"],
                    issue_type="DUPLICATE_DISBURSEMENT",
                    severity="CRITICAL",
                    description=f"Duplicate active disbursement detected for application {app_id}."
                ))

    return detected
