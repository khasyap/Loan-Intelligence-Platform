"""
Master Synthetic Data Generation Orchestrator:
Coordinates the generation of master data, CreditProfiles, transaction workflows,
affordability checks, underwriting decisions, amortization schedules, anomaly staging,
comprehensive validations, and exports.
"""

import os
import sys
import argparse
import datetime
import yaml
import json
from decimal import Decimal

# Ensure project root is in sys.path
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
from backend.app.evaluation.comprehensive_metrics import compute_comprehensive_evaluation
from backend.app.validation.validator import run_system_validation, write_validation_reports
from generator.exporters.exporter import export_all_datasets

from backend.app.database.connection import engine, SessionLocal, Base
from backend.app.models.entities import (
    Applicant, Employment, IncomeRecord, CreditFacility, CreditProfile, LoanProduct,
    LoanApplication, Document, AffordabilityCheck, Decision, RepaymentSchedule,
    ApplicationStatusHistory, DecisionRuleExecution, Disbursement,
    DisbursementEvent, DatasetGenerationRun, GroundTruthAnomaly
)

def run_pipeline(profile: str = "starter", custom_seed: int = 20261022, seed_db: bool = True):
    print("=" * 80)
    print(f"LOAN INTELLIGENCE PLATFORM: SYNTHETIC DATA GENERATION ENGINE")
    print(f"Profile: {profile.upper()} | Seed: {custom_seed} | Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print("=" * 80)

    start_time = datetime.datetime.now(datetime.timezone.utc)

    # 1. Load Configuration
    with open("config/generation.yaml", "r", encoding="utf-8") as f:
        gen_cfg = yaml.safe_load(f)

    if profile not in gen_cfg["profiles"]:
        raise ValueError(f"Unknown profile '{profile}'. Choose from: {list(gen_cfg['profiles'].keys())}")

    p_cfg = gen_cfg["profiles"][profile]
    applicant_count = p_cfg["applicant_count"]
    application_count = p_cfg["application_count"]
    anomaly_count = p_cfg["anomaly_count"]

    print(f"\n[1/8] Generating Master Data...")
    print(f" -> 4 Loan Products...")
    products = get_loan_products("config/business_rules.yaml")
    print(f" -> {applicant_count:,} Synthetic Applicants...")
    applicants = generate_applicants(applicant_count, seed=custom_seed)
    print(f" -> Employment Profiles...")
    employments = generate_employment(applicants, seed=custom_seed)
    print(f" -> Income Records...")
    income_records = generate_income_records(applicants, employments, seed=custom_seed)
    print(f" -> Existing Credit Facilities...")
    credit_facilities = generate_credit_facilities(applicants, seed=custom_seed)

    print(f"\n[2/8] Deriving Grounded Credit Profiles & Behavioral Scores...")
    credit_profiles = generate_credit_profiles(applicants, credit_facilities, seed=custom_seed)
    print(f" -> Generated {len(credit_profiles):,} CreditProfile records synchronized with bureau history.")

    print(f"\n[3/8] Generating Transaction Origination Data...")
    print(f" -> {application_count:,} Loan Applications...")
    applications = generate_applications(application_count, applicants, products, seed=custom_seed)
    print(f" -> Supporting Documents...")
    documents = generate_documents(applications, seed=custom_seed)

    print(f"\n[4/8] Financial Calculations & Affordability Assessments...")
    affordability_checks = generate_affordability_checks(
        applications, products, income_records, credit_facilities, seed=custom_seed
    )

    print(f"\n[5/8] Underwriting Decision Rules Engine Execution (Precedence & Overrides)...")
    decisions, executions, status_history = generate_decisions(
        applications, products, applicants, affordability_checks, documents, employments, seed=custom_seed
    )

    print(f"\n[6/8] Repayment Schedule Amortization & Disbursement Eligibility...")
    repayment_schedules = generate_repayment_schedules(
        applications, products, decisions, seed=custom_seed
    )
    disbursements, disb_events = generate_disbursements(
        applications, decisions, documents, affordability_checks, seed=custom_seed
    )

    print(f"\n[7/8] Anomaly Staging Layer & Ground Truth Separation...")
    ground_truth, staged_anomalies, anom_stats = inject_anomalies_to_staging(
        applications, products, decisions, affordability_checks, repayment_schedules,
        income_records, employments, disbursements,
        anomaly_target_count=anomaly_count, seed=custom_seed
    )
    print(f" -> Injected {len(ground_truth)} anomalies into isolated staging layer.")

    # Persist staged anomalies for independent auditing and compliance verification
    os.makedirs("data/anomalies", exist_ok=True)
    with open("data/anomalies/staged_anomalies.json", "w", encoding="utf-8") as f:
        def json_serial(obj):
            if isinstance(obj, (datetime.date, datetime.datetime)):
                return obj.isoformat()
            if isinstance(obj, Decimal):
                return float(obj)
            raise TypeError(f"Type {type(obj)} not serializable")
        json.dump(staged_anomalies, f, indent=2, default=json_serial)


    print(f"\n[8/8] Independent Anomaly Detection, Comprehensive Evaluation & Validation...")
    # Detection: inspects operational + staged pool, ZERO ground-truth leakage
    detected = detect_operational_anomalies(
        applications, products, decisions, affordability_checks, repayment_schedules,
        income_records, employments, disbursements, documents,
        staged_records=staged_anomalies
    )
    detected_dicts = [d.to_dict() for d in detected]

    # Evaluation against ground truth
    eval_results = evaluate_anomalies(ground_truth, detected_dicts)
    os.makedirs("reports", exist_ok=True)
    with open("reports/anomaly_evaluation.json", "w", encoding="utf-8") as f:
        json.dump(eval_results, f, indent=2)

    end_time = datetime.datetime.now(datetime.timezone.utc)
    comp_eval = compute_comprehensive_evaluation(
        applicants, applications, products, decisions, affordability_checks,
        repayment_schedules, disbursements, ground_truth, detected_dicts,
        start_time, end_time
    )
    with open("reports/comprehensive_evaluation.json", "w", encoding="utf-8") as f:
        json.dump(comp_eval, f, indent=2)

    print(f" -> Comprehensive Evaluation Summary:")
    print(f"    Decision Consistency:  {comp_eval['quality_and_compliance']['decision_rule_consistency_pct']}%")
    print(f"    Math Error Rate:       {comp_eval['quality_and_compliance']['financial_calculation_error_rate_pct']}%")
    print(f"    Schedule Reconciled:   {comp_eval['quality_and_compliance']['repayment_reconciliation_rate_pct']}%")
    print(f"    Referential Integrity: {comp_eval['quality_and_compliance']['referential_integrity_rate_pct']}%")
    print(f"    Anomaly Precision:     {eval_results['summary']['precision'] * 100:.2f}%")
    print(f"    Anomaly Recall:        {eval_results['summary']['recall'] * 100:.2f}%")
    print(f"    Anomaly F1 Score:      {eval_results['summary']['f1_score'] * 100:.2f}%")

    # Structural, Relational, Lifecycle & Arithmetic Validation
    val_summary = run_system_validation(
        applicants, employments, income_records, credit_facilities, products,
        applications, documents, affordability_checks, decisions, repayment_schedules,
        disbursements
    )
    write_validation_reports(val_summary, "reports")
    print(f" -> Validation Suite: {val_summary['passed_checks']}/{val_summary['total_checks']} checks passed.")

    # Export all datasets
    print(f"\nExporting Datasets to CSV, JSON, SQL...")
    dataset_bundle = {
        "applicants": applicants,
        "employments": employments,
        "income_records": income_records,
        "credit_facilities": credit_facilities,
        "credit_profiles": credit_profiles,
        "loan_products": products,
        "loan_applications": applications,
        "documents": documents,
        "affordability_checks": affordability_checks,
        "decisions": decisions,
        "repayment_schedules": repayment_schedules,
        "application_status_history": status_history,
        "disbursements": disbursements,
        "ground_truth": ground_truth
    }
    manifest = export_all_datasets(dataset_bundle, "data")
    print(f" -> Successfully exported {manifest['total_records']:,} operational records into data/exports/")

    if seed_db:
        print(f"\nSeeding Relational Database (20 tables)...")
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            for tbl in reversed(Base.metadata.sorted_tables):
                db.execute(tbl.delete())
            db.commit()

            for p in products:
                db.add(LoanProduct(**p))
            db.commit()

            for a in applicants:
                db.add(Applicant(**a))
            db.commit()

            for e in employments:
                db.add(Employment(**e))
            db.commit()

            for inc in income_records:
                db.add(IncomeRecord(**inc))
            db.commit()

            for fac in credit_facilities:
                db.add(CreditFacility(**fac))
            db.commit()

            for cp in credit_profiles:
                db.add(CreditProfile(**cp))
            db.commit()

            for app in applications:
                db.add(LoanApplication(**app))
            db.commit()

            for doc in documents:
                db.add(Document(**doc))
            db.commit()

            for aff in affordability_checks:
                db.add(AffordabilityCheck(**aff))
            db.commit()

            for dec in decisions:
                dec_copy = dict(dec)
                if isinstance(dec_copy["rules_triggered"], list):
                    dec_copy["rules_triggered"] = json.dumps(dec_copy["rules_triggered"])
                db.add(Decision(**dec_copy))
            db.commit()

            for s in repayment_schedules:
                db.add(RepaymentSchedule(**s))
            db.commit()

            for h in status_history:
                db.add(ApplicationStatusHistory(**h))
            db.commit()

            seen_disb_apps = set()
            for disb in disbursements:
                if disb["application_id"] not in seen_disb_apps:
                    seen_disb_apps.add(disb["application_id"])
                    db.add(Disbursement(**disb))
            db.commit()

            for gt in ground_truth:
                db.add(GroundTruthAnomaly(**gt))
            db.commit()

            run_rec = DatasetGenerationRun(
                run_id=f"RUN-{int(start_time.timestamp())}",
                seed=custom_seed,
                profile=profile,
                applicant_count=len(applicants),
                application_count=len(applications),
                anomaly_count=len(ground_truth),
                config_hash="sha256:gen_config_hash",
                started_at=start_time,
                completed_at=end_time
            )
            db.add(run_rec)
            db.commit()
            print(" -> Relational database seeded successfully!")
        except Exception as ex:
            db.rollback()
            print(f" [!] Database seeding error: {ex}")
            raise
        finally:
            db.close()

    duration = (datetime.datetime.now(datetime.timezone.utc) - start_time).total_seconds()
    print("=" * 80)
    print(f"PIPELINE COMPLETED SUCCESSFULLY in {duration:.2f} seconds!")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synthetic Data Generation Pipeline")
    parser.add_argument("--profile", choices=["starter", "medium", "full"], default="starter", help="Generation scale")
    parser.add_argument("--seed", type=int, default=20261022, help="Pseudorandom generator seed")
    parser.add_argument("--no-db", action="store_true", help="Skip database seeding")
    args = parser.parse_args()

    run_pipeline(profile=args.profile, custom_seed=args.seed, seed_db=not args.no_db)
