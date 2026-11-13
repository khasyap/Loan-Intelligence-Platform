"""
Master Data Generator: Income Records
Generates primary and secondary verified income records.
"""

from decimal import Decimal
import datetime
from typing import List, Dict, Any
import numpy as np

def generate_income_records(
    applicants: List[Dict[str, Any]],
    employments: List[Dict[str, Any]],
    seed: int = 20261022
) -> List[Dict[str, Any]]:
    rng = np.random.default_rng(seed + 2)
    income_records = []
    inc_counter = 1

    # Map applicant_id to primary employment
    emp_by_app = {e["applicant_id"]: e for e in employments}

    for app in applicants:
        app_id = app["applicant_id"]
        emp = emp_by_app.get(app_id)
        
        salary = emp["monthly_salary"] if emp else Decimal("35000.00")
        gross = salary
        # Net take home is roughly 82% to 88% of gross
        tax_factor = Decimal(str(round(0.82 + (rng.random() * 0.08), 2)))
        net = (gross * tax_factor).quantize(Decimal("0.01"))

        source = "PRIMARY_SALARY" if emp and emp["employment_type"] == "SALARIED" else "BUSINESS_PROFITS"
        if emp and emp["employment_type"] == "UNEMPLOYED":
            gross = Decimal("0.00")
            net = Decimal("0.00")

        inc_id = f"INC-2026-{inc_counter:06d}"
        inc_counter += 1

        v_status = emp["verification_status"] if emp else "VERIFIED"

        income_records.append({
            "income_record_id": inc_id,
            "applicant_id": app_id,
            "employment_id": emp["employment_id"] if emp else None,
            "income_source": source,
            "gross_monthly_income": gross,
            "net_monthly_income": net,
            "additional_income": Decimal("0.00"),
            "income_period_start": datetime.date(2025, 10, 1),
            "income_period_end": datetime.date(2026, 3, 31),
            "verification_status": v_status,
            "source_reference": f"ITR-AY26-{inc_counter:05d}"
        })

        # 15% probability of secondary income (rental or investments)
        if rng.random() < 0.15 and gross > 0:
            sec_gross = Decimal(str(int(rng.integers(10000, 45000))))
            sec_net = (sec_gross * Decimal("0.90")).quantize(Decimal("0.01"))
            sec_id = f"INC-2026-{inc_counter:06d}"
            inc_counter += 1
            income_records.append({
                "income_record_id": sec_id,
                "applicant_id": app_id,
                "employment_id": None,
                "income_source": "RENTAL" if rng.random() < 0.6 else "INVESTMENTS",
                "gross_monthly_income": sec_gross,
                "net_monthly_income": sec_net,
                "additional_income": Decimal("0.00"),
                "income_period_start": datetime.date(2025, 10, 1),
                "income_period_end": datetime.date(2026, 3, 31),
                "verification_status": "VERIFIED",
                "source_reference": f"BANK-STMT-{sec_id}"
            })

    return income_records

