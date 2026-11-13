# Implementation Plan: Loan Origination, Risk Assessment & Decision Intelligence Platform

## Executive Summary
This document provides the master technical blueprint and phased execution strategy for the **Loan Intelligence Platform** — an enterprise-grade, end-to-end loan origination, affordability assessment, risk evaluation, decision management, and disbursement eligibility system built for high-throughput synthetic simulation, compliance auditing, and decision explainability.

---

## 1. System Objectives & Guiding Principles

1. **Deterministic Reproducibility**: Using a fixed global seed (`20261022`), all master data, financial calculations, document workflows, decisions, repayment schedules, and anomaly injections produce bit-for-bit identical outputs across runs.
2. **Strict Ground-Truth Isolation & Anomaly Staging**: Zero data leakage. Anomaly ground truth and expected labels are persisted in a completely segregated data store (`data/ground_truth.csv`). Operational database integrity constraints are preserved by staging deliberate malformed records in an isolated exception queue (`staged_anomalies`).
3. **No Unfair Discrimination**: Protected demographic attributes (e.g., gender, race, religion, marital status) are strictly excluded from all eligibility, risk scoring, and credit decisions.
4. **Relational Integrity with Enterprise Constraints**: Comprehensive foreign key enforcement, immutable audit logging, non-overwriting historical state machines (`ApplicationStatusHistory`, `Decision`, `DocumentVerificationHistory`), human underwriter override history (`DecisionOverrideHistory`), and database-level unique constraints preventing duplicate disbursements.
5. **Multi-Scale Elastic Generation**: Parametric generation supporting three documented profiles:
   - `starter`: 200 applicants, 120 applications, 25 anomalies
   - `medium`: 2,000 applicants, 1,200 applications, 100 anomalies
   - `full`: 10,000 applicants, 6,000 applications, 300 anomalies (benchmarked at 27.32s)
6. **Multi-Format Persistence & Portability**: Generates real, validated CSV, JSON, and SQL seed files (273,645 records), with dual-database runtime support (PostgreSQL for containerized production, SQLite for immediate local execution).

---

## 2. Architecture & Component Blueprint

```
+-----------------------------------------------------------------------------------+
|                                  USER INTERFACES                                  |
|   React 18 + TypeScript + Tailwind CSS + Recharts Financial Intelligence Suite   |
|   - Executive View      - Risk Analytics      - Operations Funnel                 |
|   - Anomaly Lab         - Repayment Tracker   - Interactive Origination Simulator  |
+------------------------------------------+----------------------------------------+
                                           | HTTP / REST API (JSON) + Bearer RBAC
+------------------------------------------v----------------------------------------+
|                               FASTAPI BACKEND SERVICE                             |
|  /api/v1/auth          /api/v1/applications  /api/v1/applicants  /api/v1/analytics  |
|  /api/v1/decisions     /api/v1/repayments    /api/v1/anomalies   /api/v1/disbursements |
+-------------------+----------------------+--------------------+-------------------+
                    |                      |                    |
+-------------------v------+  +------------v-------+  +---------v-------------------+
|  FINANCIAL MATH ENGINE   |  | DECISION RULES     |  | ANOMALY DETECTOR ENGINE     |
|  - Existing & Total DTI  |  | - 10 Deterministic |  | - Invalid Term Auditor      |
|  - FOIR & Disposable Inc |  |   Rules with Tiered|  | - Reconciliation Verifier   |
|  - Reducing Balance EMI  |  |   Severity         |  | - Temporal Order Inspector  |
|  - Schedule Amortization |  | - Underwriter      |  | - Income Conflict Checker   |
|  - Penny-Rounding Adjust |  |   Override Workflow|  | - Duplicate Payout Detector |
|  - Zero-Interest Support |  | - Explainability   |  | - Zero Ground-Truth Access  |
+-------------------+------+  +------------+-------+  +---------+-------------------+
                    |                      |                    |
+-------------------v----------------------v--------------------v-------------------+
|                         RELATIONAL PERSISTENCE LAYER                              |
|           SQLAlchemy 2.0 ORM  |  SQLite (Local)  |  PostgreSQL (Docker)           |
|  [20 Relational Tables: Master Entities + Transactional Logs + Audit Ledgers]     |
+------------------------------------------+----------------------------------------+
                                           ^
                                           | Bulk Seed / ORM Pipeline
+------------------------------------------+----------------------------------------+
|                      SYNTHETIC DATA GENERATION PIPELINE                           |
|  Master Data Gen (Applicants, Products, Employment, Income, Facilities)           |
|  --> Grounded CreditProfile Derivation (On-Time%, Card Util%, Delinquencies)      |
|  --> Application Origination & Document Submissions                               |
|  --> Affordability Calculations & Explainable Decisions                           |
|  --> Repayment Amortization & Disbursement Eligibility Gate Check                 |
|  --> Anomaly Staging Layer (5 Mandatory Edge Cases)                               |
|  --> Ground Truth Splitter & Exporters (14 CSVs / JSON / SQL: 273,645 rows)       |
+-----------------------------------------------------------------------------------+
```

