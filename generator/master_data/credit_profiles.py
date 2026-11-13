"""
Master Data Generator: CreditProfile Entity
Derives deterministic credit bureau profiles and behavioral scores
directly from credit facilities, payment history, and utilization.
"""

from decimal import Decimal
import datetime
from typing import List, Dict, Any, Tuple
import numpy as np

def derive_credit_score_and_profile(
    applicant_id: str,
    facilities: List[Dict[str, Any]],
    counter: int,
    seed: int = 20261022
) -> Dict[str, Any]:
    """
    Computes a grounded, explainable synthetic credit score from behavioral attributes.
    """
    rng = np.random.default_rng(seed + 50 + counter)

    active_facilities = [f for f in facilities if f.get("payment_status") != "CLOSED"]
    card_facilities = [f for f in active_facilities if f.get("facility_type") == "CREDIT_CARD"]
    
    total_card_limit = sum((Decimal(str(f["credit_limit"])) for f in card_facilities), Decimal("0.00"))
    total_card_balance = sum((Decimal(str(f["outstanding_balance"])) for f in card_facilities), Decimal("0.00"))

    if total_card_limit > Decimal("0.00"):
        utilization = ((total_card_balance / total_card_limit) * Decimal("100.00")).quantize(Decimal("0.01"))
    else:
        utilization = Decimal("0.00")

    overdue_count = sum(1 for f in active_facilities if "OVERDUE" in f.get("payment_status", ""))
    default_count = sum(1 for f in active_facilities if f.get("payment_status") == "DEFAULTED")

    # Payment history percentage derivation
    if default_count > 0:
        on_time_pct = Decimal(str(round(float(rng.uniform(62.0, 78.0)), 2)))
    elif overdue_count > 0:
        on_time_pct = Decimal(str(round(float(rng.uniform(86.0, 94.0)), 2)))
    elif len(active_facilities) > 0:
        on_time_pct = Decimal(str(round(float(rng.uniform(96.0, 100.0)), 2)))
    else:
        # Thin file (no facilities yet)
        on_time_pct = Decimal("95.00")

    # Deterministic Formula:
    # Base = 680
    base_score = 680.0
    history_component = (float(on_time_pct) - 90.0) * 11.5
    utilization_penalty = max(0.0, (float(utilization) - 30.0) * 1.8)
    delinquency_penalty = (overdue_count * 45.0) + (default_count * 135.0)
    tenure_bonus = min(35.0, len(active_facilities) * 8.0)

    computed_score = int(round(base_score + history_component - utilization_penalty - delinquency_penalty + tenure_bonus))
    final_score = max(300, min(900, computed_score))

    # Score Band Classification
    if final_score >= 780:
        band = "EXCELLENT"
    elif final_score >= 720:
        band = "VERY_GOOD"
    elif final_score >= 660:
        band = "GOOD"
    elif final_score >= 600:
        band = "FAIR"
    else:
        band = "POOR"

    profile_id = f"CP-2026-{counter:06d}"
    assessment_date = datetime.date(2026, 1, 10)

    return {
        "credit_profile_id": profile_id,
        "applicant_id": applicant_id,
        "synthetic_credit_score": final_score,
        "score_band": band,
        "payment_history": on_time_pct,
        "credit_utilization": utilization,
        "active_facility_count": len(active_facilities),
        "assessment_date": assessment_date,
        "score_version": "v1.0.0",
        "source_type": "SYNTHETIC_BUREAU_V1",
        "created_at": datetime.datetime(2026, 1, 10, 8, 0, 0, tzinfo=datetime.timezone.utc)
    }


def generate_credit_profiles(
    applicants: List[Dict[str, Any]],
    credit_facilities: List[Dict[str, Any]],
    seed: int = 20261022
) -> List[Dict[str, Any]]:
    """
    Generates grounded CreditProfiles for all applicants and synchronizes Applicant.credit_score.
    """
    fac_by_app: Dict[str, List[Dict[str, Any]]] = {}
    for f in credit_facilities:
        fac_by_app.setdefault(f["applicant_id"], []).append(f)

    profiles = []
    counter = 1

    for app in applicants:
        a_id = app["applicant_id"]
        app_facs = fac_by_app.get(a_id, [])
        profile = derive_credit_score_and_profile(a_id, app_facs, counter, seed=seed)
        
        # Synchronize applicant credit score with grounded synthetic score
        app["credit_score"] = profile["synthetic_credit_score"]

        profiles.append(profile)
        counter += 1

    return profiles

