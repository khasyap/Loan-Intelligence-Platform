# Validation Methodology & Automated Integrity Audits

## 1. Overview
The platform features an automated, multi-tiered validation suite (`backend/app/validation/validator.py`) and a comprehensive regulatory evaluation service (`backend/app/evaluation/comprehensive_metrics.py`) executing five primary audit tiers:

### Tier 1: Structural Integrity & Uniqueness
- Verifies primary key uniqueness for all core entities (`applicants`, `credit_profiles`, `loan_applications`, `decisions`, `disbursements`, etc.).
- Validates identifier regex formats (`APP-2026-XXXXXX`, `CP-2026-XXXXXX`, `LOAN-2026-XXXXXX`).
- Validates data types, required non-null constraints, and enumeration domains.

### Tier 2: Relational & Referential Integrity
- Asserts zero orphaned child records.
- Every `LoanApplication` must resolve to an active `Applicant` and valid `LoanProduct`.
- Every `CreditProfile` must resolve to an active `Applicant`.
- Every `Document`, `AffordabilityCheck`, `Decision`, `RepaymentSchedule`, and `Disbursement` must map to an existing `LoanApplication`.
- Referential integrity check rate: **100.0%**.

### Tier 3: Lifecycle Consistency & State Machine Compliance
- Validates that state transitions follow permitted pathways (`SUBMITTED` -> `UNDER_REVIEW` -> `APPROVED` / `REJECTED` / `MANUAL_REVIEW`).
- Asserts that `decisions.decision_timestamp >= affordability_checks.assessment_timestamp`.
- Asserts that no loan with a `REJECTED` decision is ever disbursed.
- Asserts zero auto-disbursement prior to 100% document verification.

### Tier 4: Financial & Arithmetic Precision
- Verifies Existing DTI matches $(Debt / Gross) \times 100$ within $0.05\%$ tolerance.
- Verifies FOIR matches $((Debt + EMI) / Net) \times 100$ within $0.05\%$ tolerance.
- Verifies that $\text{Disposable Income} = \text{Net} - \text{Debt} - \text{Proposed EMI}$.
- Audits repayment schedules to confirm $\sum Principal = Disbursed Principal$ and final closing balance $= 0.00$.
- Financial calculation error rate: **0.0%**.
- Repayment schedule reconciliation rate: **100.0%**.

### Tier 5: Fair Lending, Prohibited Features & Anti-Leakage
- Audits all decision rule execution traces to guarantee **zero protected attributes** (gender, race, ethnicity, religion, marital status) are evaluated.
- Checks Python inspection signatures to guarantee zero ground-truth label leakage into the anomaly detector.

---

## 2. Validation Reports & Generated Artifacts

Validation results and evaluation metrics are compiled and exported to:
- `reports/comprehensive_evaluation.json`: High-level portfolio, fairness, math, and anomaly metrics.
- `reports/validation_summary.json`: Detailed validation check breakdown by category.
- `reports/validation_summary.csv`: Tabular audit ledger of every validation rule tested.
- `reports/reproducibility_report.json`: Cryptographic SHA-256 comparison proving 100% bit-for-bit repeatability.
