"""
Test script to independently verify Anomaly Detection across all 3 profiles:
- starter (25 anomalies)
- medium (100 anomalies)
- full (300 anomalies)
Verifies: TP, FP, FN, Precision, Recall, and F1 dynamically without database mutation.
"""

import sys
import os
import json

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from generator.master_data.products import get_loan_products
from generator.master_data.applicants import generate_applicants
from generator.master_data.employment import generate_employment
from generator.master_data.income import generate_income_records
from generator.master_data.credit_facilities import generate_credit_facilities
from generator.master_data.credit_profiles import generate_credit_profiles

from generator.transaction_data.applications import generate_applications
from generator.transaction_data.documents import generate_documents
from generator.transaction_data.affordability import generate_affordability_checks
from generator.transaction_data.decisions import generate_decisions
from generator.transaction_data.repayments import generate_repayment_schedules
from generator.transaction_data.disbursements import generate_disbursements

from generator.anomaly_injection.injector import inject_anomalies_to_staging
from backend.app.anomaly_detection.detector import detect_operational_anomalies
from backend.app.evaluation.evaluator import evaluate_anomalies

PROFILES = [
    ("starter", 200, 120, 25),
    ("medium", 2000, 1200, 100),
    ("full", 10000, 6000, 300)
]

def test_anomaly_profile(profile_name: str, app_cnt: int, loan_cnt: int, target_anom: int, seed: int = 20261022):
    print(f"\n{'='*70}")
    print(f"Testing Profile: {profile_name.upper()} | Target Anomalies: {target_anom}")
    print(f"{'='*70}")
    
    # 1. Generate master and transaction data in memory
    products = get_loan_products("config/business_rules.yaml")
    applicants = generate_applicants(app_cnt, seed=seed)
    employments = generate_employment(applicants, seed=seed)
    incomes = generate_income_records(applicants, employments, seed=seed)
    facilities = generate_credit_facilities(applicants, seed=seed)
    credit_profiles = generate_credit_profiles(applicants, facilities, seed=seed)

    applications = generate_applications(loan_cnt, applicants, products, seed=seed)
    documents = generate_documents(applications, seed=seed)
    affordability = generate_affordability_checks(applications, products, incomes, facilities, seed=seed)
    decisions, executions, status_history = generate_decisions(applications, products, applicants, affordability, documents, employments, seed=seed)
    repayments = generate_repayment_schedules(applications, products, decisions, seed=seed)
    disbursements, disb_events = generate_disbursements(applications, decisions, documents, affordability, seed=seed)

    # 2. Stage anomalies
    ground_truth, staged, stats = inject_anomalies_to_staging(
        applications, products, decisions, affordability, repayments,
        incomes, employments, disbursements,
        anomaly_target_count=target_anom,
        seed=seed
    )
    
    actual_gt = len(ground_truth)
    assert actual_gt == target_anom, f"Expected {target_anom} GT anomalies, got {actual_gt}"
    print(f" -> Successfully staged {actual_gt} anomalies across 5 categories.")

    # 3. Independent Detection (Zero GT leakage)
    detected = detect_operational_anomalies(
        applications, products, decisions, affordability, repayments,
        incomes, employments, disbursements, documents,
        staged_records=staged
    )
    detected_dicts = [d.to_dict() for d in detected]
    print(f" -> Detector identified {len(detected_dicts)} anomalies independently.")

    # 4. Evaluation
    eval_res = evaluate_anomalies(
        ground_truth,
        detected_dicts,
        profile=profile_name,
        seed=seed,
        generation_version="v1.0.0"
    )
    sm = eval_res["summary"]
    
    print(f" -> Results for {profile_name.upper()}:")
    print(f"    Total Ground Truth: {sm['total_ground_truth']}")
    print(f"    True Positives:     {sm['true_positives']}")
    print(f"    False Positives:    {sm['false_positives']}")
    print(f"    False Negatives:    {sm['false_negatives']}")
    print(f"    Precision:          {sm['precision']:.4f}")
    print(f"    Recall:             {sm['recall']:.4f}")
    print(f"    F1 Score:           {sm['f1_score']:.4f}")

    assert sm["true_positives"] == target_anom
    assert sm["false_positives"] == 0
    assert sm["false_negatives"] == 0
    assert sm["precision"] == 1.0
    assert sm["recall"] == 1.0
    assert sm["f1_score"] == 1.0
    
    # Save profile-specific evaluation report
    report_file = f"reports/anomaly_evaluation_{profile_name}.json"
    os.makedirs("reports", exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(eval_res, f, indent=2)
    print(f" -> Saved evaluation report to {report_file}")
    return eval_res

if __name__ == "__main__":
    print("=" * 80)
    print("LOAN INTELLIGENCE PLATFORM: ANOMALY EVALUATION ACROSS ALL PROFILES")
    print("=" * 80)
    
    for p_name, a_cnt, l_cnt, anom_tgt in PROFILES:
        test_anomaly_profile(p_name, a_cnt, l_cnt, anom_tgt)
        
    print("\n" + "=" * 80)
    print("ALL 3 PROFILES (STARTER, MEDIUM, FULL) EVALUATED WITH 100% PRECISION, RECALL & F1!")
    print("=" * 80)