---

## 3. Core Entities & Cardinality Specifications

The relational schema implements 20 tables:

| Entity Index | Entity Name | Primary Key | Parent / FK | Cardinality & Lifecycle Notes |
|:---|:---|:---|:---|:---|
| **Entity A** | `Applicant` | `applicant_id` (`APP-2026-XXXXXX`) | None | 1:N with Employment, Income, Facilities, Credit Profiles, Applications |
| **Entity B** | `Employment` | `employment_id` (`EMP-2026-XXXXXX`) | `Applicant` (1:N) | Tracks career tenure, industry, job stability |
| **Entity C** | `IncomeRecord` | `income_record_id` (`INC-2026-XXXXXX`) | `Applicant`, `Employment` | Supports primary salary, secondary business, rental streams |
| **Entity D** | `CreditFacility` | `credit_facility_id` (`FAC-2026-XXXXXX`) | `Applicant` (1:N) | Existing debt obligations, outstanding balances, EMIs |
| **Entity D2**| `CreditProfile` | `credit_profile_id` (`CP-2026-XXXXXX`) | `Applicant` (1:N) | Formulaic bureau score (300-900), score bands, utilization |
| **Entity E** | `LoanProduct` | `product_id` (`PROD-001`..`004`) | None | 4 products: Personal, Auto, Home, Small Business |
| **Entity F** | `LoanApplication` | `application_id` (`LOAN-2026-XXXXXX`) | `Applicant`, `LoanProduct` | Core transactional anchor for all downstream workflows |
| **Entity G** | `Document` | `document_id` (`DOC-LOAN-...-XXX`) | `LoanApplication` (1:N) | Mandatory verification artifacts (PAN/KYC, Income, etc.) |
| **Entity H** | `AffordabilityCheck`| `affordability_check_id` (`AFF-LOAN-...`) | `LoanApplication` (1:N) | Deterministic DTI, FOIR, Disposable Income ledger |
| **Entity I** | `Decision` | `decision_id` (`DEC-LOAN-...-XX`) | `LoanApplication` (1:N) | Immutable decision history with rule evaluation traces |
| **Entity I2**| `DecisionOverrideHistory` | `override_id` (`OVR-...`) | `Decision`, `LoanApplication` | Underwriter manual override audit trail with mandatory reasons |
| **Entity J** | `RepaymentSchedule` | `schedule_id` (`SCH-LOAN-...-XXX`) | `LoanApplication` (1:N) | Monthly amortization schedule with penny rounding |
| **Entity K** | `Disbursement` | `disbursement_id` (`DISB-LOAN-...`) | `LoanApplication` (1:1) | Master disbursement record enforcing exactly one successful payout |

### Supporting Ledgers & Tables:
1. `ApplicationStatusHistory`: Chronological tracking of status transitions.
2. `DocumentVerificationHistory`: Audit trail of document status checks, verifier IDs, and rejection reasons.
3. `DecisionRule`: Rule catalog storing priority, conditions, threshold values, and rule versions.
4. `DecisionRuleExecution`: Granular execution logs recording inputs, boolean results, and trigger flags per application.
5. `DisbursementEvent`: Temporal state ledger (`ELIGIBILITY_CHECKED` -> `ELIGIBLE` -> `INITIATED` -> `DISBURSED` / `FAILED` / `REVERSED`).
6. `AuditLog`: System-wide immutable action log with actor, IP, timestamp, and diff payloads.
7. `DatasetGenerationRun`: Metadata ledger for reproducibility tracking (seed, counts, durations, configuration hash).
8. `GroundTruthAnomaly`: Segregated ground-truth register recording injected anomalies for detector evaluation.

---

## 4. Five Mandatory Anomaly Scenarios & Defense Blueprint

| Anomaly Code | Category Name | Injection Mechanism | Detection Logic | Expected Severity |
|:---|:---|:---|:---|:---|
| `ANOM-01` | `INVALID_TERM` | Term set to product max + 24 months | `term < min_term OR term > max_term` | `HIGH` |
| `ANOM-02` | `SCHEDULE_RECONCILIATION_FAILURE` | Perturb installment principal by ₹250 | `abs(sum(principal) - sanctioned) > 0.05` | `CRITICAL` |
| `ANOM-03` | `DECISION_BEFORE_CHECKS` | Backdate decision timestamp before checks | `decision_ts < assessment_ts` | `CRITICAL` |
| `ANOM-04` | `INCOME_SOURCE_CONFLICT` | Stated income inflated 350% vs payroll | `variance(stated, payroll) > 30%` | `MEDIUM` |
| `ANOM-05` | `DUPLICATE_DISBURSEMENT` | Staged duplicate successful payout | `count(disbursed) > 1` | `CRITICAL` |
