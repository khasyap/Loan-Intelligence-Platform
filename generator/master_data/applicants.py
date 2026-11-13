"""
Master Data Generator: Synthetic Applicants
Ensures deterministic generation using seed, zero protected attributes,
and realistic demographic/geographic distributions.
"""

import datetime
from typing import List, Dict, Any
from faker import Faker
import numpy as np

CITIES = [
    ("Mumbai", "Maharashtra", "400001"),
    ("Bengaluru", "Karnataka", "560001"),
    ("Delhi", "Delhi", "110001"),
    ("Hyderabad", "Telangana", "500001"),
    ("Pune", "Maharashtra", "411001"),
    ("Chennai", "Tamil Nadu", "600001"),
    ("Kolkata", "West Bengal", "700001"),
    ("Ahmedabad", "Gujarat", "380001"),
    ("Jaipur", "Rajasthan", "302001"),
    ("Chandigarh", "Punjab", "160001"),
    ("Kochi", "Kerala", "682001"),
    ("Indore", "Madhya Pradesh", "452001")
]

def generate_applicants(count: int, seed: int = 20261022) -> List[Dict[str, Any]]:
    fake = Faker()
    Faker.seed(seed)
    rng = np.random.default_rng(seed)

    applicants = []
    # Vectorized credit score generation
    credit_scores = rng.normal(loc=710, scale=75, size=count)
    credit_scores = np.clip(np.round(credit_scores), 300, 900).astype(int)

    base_time = datetime.datetime(2026, 1, 1, 9, 0, 0)

    for i in range(1, count + 1):
        app_id = f"APP-2026-{i:06d}"
        first_name = fake.first_name()
        last_name = fake.last_name()
        clean_first = "".join(filter(str.isalnum, first_name.lower()))
        clean_last = "".join(filter(str.isalnum, last_name.lower()))
        email = f"{clean_first}.{clean_last}.{i}@example.org"
        phone = f"+9198{rng.integers(10000000, 99999999)}"

        city_info = CITIES[i % len(CITIES)]
        city, state, postal = city_info

        # Age 21 to 65
        birth_year = 2026 - int(rng.integers(22, 63))
        birth_month = int(rng.integers(1, 13))
        birth_day = int(rng.integers(1, 28))
        dob = datetime.date(birth_year, birth_month, birth_day)

        created_at = base_time + datetime.timedelta(minutes=int(i * 15))

        applicants.append({
            "applicant_id": app_id,
            "first_name": first_name,
            "last_name": last_name,
            "date_of_birth": dob,
            "email": email,
            "phone": phone,
            "city": city,
            "state": state,
            "postal_code": postal,
            "applicant_status": "ACTIVE",
            "credit_score": int(credit_scores[i - 1]),
            "created_at": created_at
        })

    return applicants

