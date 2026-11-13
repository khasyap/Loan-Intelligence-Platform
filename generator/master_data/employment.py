"""
Master Data Generator: Employment History
Generates 1 to 2 employment records per applicant.
"""

from decimal import Decimal
import datetime
from typing import List, Dict, Any
import numpy as np

EMPLOYERS = [
    "Tata Consultancy Services", "Infosys Technologies", "HDFC Bank Ltd",
    "Reliance Industries", "Wipro Limited", "ICICI Bank", "Larsen & Toubro",
    "Bharti Airtel", "State Bank of India", "Mahindra & Mahindra",
    "Cognizant Tech", "Apex Healthcare", "National Retail Chain",
    "Pinnacle Software Solutions", "Zenith Financial Services"
]

INDUSTRIES = ["IT", "FINANCE", "HEALTHCARE", "MANUFACTURING", "RETAIL", "EDUCATION", "SERVICES"]

JOB_TITLES = [
    "Software Engineer", "Senior Analyst", "Operations Manager",
    "Accountant", "Sales Executive", "Project Lead", "Consultant",
    "System Administrator", "Quality Assurance Engineer", "Branch Manager"
]

def generate_employment(applicants: List[Dict[str, Any]], seed: int = 20261022) -> List[Dict[str, Any]]:
    rng = np.random.default_rng(seed + 1)
    employments = []
    emp_counter = 1

    for app in applicants:
        app_id = app["applicant_id"]
        # Determine employment type
        p = rng.random()
        if p < 0.68:
            emp_type = "SALARIED"
            monthly_salary = Decimal(str(int(rng.integers(30000, 250000))))
        elif p < 0.90:
            emp_type = "SELF_EMPLOYED"
            monthly_salary = Decimal(str(int(rng.integers(45000, 350000))))
        elif p < 0.97:
            emp_type = "FREELANCE"
            monthly_salary = Decimal(str(int(rng.integers(25000, 150000))))
        else:
            emp_type = "UNEMPLOYED"
            monthly_salary = Decimal("0.00")

        # Tenure: 6 months to 10 years
        tenure_months = int(rng.integers(6, 120))
        start_year = 2026 - (tenure_months // 12)
        start_month = max(1, min(12, 12 - (tenure_months % 12)))
        start_date = datetime.date(start_year, start_month, 1)

        employer = EMPLOYERS[rng.integers(0, len(EMPLOYERS))] if emp_type != "UNEMPLOYED" else "N/A"
        job_title = JOB_TITLES[rng.integers(0, len(JOB_TITLES))] if emp_type != "UNEMPLOYED" else "Unemployed"
        industry = INDUSTRIES[rng.integers(0, len(INDUSTRIES))] if emp_type != "UNEMPLOYED" else "SERVICES"

        # Verification status
        v_rand = rng.random()
        if v_rand < 0.88:
            v_status = "VERIFIED"
        elif v_rand < 0.96:
            v_status = "PENDING"
        else:
            v_status = "REJECTED"

        emp_id = f"EMP-2026-{emp_counter:06d}"
        emp_counter += 1

        employments.append({
            "employment_id": emp_id,
            "applicant_id": app_id,
            "employer_name": employer,
            "employment_type": emp_type,
            "industry": industry,
            "job_title": job_title,
            "employment_start_date": start_date,
            "employment_end_date": None,
            "monthly_salary": monthly_salary,
            "employment_status": "CURRENT" if emp_type != "UNEMPLOYED" else "TERMINATED",
            "verification_status": v_status
        })

    return employments

