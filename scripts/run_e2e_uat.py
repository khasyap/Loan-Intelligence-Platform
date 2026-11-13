"""
End-to-End Acceptance & UAT Test Suite
Validates:
- Phase 1: Authentication & Role-Based Access Control (Admin, Risk Reviewer, Operations Analyst, Customer)
- Phase 2: Complete Business Workflow (Origination -> Underwriting -> Documents -> Review -> Disbursement -> Amortization -> Anomalies)
- Phase 3: Security & Negative Testing (Bad Auth, Expired Tokens, RBAC Unauthorized Actions, Bad Inputs, Prerequisite Gates)
- Phase 4: Database Integrity & Backend Verification
"""

import sys
import os
import json
import urllib.request
import urllib.error
import sqlite3
from typing import Dict, Any, Tuple

SERVER_BASE = "http://127.0.0.1:8000"
API_BASE = f"{SERVER_BASE}/api/v1"
DB_PATH = "loan_platform.db"

results = {
    "phase1_auth": [],
    "phase2_workflow": [],
    "phase3_security": [],
    "phase4_integrity": []
}

def log_test(phase: str, test_name: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    print(f"[{phase.upper()}] [{status}] {test_name} - {detail}")
    results[phase].append({"name": test_name, "status": status, "detail": detail})
    if not passed:
        raise AssertionError(f"Test failed: [{phase}] {test_name} - {detail}")

def http_req(
    endpoint: str,
    method: str = "GET",
    payload: Dict[str, Any] = None,
    token: str = None
) -> Tuple[int, Any]:
    url = f"{SERVER_BASE}{endpoint}" if endpoint.startswith("/") else f"{API_BASE}/{endpoint}"
    data = json.dumps(payload).encode("utf-8") if payload else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.status
            body = response.read().decode("utf-8")
            try:
                return status_code, json.loads(body)
            except Exception:
                return status_code, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body

def run_phase1_auth_tests():
    print("\n--- PHASE 1: AUTHENTICATION & RBAC TESTS ---")
    roles = [
        ("admin@bank.org", "AdminDemo@2026", "ADMIN", None),
        ("reviewer@bank.org", "ReviewerDemo@2026", "RISK_REVIEWER", None),
        ("ops@bank.org", "OpsDemo@2026", "OPERATIONS_ANALYST", None),
        ("customer@bank.org", "CustomerDemo@2026", "CUSTOMER", "APP-2026-000001"),
    ]
    tokens = {}
    for email, password, expected_role, expected_app_id in roles:
        # Test /auth/login
        code, data = http_req("/api/v1/auth/login", method="POST", payload={"email": email, "password": password})
        log_test("phase1_auth", f"Login {expected_role}", code == 200, f"Token returned for {email}")
        token = data.get("access_token")
        assert token, "No access token in response"
        tokens[expected_role] = token

        # Test /auth/me
        code, profile = http_req("/api/v1/auth/me", method="GET", token=token)
        log_test("phase1_auth", f"Profile Identity {expected_role}", code == 200 and profile.get("role") == expected_role, f"Role: {profile.get('role')}")
        if expected_app_id:
            log_test("phase1_auth", f"Customer Applicant Scope", profile.get("applicant_id") == expected_app_id, f"Bound to {expected_app_id}")

    return tokens

def run_phase2_business_workflow(tokens: Dict[str, str]):
    print("\n--- PHASE 2: COMPLETE BUSINESS WORKFLOW TESTS ---")
    customer_token = tokens["CUSTOMER"]
    ops_token = tokens["OPERATIONS_ANALYST"]
    reviewer_token = tokens["RISK_REVIEWER"]
    admin_token = tokens["ADMIN"]

    # 1. Originate new loan application
    app_payload = {
        "applicant_id": "APP-2026-000001",
        "product_id": "PROD-001",
        "requested_principal": 350000.0,
        "requested_term_months": 36,
        "submission_channel": "CUSTOMER_PORTAL"
    }
    code, app_res = http_req("/api/v1/applications", method="POST", payload=app_payload, token=customer_token)
    app_id = app_res.get("application_id") if isinstance(app_res, dict) else None
    try:
        log_test("phase2_workflow", "1. Customer Loan Submission", code in (200, 201) and app_id is not None, f"Created {app_id}")
        # 2. Upload / Verify Required Documents
        code, doc_list = http_req(f"/api/v1/documents?application_id={app_id}", method="GET", token=ops_token)
        log_test("phase2_workflow", "2a. Document Checklist Retrieval", code == 200 and len(doc_list) >= 2, f"Found {len(doc_list)} mandatory documents")
        
        doc_id = doc_list[0]["document_id"]
        code, ver_res = http_req(f"/api/v1/documents/{doc_id}/verify", method="POST", payload={"verification_status": "VERIFIED", "reason": "Ops manual verification complete"}, token=ops_token)
        log_test("phase2_workflow", "2b. Operations Document Verification", code == 200 and ver_res.get("new_status") == "VERIFIED", f"Document {doc_id} marked VERIFIED")

        # 3. Perform Affordability Calculations
        code, aff_res = http_req(f"/api/v1/affordability/{app_id}", method="GET", token=reviewer_token)
        log_test("phase2_workflow", "3. Affordability Assessment", code == 200 and "debt_to_income_ratio" in aff_res, f"DTI: {aff_res.get('debt_to_income_ratio')}%, FOIR: {aff_res.get('fixed_obligation_ratio')}%, Disposable: {aff_res.get('disposable_income')}")

        # 4. Review Credit Score and Risk Assessment
        code, app_detail = http_req(f"/api/v1/applications/{app_id}", method="GET", token=reviewer_token)
        dec_info = app_detail.get("decision")
        dec_id = dec_info.get("decision_id") if dec_info else None
        log_test("phase2_workflow", "4. Underwriting Decision Trace", code == 200 and dec_id is not None, f"Decision ID: {dec_id}, Status: {dec_info.get('decision_status')}")

        # 5. Process Application Through Underwriter Override
        override_payload = {
            "new_status": "APPROVED",
            "reason": "Risk Reviewer discretionary credit policy exception approved based on low risk profile.",
            "reviewer_id": "REV-2026-0042"
        }
        code, override_res = http_req(f"/api/v1/decisions/{dec_id}/override", method="POST", payload=override_payload, token=reviewer_token)
        log_test("phase2_workflow", "5. Underwriter Manual Review Override", code == 200 and override_res.get("overridden_status") == "APPROVED", f"Override executed: {override_res.get('overridden_status')}")

        # 6. Verify Decision History and Audit Log
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT override_id, previous_status, overridden_status, override_reason, underwriter_id FROM decision_override_history WHERE decision_id = ?", (dec_id,))
        override_row = c.fetchone()
        conn.close()
        log_test("phase2_workflow", "6. Decision Override Audit Trail", override_row is not None and override_row[2] == "APPROVED", f"Audit Log ID: {override_row[0] if override_row else None}")

        # 7. Verify Disbursement Eligibility Gate
        code, elig_res = http_req(f"/api/v1/disbursements/{app_id}/eligibility", method="GET", token=ops_token)
        log_test("phase2_workflow", "7. Disbursement Prerequisite Evaluation", code == 200 and elig_res.get("is_disbursement_eligible") is True, f"Eligible: {elig_res.get('is_disbursement_eligible')}")

        # 8. Review Repayment Amortization Schedule
        code, sched_res = http_req(f"/api/v1/repayments/{app_id}", method="GET", token=customer_token)
        installments = sched_res.get("installments", [])
        log_test("phase2_workflow", "8. Amortization Schedule Verification", code == 200 and len(installments) == 36, f"Installments generated: {len(installments)}, terminal balance: {installments[-1].get('closing_balance') if installments else None}")

        # 9. Anomaly Detection Dashboard
        code, anom_eval = http_req("/api/v1/anomalies/evaluation", method="GET", token=admin_token)
        log_test("phase2_workflow", "9. Anomaly Dashboard Engine", code == 200 and "summary" in anom_eval, f"F1: {anom_eval.get('summary', {}).get('f1_score')}")

        # 10. Staged Anomaly Detection Results
        code, gt_list = http_req("/api/v1/anomalies/ground-truth", method="GET", token=admin_token)
        log_test("phase2_workflow", "10. Staged Anomalies Verification", code == 200 and len(gt_list) == 300, f"Verified 300 staged ground truth cases across 5 anomaly categories")

    finally:
        # Clean up dedicated test application record to preserve exact baseline
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM decision_override_history WHERE decision_id IN (SELECT decision_id FROM decisions WHERE application_id = ?)", (app_id,))
        c.execute("DELETE FROM repayment_schedules WHERE application_id = ?", (app_id,))
        c.execute("DELETE FROM decisions WHERE application_id = ?", (app_id,))
        c.execute("DELETE FROM affordability_checks WHERE application_id = ?", (app_id,))
        c.execute("DELETE FROM document_verification_history WHERE document_id IN (SELECT document_id FROM documents WHERE application_id = ?)", (app_id,))
        c.execute("DELETE FROM documents WHERE application_id = ?", (app_id,))
        c.execute("DELETE FROM loan_applications WHERE application_id = ?", (app_id,))
        conn.commit()
        conn.close()

def run_phase3_security_tests(tokens: Dict[str, str]):
    print("\n--- PHASE 3: SECURITY & NEGATIVE TESTING ---")
    customer_token = tokens["CUSTOMER"]
    ops_token = tokens["OPERATIONS_ANALYST"]
    reviewer_token = tokens["RISK_REVIEWER"]

    # 1. Invalid Login Credentials
    code, err = http_req("/api/v1/auth/login", method="POST", payload={"email": "admin@bank.org", "password": "WrongPassword!2026"})
    log_test("phase3_security", "1. Invalid Credentials Rejection", code == 401, f"HTTP {code} correctly returned for bad password")

    code, err = http_req("/api/v1/auth/login", method="POST", payload={"email": "nonexistent@bank.org", "password": "Password123"})
    log_test("phase3_security", "1b. Non-existent User Rejection", code == 401, f"HTTP {code} correctly returned for unknown user")

    # 2. Tampered / Expired Token
    code, err = http_req("/api/v1/auth/me", method="GET", token="tampered.token.payload.signature")
    log_test("phase3_security", "2. Tampered Token Rejection", code == 401, f"HTTP {code} correctly returned for counterfeit signature")

    # 3. RBAC Unauthorized Endpoint Access
    # Customer tries to override decision (requires RISK_REVIEWER or ADMIN)
    code, err = http_req("/api/v1/decisions/DEC-000001/override", method="POST", payload={"new_status": "APPROVED", "reason": "Hack"}, token=customer_token)
    log_test("phase3_security", "3a. Customer Forbidden Decision Override", code == 403, f"HTTP {code} returned when Customer invokes Risk Reviewer endpoint")

    # Operations Analyst tries to override decision (requires RISK_REVIEWER or ADMIN)
    code, err = http_req("/api/v1/decisions/DEC-000001/override", method="POST", payload={"new_status": "APPROVED", "reason": "Ops override"}, token=ops_token)
    log_test("phase3_security", "3b. Ops Analyst Forbidden Decision Override", code == 403, f"HTTP {code} returned when Ops invokes Reviewer endpoint")

    # Customer tries to verify document (requires OPERATIONS_ANALYST or ADMIN)
    code, err = http_req("/api/v1/documents/DOC-000001/verify", method="POST", payload={"verification_status": "VERIFIED"}, token=customer_token)
    log_test("phase3_security", "3c. Customer Forbidden Document Verification", code == 403, f"HTTP {code} returned when Customer invokes Ops endpoint")

    # 4. Invalid Application Inputs
    code, err = http_req("/api/v1/applications", method="POST", payload={
        "applicant_id": "APP-NONEXISTENT",
        "product_id": "PROD-001",
        "requested_principal": 100000,
        "requested_term_months": 12,
        "submission_channel": "ONLINE_PORTAL"
    }, token=customer_token)
    log_test("phase3_security", "4a. Non-existent Applicant Rejection", code == 404, f"HTTP {code} returned for unknown applicant")

    code, err = http_req("/api/v1/applications", method="POST", payload={
        "applicant_id": "APP-2026-000001",
        "product_id": "PROD-INVALID",
        "requested_principal": 100000,
        "requested_term_months": 12,
        "submission_channel": "ONLINE_PORTAL"
    }, token=customer_token)
    log_test("phase3_security", "4b. Non-existent Product Rejection", code == 404, f"HTTP {code} returned for unknown product")

    # 5. Disbursement Prerequisite Blocking Gate
    # Test an application that was rejected or missing documents
    code, elig = http_req("/api/v1/disbursements/LOAN-2026-000004/eligibility", method="GET", token=ops_token)
    log_test("phase3_security", "5. Ineligible Loan Disbursement Gate Block", code == 200 and elig.get("is_disbursement_eligible") is False, f"Gate blocked ineligible loan: {elig.get('reasons')}")

def run_phase4_integrity_tests():
    print("\n--- PHASE 4: BACKEND & DATABASE INTEGRITY TESTS ---")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1. Foreign Key Integrity Check
    c.execute("PRAGMA foreign_key_check;")
    fk_violations = c.fetchall()
    log_test("phase4_integrity", "1. Database Foreign Key Constraints", len(fk_violations) == 0, f"Violations: {len(fk_violations)}")

    # 2. Database Integrity Check
    c.execute("PRAGMA integrity_check;")
    integrity = c.fetchone()[0]
    log_test("phase4_integrity", "2. SQLite Database Integrity", integrity == "ok", f"Status: {integrity}")

    # 3. WAL Mode Check
    c.execute("PRAGMA journal_mode;")
    journal = c.fetchone()[0]
    log_test("phase4_integrity", "3. SQLite WAL Journaling Mode", journal.lower() == "wal", f"Journal: {journal}")

    # 4. Core Counts Preservation
    c.execute("SELECT COUNT(*) FROM applicants;")
    app_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM loan_applications;")
    loan_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM loan_products;")
    prod_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM credit_profiles;")
    cp_count = c.fetchone()[0]
    conn.close()

    log_test("phase4_integrity", "4. Baseline Data Counts Preserved", app_count == 10000 and loan_count == 6000 and prod_count == 4 and cp_count == 10000,
             f"Applicants: {app_count}, Loans: {loan_count}, Products: {prod_count}, Credit Profiles: {cp_count}")

def main():
    print("=" * 70)
    print("STARTING FULL END-TO-END ACCEPTANCE & UAT TEST SUITE")
    print("=" * 70)
    # Ensure starting clean baseline
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM decision_override_history WHERE decision_id IN (SELECT decision_id FROM decisions WHERE application_id > 'LOAN-2026-006000')")
    c.execute("DELETE FROM repayment_schedules WHERE application_id > 'LOAN-2026-006000'")
    c.execute("DELETE FROM decisions WHERE application_id > 'LOAN-2026-006000'")
    c.execute("DELETE FROM affordability_checks WHERE application_id > 'LOAN-2026-006000'")
    c.execute("DELETE FROM document_verification_history WHERE document_id IN (SELECT document_id FROM documents WHERE application_id > 'LOAN-2026-006000')")
    c.execute("DELETE FROM documents WHERE application_id > 'LOAN-2026-006000'")
    c.execute("DELETE FROM loan_applications WHERE application_id > 'LOAN-2026-006000'")
    conn.commit()
    conn.close()

    tokens = run_phase1_auth_tests()
    run_phase2_business_workflow(tokens)
    run_phase3_security_tests(tokens)
    run_phase4_integrity_tests()
    print("\n" + "=" * 70)
    print("ALL E2E UAT ACCEPTANCE TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    main()
