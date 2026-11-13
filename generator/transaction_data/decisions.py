"""
Transaction Data Generator: Underwriting Decisions & State History
Integrates with Explainable Decision Rules Engine.
"""

import datetime
from typing import List, Dict, Any, Tuple
from backend.app.rules_engine.engine import evaluate_application

def generate_decisions(
    applications: List[Dict[str, Any]],
    products: List[Dict[str, Any]],
    applicants: List[Dict[str, Any]],
    affordability_checks: List[Dict[str, Any]],
    documents: List[Dict[str, Any]],
    employments: List[Dict[str, Any]],
    seed: int = 20261022
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Evaluates applications and returns:
    1. decisions
    2. decision_rule_executions
    3. application_status_history
    """
    prod_map = {p["product_id"]: p for p in products}
    app_map = {a["applicant_id"]: a for a in applicants}
    aff_map = {c["application_id"]: c for c in affordability_checks}
    
    docs_by_app: Dict[str, List[Dict[str, Any]]] = {}
    for d in documents:
        docs_by_app.setdefault(d["application_id"], []).append(d)

    emp_by_app: Dict[str, List[Dict[str, Any]]] = {}
    for e in employments:
        emp_by_app.setdefault(e["applicant_id"], []).append(e)

    # Active application counts per applicant
    active_counts: Dict[str, int] = {}
    for ap in applications:
        a_id = ap["applicant_id"]
        active_counts[a_id] = active_counts.get(a_id, 0) + 1

    decisions = []
    executions = []
    status_histories = []

    exec_counter = 1
    hist_counter = 1

    for app in applications:
        app_id = app["application_id"]
        applicant_id = app["applicant_id"]
        product_id = app["product_id"]

        product = prod_map[product_id]
        applicant = app_map[applicant_id]
        affordability = aff_map[app_id]
        app_docs = docs_by_app.get(app_id, [])
        app_emps = emp_by_app.get(applicant_id, [])

        result = evaluate_application(
            application=app,
            product=product,
            applicant=applicant,
            affordability=affordability,
            documents=app_docs,
            employments=app_emps,
            active_application_count=active_counts[applicant_id]
        )

        dec_id = f"DEC-{app_id}-01"
        # Decision timestamp occurs 1 hour after affordability assessment
        dec_timestamp = affordability["assessment_timestamp"] + datetime.timedelta(hours=1)

        decisions.append({
            "decision_id": dec_id,
            "application_id": app_id,
            "decision_sequence": 1,
            "decision_status": result.status,
            "decision_timestamp": dec_timestamp,
            "decision_reason_code": result.reason_code,
            "decision_explanation": result.explanation,
            "risk_score": result.risk_score,
            "rules_triggered": result.rules_triggered,
            "reviewer_id": "SYSTEM_RULES_ENGINE",
            "rule_version": result.rule_version
        })

        # Update application status
        app["application_status"] = result.status

        # Collect rule executions
        for r_exec in result.rule_executions:
            exec_id = f"EXEC-{app_id}-{exec_counter:06d}"
            exec_counter += 1
            executions.append({
                "execution_id": exec_id,
                "decision_id": dec_id,
                "rule_id": r_exec["rule_id"],
                "rule_version": r_exec["rule_version"],
                "evaluated_values": r_exec["evaluated_values"],
                "is_triggered": r_exec["is_triggered"],
                "triggered_action": r_exec["triggered_action"]
            })

        # Status history: SUBMITTED -> UNDER_REVIEW -> Final Decision
        hist_1 = {
            "history_id": f"HIST-{hist_counter:06d}",
            "application_id": app_id,
            "previous_status": None,
            "new_status": "SUBMITTED",
            "changed_at": app["application_date"],
            "changed_by": "SYSTEM_PORTAL",
            "notes": "Application successfully submitted via online channel."
        }
        hist_counter += 1

        hist_2 = {
            "history_id": f"HIST-{hist_counter:06d}",
            "application_id": app_id,
            "previous_status": "SUBMITTED",
            "new_status": "UNDER_REVIEW",
            "changed_at": affordability["assessment_timestamp"],
            "changed_by": "AFFORDABILITY_SERVICE",
            "notes": "Affordability and document verification checks initiated."
        }
        hist_counter += 1

        hist_3 = {
            "history_id": f"HIST-{hist_counter:06d}",
            "application_id": app_id,
            "previous_status": "UNDER_REVIEW",
            "new_status": result.status,
            "changed_at": dec_timestamp,
            "changed_by": "SYSTEM_RULES_ENGINE",
            "notes": f"Decision reached: {result.status} ({result.reason_code})"
        }
        hist_counter += 1

        status_histories.extend([hist_1, hist_2, hist_3])

    return decisions, executions, status_histories

