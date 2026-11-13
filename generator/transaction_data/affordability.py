"""
Transaction Data Generator: Affordability Assessments
Integrates with Financial Calculation Engine to assess DTI, FOIR and disposable income.
"""

from decimal import Decimal
import datetime
import json
from typing import List, Dict, Any
from backend.app.calculations.financial import (
    calculate_dti,
    calculate_foir,
    calculate_disposable_income,
    calculate_reducing_emi
)

def generate_affordability_checks(
    applications: List[Dict[str, Any]],
    products: List[Dict[str, Any]],
    income_records: List[Dict[str, Any]],
    credit_facilities: List[Dict[str, Any]],
    seed: int = 20261022
) -> List[Dict[str, Any]]:
    prod_map = {p["product_id"]: p for p in products}

    # Aggregate incomes by applicant
    gross_by_app: Dict[str, Decimal] = {}
    net_by_app: Dict[str, Decimal] = {}
    for inc in income_records:
        a_id = inc["applicant_id"]
        gross_by_app[a_id] = gross_by_app.get(a_id, Decimal("0.00")) + Decimal(str(inc["gross_monthly_income"]))
        net_by_app[a_id] = net_by_app.get(a_id, Decimal("0.00")) + Decimal(str(inc["net_monthly_income"]))

    # Aggregate existing EMIs by applicant
    debt_by_app: Dict[str, Decimal] = {}
    for fac in credit_facilities:
        if fac.get("payment_status") != "CLOSED":
            a_id = fac["applicant_id"]
            debt_by_app[a_id] = debt_by_app.get(a_id, Decimal("0.00")) + Decimal(str(fac["monthly_emi"]))

    affordability_checks = []

    for app in applications:
        app_id = app["application_id"]
        applicant_id = app["applicant_id"]
        product_id = app["product_id"]
        product = prod_map[product_id]

        gross_income = gross_by_app.get(applicant_id, Decimal("45000.00"))
        net_income = net_by_app.get(applicant_id, Decimal("38000.00"))
        existing_debt = debt_by_app.get(applicant_id, Decimal("0.00"))

        principal = Decimal(str(app["requested_principal"]))
        term = int(app["requested_term_months"])
        rate = Decimal(str(product["annual_interest_rate"]))

        proposed_emi = calculate_reducing_emi(principal, rate, term)
        dti = calculate_dti(existing_debt, gross_income)
        foir = calculate_foir(existing_debt, proposed_emi, net_income)
        disposable = calculate_disposable_income(net_income, existing_debt, proposed_emi)

        # Affordability status classification
        max_dti = Decimal(str(product["maximum_dti"]))
        max_foir = Decimal(str(product["maximum_foir"]))

        if dti <= max_dti and foir <= max_foir and disposable > Decimal("0.00"):
            aff_status = "PASSED"
        elif dti <= (max_dti * Decimal("1.20")) and foir <= (max_foir * Decimal("1.10")):
            aff_status = "BORDERLINE"
        else:
            aff_status = "FAILED"

        assessment_ts = app["application_date"] + datetime.timedelta(hours=2)
        aff_id = f"AFF-{app_id}-01"

        calc_details = {
            "gross_income": str(gross_income),
            "net_income": str(net_income),
            "existing_debt": str(existing_debt),
            "proposed_emi": str(proposed_emi),
            "dti_ratio": str(dti),
            "foir_ratio": str(foir),
            "disposable_income": str(disposable),
            "product_dti_limit": str(max_dti),
            "product_foir_limit": str(max_foir)
        }

        affordability_checks.append({
            "affordability_check_id": aff_id,
            "application_id": app_id,
            "assessment_timestamp": assessment_ts,
            "monthly_net_income": net_income,
            "existing_monthly_debt": existing_debt,
            "proposed_monthly_emi": proposed_emi,
            "debt_to_income_ratio": dti,
            "fixed_obligation_ratio": foir,
            "disposable_income": disposable,
            "affordability_status": aff_status,
            "rule_version": "v1.0.0",
            "calculation_details": json.dumps(calc_details)
        })

    return affordability_checks

