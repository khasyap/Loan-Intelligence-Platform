"""
Master Data: 4 Configurable Loan Products
"""

from decimal import Decimal
import datetime
from typing import List, Dict, Any
import yaml

def get_loan_products(config_path: str = "config/business_rules.yaml") -> List[Dict[str, Any]]:
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    products = []
    for p in config.get("products", []):
        products.append({
            "product_id": p["product_id"],
            "product_name": p["product_name"],
            "product_type": p["product_type"],
            "min_principal": Decimal(str(p["min_principal"])),
            "max_principal": Decimal(str(p["max_principal"])),
            "min_term_months": int(p["min_term_months"]),
            "max_term_months": int(p["max_term_months"]),
            "annual_interest_rate": Decimal(str(p["annual_interest_rate"])),
            "processing_fee_rate": Decimal(str(p["processing_fee_rate"])),
            "maximum_dti": Decimal(str(p["maximum_dti"])),
            "maximum_foir": Decimal(str(p["maximum_foir"])),
            "minimum_credit_score": int(p["minimum_credit_score"]),
            "product_status": p.get("product_status", "ACTIVE"),
            "effective_from": datetime.date(2026, 1, 1),
            "effective_to": None
        })
    return products

