"""
Transaction Data Generator: Loan Applications
Synthesizes baseline loan applications referencing master applicants and loan products.
"""

from decimal import Decimal
import datetime
from typing import List, Dict, Any
import numpy as np

CHANNELS = ["ONLINE_PORTAL", "MOBILE_APP", "BRANCH_AGENT", "PARTNER_API"]

def generate_applications(
    count: int,
    applicants: List[Dict[str, Any]],
    products: List[Dict[str, Any]],
    seed: int = 20261022
) -> List[Dict[str, Any]]:
    rng = np.random.default_rng(seed + 10)
    applications = []

    prod_map = {p["product_id"]: p for p in products}
    prod_ids = list(prod_map.keys())

    num_applicants = len(applicants)

    base_time = datetime.datetime(2026, 1, 15, 10, 0, 0)

    for i in range(1, count + 1):
        app_id = f"LOAN-2026-{i:06d}"

        # Assign applicant: primarily 1:1, but allowing some applicants to have 2 applications (duplicates)
        if i <= num_applicants:
            applicant = applicants[i - 1]
        else:
            # Duplicate applicant assignment
            dup_idx = int(rng.integers(0, min(500, num_applicants)))
            applicant = applicants[dup_idx]

        applicant_id = applicant["applicant_id"]

        # Product selection
        p_id = prod_ids[rng.integers(0, len(prod_ids))]
        prod = prod_map[p_id]

        # Requested principal: realistic distribution around median product limit
        min_p = float(prod["min_principal"])
        max_p = float(prod["max_principal"])
        
        # 95% within limits, 5% edge cases
        if rng.random() < 0.95:
            req_p_val = rng.uniform(min_p, max_p * 0.85)
        else:
            req_p_val = rng.uniform(max_p * 0.95, max_p * 1.20)
        
        # Round to nearest 5,000 INR
        req_principal = Decimal(str(int(round(req_p_val / 5000.0) * 5000)))

        # Requested term: within product term range
        min_t = prod["min_term_months"]
        max_t = prod["max_term_months"]
        req_term = int(rng.integers(min_t, max_t + 1))

        app_date = base_time + datetime.timedelta(minutes=int(i * 12))
        channel = CHANNELS[int(rng.choice([0, 1, 2, 3], p=[0.60, 0.25, 0.10, 0.05]))]

        applications.append({
            "application_id": app_id,
            "applicant_id": applicant_id,
            "product_id": p_id,
            "requested_principal": req_principal,
            "requested_term_months": req_term,
            "application_date": app_date,
            "application_status": "SUBMITTED",  # Initial state, updated during lifecycle processing
            "submission_channel": channel,
            "application_version": 1
        })

    return applications

