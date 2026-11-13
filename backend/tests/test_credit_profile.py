"""
Unit & Integration Tests: CreditProfile Entity & Behavioral Score Calculation.
Verifies formulaic derivation of synthetic credit scores, score bands,
clamping bounds [300, 900], payment history weighting, and facility links.
"""

import pytest
from decimal import Decimal
import datetime

from generator.master_data.credit_profiles import (
    derive_credit_score_and_profile,
    generate_credit_profiles
)
from generator.master_data.credit_facilities import generate_credit_facilities
from generator.master_data.applicants import generate_applicants


def test_credit_score_bounds_and_clamping():
    """Verify synthetic credit scores are strictly clamped between 300 and 900."""
    facilities_clean = [
        {
            "facility_type": "CREDIT_CARD",
            "credit_limit": Decimal("100000.00"),
            "outstanding_balance": Decimal("5000.00"),
            "payment_status": "CURRENT"
        }
    ]
    profile = derive_credit_score_and_profile("APP-2026-000001", facilities_clean, counter=1, seed=20261022)
    assert 300 <= profile["synthetic_credit_score"] <= 900
    assert profile["score_band"] in ["EXCELLENT", "VERY_GOOD", "GOOD", "FAIR", "POOR"]
    assert profile["applicant_id"] == "APP-2026-000001"
    assert profile["source_type"] == "SYNTHETIC_BUREAU_V1"


def test_credit_score_delinquency_penalty():
    """Verify that overdue and defaulted facilities significantly lower the credit score."""
    clean_facilities = [
        {
            "facility_type": "CREDIT_CARD",
            "credit_limit": Decimal("50000.00"),
            "outstanding_balance": Decimal("5000.00"),
            "payment_status": "CURRENT"
        }
    ]
    delinquent_facilities = [
        {
            "facility_type": "CREDIT_CARD",
            "credit_limit": Decimal("50000.00"),
            "outstanding_balance": Decimal("48000.00"),
            "payment_status": "DEFAULTED"
        },
        {
            "facility_type": "PERSONAL_LOAN",
            "credit_limit": Decimal("100000.00"),
            "outstanding_balance": Decimal("90000.00"),
            "payment_status": "OVERDUE_90"
        }
    ]

    p_clean = derive_credit_score_and_profile("APP-CLEAN", clean_facilities, counter=1, seed=20261022)
    p_delinq = derive_credit_score_and_profile("APP-DELINQ", delinquent_facilities, counter=2, seed=20261022)

    assert p_delinq["synthetic_credit_score"] < p_clean["synthetic_credit_score"]
    assert p_delinq["credit_utilization"] > p_clean["credit_utilization"]


def test_credit_profile_batch_generation():
    """Verify batch generation of credit profiles maps 1:1 or 1:N with applicants."""
    applicants = generate_applicants(30, seed=20261022)
    facilities = generate_credit_facilities(applicants, seed=20261022)
    profiles = generate_credit_profiles(applicants, facilities, seed=20261022)

    assert len(profiles) == len(applicants)
    applicant_ids = {a["applicant_id"] for a in applicants}
    profile_applicant_ids = {p["applicant_id"] for p in profiles}

    # Every applicant has a corresponding credit profile
    assert profile_applicant_ids == applicant_ids

    # Uniqueness of primary key
    p_ids = [p["credit_profile_id"] for p in profiles]
    assert len(p_ids) == len(set(p_ids))
