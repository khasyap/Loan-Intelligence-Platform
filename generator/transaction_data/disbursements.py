"""
Transaction Data Generator: Disbursement Records & Milestone Events
Enforces disbursement prerequisites and transactional uniqueness.
"""

from decimal import Decimal
import datetime
import json
from typing import List, Dict, Any, Tuple

def generate_disbursements(
    applications: List[Dict[str, Any]],
    decisions: List[Dict[str, Any]],
    documents: List[Dict[str, Any]],
    affordability_checks: List[Dict[str, Any]],
    seed: int = 20261022
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Evaluates disbursement prerequisites:
    - Approved decision exists
    - Documents verified
    - Affordability passed
    Returns:
    1. disbursements
    2. disbursement_events
    """
    dec_map = {d["application_id"]: d for d in decisions}
    aff_map = {a["application_id"]: a for a in affordability_checks}
    
    docs_by_app: Dict[str, List[Dict[str, Any]]] = {}
    for d in documents:
        docs_by_app.setdefault(d["application_id"], []).append(d)

    disbursements = []
    events = []
    evt_counter = 1

    for app in applications:
        app_id = app["application_id"]
        decision = dec_map.get(app_id)
        affordability = aff_map.get(app_id)
        app_docs = docs_by_app.get(app_id, [])

        # Prerequisite 1: Approved status
        if not decision or decision["decision_status"] != "APPROVED":
            continue

        # Prerequisite 2: Documents verified
        all_docs_verified = all(
            d.get("verification_status") == "VERIFIED" for d in app_docs
        ) and len(app_docs) > 0
        if not all_docs_verified:
            continue

        # Prerequisite 3: Affordability passed
        if not affordability or affordability["affordability_status"] != "PASSED":
            continue

        # Loan is eligible for disbursement!
        disb_id = f"DISB-{app_id}"
        disb_amount = Decimal(str(app["requested_principal"]))
        disb_date = decision["decision_timestamp"].date() + datetime.timedelta(days=2)
        created_at = decision["decision_timestamp"] + datetime.timedelta(days=2, hours=4)
        bank_ref = f"NEFT-2026-{app_id[-6:]}"

        disbursement = {
            "disbursement_id": disb_id,
            "application_id": app_id,
            "disbursed_amount": disb_amount,
            "disbursement_date": disb_date,
            "disbursement_status": "DISBURSED",
            "bank_reference": bank_ref,
            "created_at": created_at
        }
        disbursements.append(disbursement)

        # Update application state to DISBURSED
        app["application_status"] = "DISBURSED"

        # Generate sequence of milestone events
        # 1. ELIGIBILITY_CHECKED
        events.append({
            "event_id": f"EVT-{evt_counter:06d}",
            "disbursement_id": disb_id,
            "event_type": "ELIGIBILITY_CHECKED",
            "event_timestamp": decision["decision_timestamp"] + datetime.timedelta(days=1),
            "event_payload": json.dumps({"status": "CHECK_PASSED"})
        })
        evt_counter += 1

        # 2. ELIGIBLE
        events.append({
            "event_id": f"EVT-{evt_counter:06d}",
            "disbursement_id": disb_id,
            "event_type": "ELIGIBLE",
            "event_timestamp": decision["decision_timestamp"] + datetime.timedelta(days=1, hours=1),
            "event_payload": json.dumps({"sanctioned_amount": str(disb_amount)})
        })
        evt_counter += 1

        # 3. DISBURSEMENT_INITIATED
        events.append({
            "event_id": f"EVT-{evt_counter:06d}",
            "disbursement_id": disb_id,
            "event_type": "DISBURSEMENT_INITIATED",
            "event_timestamp": decision["decision_timestamp"] + datetime.timedelta(days=2),
            "event_payload": json.dumps({"bank_gateway": "NEFT", "ref": bank_ref})
        })
        evt_counter += 1

        # 4. DISBURSED
        events.append({
            "event_id": f"EVT-{evt_counter:06d}",
            "disbursement_id": disb_id,
            "event_type": "DISBURSED",
            "event_timestamp": created_at,
            "event_payload": json.dumps({"status": "SUCCESS", "cleared_at": str(created_at)})
        })
        evt_counter += 1

    return disbursements, events

