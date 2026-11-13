"""
Master Data Generator: Existing Credit Facilities
Synthesizes active loans and credit cards.
"""

from decimal import Decimal
import datetime
from typing import List, Dict, Any
import numpy as np

FACILITY_TYPES = ["CREDIT_CARD", "PERSONAL_LOAN", "AUTO_LOAN", "MORTGAGE", "EDUCATION_LOAN"]
LENDERS = ["HDFC Bank", "State Bank of India", "ICICI Bank", "Axis Bank", "Kotak Mahindra Bank", "Bajaj Finance"]

def generate_credit_facilities(applicants: List[Dict[str, Any]], seed: int = 20261022) -> List[Dict[str, Any]]:
    rng = np.random.default_rng(seed + 3)
    facilities = []
    fac_counter = 1

    for app in applicants:
        app_id = app["applicant_id"]
        # ~70% chance of having at least 1 credit facility
        if rng.random() > 0.70:
            continue

        num_facilities = int(rng.integers(1, 4))
        for _ in range(num_facilities):
            f_type = FACILITY_TYPES[rng.integers(0, len(FACILITY_TYPES))]
            lender = LENDERS[rng.integers(0, len(LENDERS))]
            
            if f_type == "CREDIT_CARD":
                limit = Decimal(str(int(rng.integers(50000, 300000))))
                utilization = Decimal(str(round(float(rng.uniform(0.05, 0.75)), 2)))
                balance = (limit * utilization).quantize(Decimal("0.01"))
                # Minimum payment ~ 5% of balance
                emi = (balance * Decimal("0.05")).quantize(Decimal("0.01"))
                rate = Decimal("36.00")
            elif f_type == "AUTO_LOAN":
                limit = Decimal(str(int(rng.integers(400000, 1200000))))
                balance = (limit * Decimal("0.60")).quantize(Decimal("0.01"))
                emi = Decimal(str(int(rng.integers(8000, 22000))))
                rate = Decimal("9.50")
            elif f_type == "MORTGAGE":
                limit = Decimal(str(int(rng.integers(2500000, 8000000))))
                balance = (limit * Decimal("0.80")).quantize(Decimal("0.01"))
                emi = Decimal(str(int(rng.integers(25000, 75000))))
                rate = Decimal("8.50")
            else:
                limit = Decimal(str(int(rng.integers(100000, 500000))))
                balance = (limit * Decimal("0.50")).quantize(Decimal("0.01"))
                emi = Decimal(str(int(rng.integers(3500, 15000))))
                rate = Decimal("12.50")

            opened_date = datetime.date(2023, int(rng.integers(1, 13)), 1)
            
            # Payment status: mostly CURRENT
            p_rand = rng.random()
            if p_rand < 0.90:
                p_status = "CURRENT"
            elif p_rand < 0.97:
                p_status = "OVERDUE_30"
            else:
                p_status = "DEFAULTED"

            fac_id = f"FAC-2026-{fac_counter:06d}"
            fac_counter += 1

            facilities.append({
                "credit_facility_id": fac_id,
                "applicant_id": app_id,
                "facility_type": f_type,
                "lender_reference": lender,
                "credit_limit": limit,
                "outstanding_balance": balance,
                "monthly_emi": emi,
                "interest_rate": rate,
                "payment_status": p_status,
                "opened_date": opened_date,
                "closed_date": None
            })

    return facilities

