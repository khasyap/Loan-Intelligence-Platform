"""
Transaction Data Generator: Document Submissions & Verification
Generates mandatory checklist documents and simulated verification outcomes.
"""

import datetime
from typing import List, Dict, Any
import numpy as np

DOC_TYPES = ["IDENTITY_PROOF", "ADDRESS_PROOF", "INCOME_PROOF", "EMPLOYMENT_PROOF"]

REJECTION_REASONS = [
    "Illegible scan / low resolution",
    "Name mismatch between ID and application",
    "Expired document presented",
    "Missing official company seal/stamp",
    "Address proof older than 90 days"
]

def generate_documents(applications: List[Dict[str, Any]], seed: int = 20261022) -> List[Dict[str, Any]]:
    rng = np.random.default_rng(seed + 20)
    documents = []

    for app in applications:
        app_id = app["application_id"]
        app_date = app["application_date"]

        # Each application generates 3 to 4 documents
        num_docs = 4 if rng.random() < 0.90 else 3

        for seq in range(1, num_docs + 1):
            doc_type = DOC_TYPES[seq - 1]
            doc_id = f"DOC-{app_id}-{seq:03d}"
            submitted_at = app_date + datetime.timedelta(minutes=int(rng.integers(10, 180)))

            # Verification outcomes
            p = rng.random()
            if p < 0.88:
                v_status = "VERIFIED"
                sub_status = "VERIFIED"
                verified_at = submitted_at + datetime.timedelta(hours=int(rng.integers(2, 24)))
                expiry = datetime.date(2028, 12, 31)
                reason = None
            elif p < 0.94:
                v_status = "PENDING"
                sub_status = "UNDER_REVIEW"
                verified_at = None
                expiry = datetime.date(2028, 12, 31)
                reason = None
            elif p < 0.97:
                v_status = "REJECTED"
                sub_status = "REJECTED"
                verified_at = submitted_at + datetime.timedelta(hours=int(rng.integers(1, 12)))
                expiry = datetime.date(2028, 12, 31)
                reason = REJECTION_REASONS[rng.integers(0, len(REJECTION_REASONS))]
            else:
                v_status = "EXPIRED"
                sub_status = "EXPIRED"
                verified_at = submitted_at + datetime.timedelta(hours=int(rng.integers(1, 12)))
                expiry = datetime.date(2025, 11, 30)  # Past date
                reason = "Document has passed valid expiration date"

            documents.append({
                "document_id": doc_id,
                "application_id": app_id,
                "document_type": doc_type,
                "submission_status": sub_status,
                "verification_status": v_status,
                "submitted_at": submitted_at,
                "verified_at": verified_at,
                "expiry_date": expiry,
                "rejection_reason": reason,
                "document_reference": f"REF-HASH-{doc_id}"
            })

    return documents

