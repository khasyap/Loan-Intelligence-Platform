"""
Transaction Data Generator: Repayment Schedules
Generates amortized monthly installments for approved loans with penny reconciliation.
"""

from decimal import Decimal
import datetime
from typing import List, Dict, Any
from backend.app.calculations.financial import (
    generate_amortization_schedule,
    verify_schedule_reconciliation
)

def generate_repayment_schedules(
    applications: List[Dict[str, Any]],
    products: List[Dict[str, Any]],
    decisions: List[Dict[str, Any]],
    seed: int = 20261022
) -> List[Dict[str, Any]]:
    prod_map = {p["product_id"]: p for p in products}
    dec_map = {d["application_id"]: d for d in decisions}

    all_installments = []

    for app in applications:
        app_id = app["application_id"]
        decision = dec_map.get(app_id)

        # Repayment schedules are created exclusively for approved loans
        if not decision or decision["decision_status"] != "APPROVED":
            continue

        product = prod_map[app["product_id"]]
        principal = Decimal(str(app["requested_principal"]))
        term = int(app["requested_term_months"])
        rate = Decimal(str(product["annual_interest_rate"]))
        
        # Disbursement date: 2 days after decision
        disb_date = decision["decision_timestamp"].date() + datetime.timedelta(days=2)

        installments = generate_amortization_schedule(
            application_id=app_id,
            principal=principal,
            annual_interest_rate=rate,
            term_months=term,
            disbursement_date=disb_date
        )

        # Audit reconciliation
        reconciled, details = verify_schedule_reconciliation(principal, installments)
        if not reconciled:
            raise ValueError(f"Schedule reconciliation failure for application {app_id}: {details}")

        all_installments.extend(installments)

    return all_installments

