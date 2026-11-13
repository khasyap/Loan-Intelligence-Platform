# Data Dictionary: Loan Origination, Risk Assessment & Decision Intelligence Platform

## Overview
This document specifies the complete schema, data types, validation constraints, foreign keys, and provenance (source vs. derived) for all ten core domain entities and supporting audit ledgers.

---

## 1. Core Domain Entities

### Entity A: Applicant (`applicants`)
Primary Key: `applicant_id`
Format: `APP-2026-XXXXXX` (Zero-padded 6-digit deterministic identifier)

| Field Name | Data Type | Required? | PK/FK | Allowed Values / Format | Unit | Source/Derived | Validation Rule / Constraints |
|:---|:---|:---|:---|:---|:---|:---|:---|
| `applicant_id` | VARCHAR(32) | Yes | PK | `^APP-2026-[0-9]{6}$` | N/A | Source | Primary Key, Unique, Immutable |
| `first_name` | VARCHAR(64) | Yes | - | Alpha characters | N/A | Source | Synthetic name; min length 2 |
| `last_name` | VARCHAR(64) | Yes | - | Alpha characters | N/A | Source | Synthetic surname; min length 2 |
| `date_of_birth` | DATE | Yes | - | YYYY-MM-DD | Date | Source | Age must be between 18 and 75 at application |
| `email` | VARCHAR(128) | Yes | - | RFC 5322 format | N/A | Source | Unique synthetic email address |
| `phone` | VARCHAR(20) | Yes | - | `^\+91[6-9][0-9]{9}$` | N/A | Source | 10-digit standard format |
| `city` | VARCHAR(64) | Yes | - | Valid synthetic city | N/A | Source | Indian / Target metro & tier-2 cities |
| `state` | VARCHAR(64) | Yes | - | Valid state/province | N/A | Source | Standard state name |
| `postal_code` | VARCHAR(12) | Yes | - | 6-digit numeric | N/A | Source | Valid postal code format |
| `applicant_status`| VARCHAR(24) | Yes | - | `ACTIVE`, `INACTIVE`, `BLOCKED` | Enum | Source | Default `ACTIVE` |
| `credit_score` | INTEGER | Yes | - | 300 to 900 | Score | Source | Synthetic credit bureau bureau score |
| `created_at` | TIMESTAMP | Yes | - | ISO-8601 UTC | Time | Source | Generation timestamp |

---

### Entity B: Employment (`employments`)
Primary Key: `employment_id`
Format: `EMP-2026-XXXXXX`

| Field Name | Data Type | Required? | PK/FK | Allowed Values / Format | Unit | Source/Derived | Validation Rule / Constraints |
|:---|:---|:---|:---|:---|:---|:---|:---|
| `employment_id` | VARCHAR(32) | Yes | PK | `^EMP-2026-[0-9]{6}$` | N/A | Source | Primary Key, Unique |
| `applicant_id` | VARCHAR(32) | Yes | FK | References `applicants.applicant_id` | N/A | Source | Non-null, indexed foreign key |
| `employer_name` | VARCHAR(128)| Yes | - | Synthetic business name | N/A | Source | Min length 3 |
| `employment_type`| VARCHAR(32) | Yes | - | `SALARIED`, `SELF_EMPLOYED`, `FREELANCE`, `UNEMPLOYED` | Enum | Source | Employment classification |
| `industry` | VARCHAR(64) | Yes | - | `IT`, `FINANCE`, `HEALTHCARE`, `MANUFACTURING`, `RETAIL`, `EDUCATION`, `SERVICES` | Enum | Source | Industry classification |
| `job_title` | VARCHAR(64) | Yes | - | Standard occupational titles | N/A | Source | Min length 2 |
| `employment_start_date`| DATE | Yes | - | Past date <= current date | Date | Source | Must be strictly before `employment_end_date` |
| `employment_end_date` | DATE | No | - | Null or date > start date | Date | Source | Null indicates current active employment |
| `monthly_salary`| DECIMAL(12,2)| Yes | - | >= 0.00 | INR | Source | Stored with 2 decimal precision |
| `employment_status` | VARCHAR(24) | Yes | - | `CURRENT`, `FORMER`, `TERMINATED` | Enum | Source | Matches `employment_end_date` nullability |
| `verification_status`| VARCHAR(24) | Yes | - | `PENDING`, `VERIFIED`, `REJECTED`, `INCONCLUSIVE` | Enum | Source | Default `PENDING` |

---

### Entity C: IncomeRecord (`income_records`)
Primary Key: `income_record_id`
Format: `INC-2026-XXXXXX`

| Field Name | Data Type | Required? | PK/FK | Allowed Values / Format | Unit | Source/Derived | Validation Rule / Constraints |
|:---|:---|:---|:---|:---|:---|:---|:---|
| `income_record_id`| VARCHAR(32) | Yes | PK | `^INC-2026-[0-9]{6}$` | N/A | Source | Primary Key, Unique |
| `applicant_id` | VARCHAR(32) | Yes | FK | References `applicants.applicant_id` | N/A | Source | Valid applicant reference |
| `employment_id`| VARCHAR(32) | No | FK | References `employments.employment_id` | N/A | Source | Nullable for secondary/investment income |
| `income_source`| VARCHAR(32) | Yes | - | `PRIMARY_SALARY`, `SECONDARY_JOB`, `BUSINESS_PROFITS`, `INVESTMENTS`, `RENTAL` | Enum | Source | Income source category |
| `gross_monthly_income`| DECIMAL(12,2)| Yes | - | >= 0.00 | INR | Source | Stated or verified gross income |
| `net_monthly_income` | DECIMAL(12,2)| Yes | - | <= gross_monthly_income | INR | Source | In-hand take home income |
| `additional_income` | DECIMAL(12,2)| Yes | - | >= 0.00 | INR | Source | Default 0.00 |
| `income_period_start`| DATE | Yes | - | YYYY-MM-DD | Date | Source | Assessment cycle start |
| `income_period_end` | DATE | Yes | - | >= income_period_start | Date | Source | Assessment cycle end |
| `verification_status`| VARCHAR(24) | Yes | - | `PENDING`, `VERIFIED`, `SUSPICIOUS`, `DISCREPANT` | Enum | Source | Compliance verification status |
| `source_reference` | VARCHAR(64) | Yes | - | Document / Tax / Payroll Ref | N/A | Source | e.g. Form 16, Bank statement UID |

---

### Entity D: CreditFacility (`credit_facilities`)
Primary Key: `credit_facility_id`
Format: `FAC-2026-XXXXXX`

| Field Name | Data Type | Required? | PK/FK | Allowed Values / Format | Unit | Source/Derived | Validation Rule / Constraints |
|:---|:---|:---|:---|:---|:---|:---|:---|
| `credit_facility_id`| VARCHAR(32)| Yes | PK | `^FAC-2026-[0-9]{6}$` | N/A | Source | Primary Key, Unique |
| `applicant_id` | VARCHAR(32) | Yes | FK | References `applicants.applicant_id` | N/A | Source | Valid applicant reference |
| `facility_type`| VARCHAR(32) | Yes | - | `CREDIT_CARD`, `PERSONAL_LOAN`, `AUTO_LOAN`, `MORTGAGE`, `EDUCATION_LOAN` | Enum | Source | Credit facility category |
| `lender_reference`| VARCHAR(64)| Yes | - | Synthetic financial institution | N/A | Source | Institution name |
| `credit_limit` | DECIMAL(12,2)| Yes | - | >= 0.00 | INR | Source | Sanctioned limit |
| `outstanding_balance`| DECIMAL(12,2)| Yes | - | >= 0.00 | INR | Source | Current debt balance |
| `monthly_emi` | DECIMAL(12,2)| Yes | - | >= 0.00 | INR | Source | Monthly servicing obligation |
| `interest_rate`| DECIMAL(5,2) | Yes | - | 0.00 to 40.00 | % p.a. | Source | Annual percentage rate |
| `payment_status`| VARCHAR(24) | Yes | - | `CURRENT`, `OVERDUE_30`, `OVERDUE_60`, `DEFAULTED`, `CLOSED` | Enum | Source | Bureau repayment behavior |
| `opened_date` | DATE | Yes | - | YYYY-MM-DD | Date | Source | Facility start date |
| `closed_date` | DATE | No | - | Null or date >= opened_date | Date | Source | Null if facility is active |

---

### Entity D2: CreditProfile (`credit_profiles`)
Primary Key: `credit_profile_id`
Format: `CP-2026-XXXXXX`

| Field Name | Data Type | Required? | PK/FK | Allowed Values / Format | Unit | Source/Derived | Validation Rule / Constraints |
|:---|:---|:---|:---|:---|:---|:---|:---|
| `credit_profile_id` | VARCHAR(32) | Yes | PK | `^CP-2026-[0-9]{6}$` | N/A | Derived | Primary Key, Unique, Immutable |
| `applicant_id` | VARCHAR(32) | Yes | FK | References `applicants.applicant_id` | N/A | Source | 1:N relationship; indexed foreign key |
| `synthetic_credit_score` | INTEGER | Yes | - | 300 to 900 | Score | Derived | Deterministically derived from payment history & utilization |
| `score_band` | VARCHAR(24) | Yes | - | `EXCELLENT`, `VERY_GOOD`, `GOOD`, `FAIR`, `POOR` | Enum | Derived | Stratified credit rating tier |
| `payment_history` | DECIMAL(5,2) | Yes | - | 0.00 to 100.00 | % | Derived | Percentage of historical installments paid on-time |
| `credit_utilization` | DECIMAL(5,2) | Yes | - | 0.00 to 100.00+ | % | Derived | Outstanding card balance / aggregate credit card limit |
| `active_facility_count` | INTEGER | Yes | - | >= 0 | Count | Derived | Number of open non-closed credit facilities |
| `assessment_date` | DATE | Yes | - | YYYY-MM-DD | Date | Source | Bureau snapshot date |
| `score_version` | VARCHAR(16) | Yes | - | `v1.0.0` | String | Source | Scoring algorithm version specification |
| `source_type` | VARCHAR(32) | Yes | - | `SYNTHETIC_BUREAU_V1` | Enum | Source | Grounded bureau origin indicator |


---

### Entity E: LoanProduct (`loan_products`)
Primary Key: `product_id`
Format: `PROD-001` through `PROD-004`

| Field Name | Data Type | Required? | PK/FK | Allowed Values / Format | Unit | Source/Derived | Validation Rule / Constraints |
|:---|:---|:---|:---|:---|:---|:---|:---|
| `product_id` | VARCHAR(16) | Yes | PK | `PROD-001` to `PROD-004` | N/A | Source | Unique product code |
| `product_name` | VARCHAR(64) | Yes | - | Product descriptive title | N/A | Source | e.g. "Express Personal Loan" |
| `product_type` | VARCHAR(32) | Yes | - | `PERSONAL`, `AUTO`, `HOME`, `BUSINESS` | Enum | Source | Lending segment |
| `min_principal` | DECIMAL(12,2)| Yes | - | > 0.00 | INR | Source | Minimum borrowing limit |
| `max_principal` | DECIMAL(12,2)| Yes | - | >= min_principal | INR | Source | Maximum borrowing limit |
| `min_term_months`| INTEGER | Yes | - | >= 1 | Months | Source | Minimum repayment tenure |
| `max_term_months`| INTEGER | Yes | - | >= min_term_months | Months | Source | Maximum repayment tenure |
| `annual_interest_rate`| DECIMAL(5,2)| Yes | - | 0.00 to 36.00 | % p.a. | Source | Base annual interest rate |
| `processing_fee_rate`| DECIMAL(5,2)| Yes | - | 0.00 to 5.00 | % | Source | Fee as percentage of principal |
| `maximum_dti` | DECIMAL(5,2) | Yes | - | 10.00 to 80.00 | % | Source | Maximum allowable Debt-to-Income |
| `maximum_foir` | DECIMAL(5,2) | Yes | - | 20.00 to 90.00 | % | Source | Maximum allowable Fixed Obligation |
| `minimum_credit_score`| INTEGER | Yes | - | 300 to 850 | Score | Source | Cutoff credit score for approval |
| `product_status`| VARCHAR(24) | Yes | - | `ACTIVE`, `INACTIVE`, `DISCONTINUED` | Enum | Source | Default `ACTIVE` |
| `effective_from`| DATE | Yes | - | YYYY-MM-DD | Date | Source | Policy start date |
| `effective_to` | DATE | No | - | Null or >= effective_from | Date | Source | Policy expiration date |

---

### Entity F: LoanApplication (`loan_applications`)
Primary Key: `application_id`
Format: `LOAN-2026-XXXXXX`

| Field Name | Data Type | Required? | PK/FK | Allowed Values / Format | Unit | Source/Derived | Validation Rule / Constraints |
|:---|:---|:---|:---|:---|:---|:---|:---|
| `application_id`| VARCHAR(32) | Yes | PK | `^LOAN-2026-[0-9]{6}$` | N/A | Source | Primary Key, Unique |
| `applicant_id` | VARCHAR(32) | Yes | FK | References `applicants.applicant_id` | N/A | Source | Non-null, indexed foreign key |
| `product_id` | VARCHAR(16) | Yes | FK | References `loan_products.product_id`| N/A | Source | Non-null, indexed foreign key |
| `requested_principal`| DECIMAL(12,2)| Yes| - | > 0.00 | INR | Source | Stated loan amount |
| `requested_term_months`| INTEGER | Yes | - | > 0 | Months | Source | Stated loan duration |
| `application_date`| TIMESTAMP | Yes | - | ISO-8601 UTC | Time | Source | Submission timestamp |
| `application_status`| VARCHAR(24)| Yes | - | `SUBMITTED`, `UNDER_REVIEW`, `PENDING_INFORMATION`, `APPROVED`, `REJECTED`, `MANUAL_REVIEW`, `DISBURSED`, `CANCELLED` | Enum | Source | Controlled state machine |
| `submission_channel`| VARCHAR(24)| Yes | - | `ONLINE_PORTAL`, `MOBILE_APP`, `BRANCH_AGENT`, `PARTNER_API` | Enum | Source | Originating channel |
| `application_version`| INTEGER | Yes | - | >= 1 | Int | Source | Incremented upon resubmission |

---

### Entity G: Document (`documents`)
Primary Key: `document_id`
Format: `DOC-LOAN-2026-XXXXXX-XXX`

| Field Name | Data Type | Required? | PK/FK | Allowed Values / Format | Unit | Source/Derived | Validation Rule / Constraints |
|:---|:---|:---|:---|:---|:---|:---|:---|
| `document_id` | VARCHAR(48) | Yes | PK | `^DOC-LOAN-2026-[0-9]{6}-[0-9]{3}$` | N/A | Source | Primary Key, Unique |
| `application_id`| VARCHAR(32) | Yes | FK | References `loan_applications.application_id` | N/A | Source | Indexed foreign key |
| `document_type` | VARCHAR(32) | Yes | - | `IDENTITY_PROOF`, `ADDRESS_PROOF`, `INCOME_PROOF`, `EMPLOYMENT_PROOF`, `BANK_STATEMENT` | Enum | Source | Checklist requirement item |
| `submission_status`| VARCHAR(24)| Yes | - | `NOT_SUBMITTED`, `SUBMITTED`, `UNDER_REVIEW`, `VERIFIED`, `REJECTED`, `EXPIRED` | Enum | Source | Submission lifecycle state |
| `verification_status`| VARCHAR(24)| Yes | - | `PENDING`, `VERIFIED`, `REJECTED`, `EXPIRED` | Enum | Derived | Result of manual or automated check |
| `submitted_at` | TIMESTAMP | No | - | Null or ISO-8601 | Time | Source | Timestamp when uploaded |
| `verified_at` | TIMESTAMP | No | - | Null or >= submitted_at | Time | Derived | Timestamp when processed |
| `expiry_date` | DATE | No | - | Null or Date | Date | Source | Expiry check for ID documents |
| `rejection_reason`| VARCHAR(255)| No | - | Text string or null | N/A | Derived | Mandatory if status == REJECTED |
| `document_reference`| VARCHAR(64)| Yes | - | Synthetic document hash/ID | N/A | Source | File path or external KYC token |

---

### Entity H: AffordabilityCheck (`affordability_checks`)
Primary Key: `affordability_check_id`
Format: `AFF-LOAN-2026-XXXXXX-XX`

| Field Name | Data Type | Required? | PK/FK | Allowed Values / Format | Unit | Source/Derived | Validation Rule / Constraints |
|:---|:---|:---|:---|:---|:---|:---|:---|
| `affordability_check_id`| VARCHAR(48)| Yes | PK | `^AFF-LOAN-2026-[0-9]{6}-[0-9]{2}$` | N/A | Source | Primary Key, Unique |
| `application_id`| VARCHAR(32) | Yes | FK | References `loan_applications.application_id` | N/A | Source | Indexed foreign key |
| `assessment_timestamp`| TIMESTAMP | Yes | - | ISO-8601 UTC | Time | Source | Must precede decision timestamp |
| `monthly_net_income` | DECIMAL(12,2)| Yes| - | >= 0.00 | INR | Derived | Aggregated verified net income |
| `existing_monthly_debt`| DECIMAL(12,2)| Yes| - | >= 0.00 | INR | Derived | Sum of active monthly EMIs |
| `proposed_monthly_emi` | DECIMAL(12,2)| Yes| - | >= 0.00 | INR | Derived | Reducing-balance EMI calculation |
| `debt_to_income_ratio` | DECIMAL(6,2)| Yes | - | >= 0.00 | % | Derived | `(existing_debt / monthly_gross) * 100` |
| `fixed_obligation_ratio`| DECIMAL(6,2)| Yes| - | >= 0.00 | % | Derived | `((existing_debt + proposed_emi) / net_income) * 100` |
| `disposable_income` | DECIMAL(12,2)| Yes | - | Any Real | INR | Derived | `net_income - existing_debt - proposed_emi` |
| `affordability_status` | VARCHAR(24) | Yes | - | `PASSED`, `BORDERLINE`, `FAILED` | Enum | Derived | Based on product DTI/FOIR limits |
| `rule_version` | VARCHAR(16) | Yes | - | e.g. `v1.0.0` | N/A | Source | Rule policy configuration version |
| `calculation_details` | TEXT | Yes | - | JSON serialized breakdown | N/A | Derived | Complete mathematical audit trace |

---

### Entity I: Decision (`decisions`)
Primary Key: `decision_id`
Format: `DEC-LOAN-2026-XXXXXX-XX`

| Field Name | Data Type | Required? | PK/FK | Allowed Values / Format | Unit | Source/Derived | Validation Rule / Constraints |
|:---|:---|:---|:---|:---|:---|:---|:---|
| `decision_id` | VARCHAR(48) | Yes | PK | `^DEC-LOAN-2026-[0-9]{6}-[0-9]{2}$` | N/A | Source | Primary Key, Unique |
| `application_id`| VARCHAR(32) | Yes | FK | References `loan_applications.application_id` | N/A | Source | Indexed foreign key |
| `decision_sequence`| INTEGER | Yes | - | >= 1 | Int | Source | Sequence number (1 for initial, 2 for re-evaluation) |
| `decision_status`| VARCHAR(24)| Yes | - | `APPROVED`, `REJECTED`, `MANUAL_REVIEW`, `PENDING_INFORMATION` | Enum | Derived | Engine output |
| `decision_timestamp`| TIMESTAMP | Yes | - | ISO-8601 UTC | Time | Source | Must be strictly >= assessment timestamp |
| `decision_reason_code`| VARCHAR(32)| Yes | - | Standardized code | N/A | Derived | e.g. `RULE_PASS_CLEAN`, `REJ_DTI_EXCEEDED` |
| `decision_explanation`| TEXT | Yes | - | Human-readable explanation | N/A | Derived | Transparent reason for customer/ops |
| `risk_score` | INTEGER | Yes | - | 300 to 900 | Score | Derived | Normalized composite risk score |
| `rules_triggered`| TEXT | Yes | - | JSON array of triggered rule IDs | N/A | Derived | e.g. `["RULE_03", "RULE_06"]` |
| `reviewer_id` | VARCHAR(32) | No | - | System or agent identifier | N/A | Source | `SYSTEM_RULES_ENGINE` or Reviewer ID |
| `rule_version` | VARCHAR(16) | Yes | - | e.g. `v1.0.0` | N/A | Source | Rule version applied |

---

### Entity J: RepaymentSchedule (`repayment_schedules`)
Primary Key: `schedule_id`
Format: `SCH-LOAN-2026-XXXXXX-XXX`

| Field Name | Data Type | Required? | PK/FK | Allowed Values / Format | Unit | Source/Derived | Validation Rule / Constraints |
|:---|:---|:---|:---|:---|:---|:---|:---|
| `schedule_id` | VARCHAR(48) | Yes | PK | `^SCH-LOAN-2026-[0-9]{6}-[0-9]{3}$` | N/A | Source | Primary Key, Unique |
| `application_id`| VARCHAR(32) | Yes | FK | References `loan_applications.application_id` | N/A | Source | Indexed foreign key |
| `installment_number`| INTEGER | Yes | - | 1 to `requested_term_months` | Int | Source | Contiguous sequence starting from 1 |
| `due_date` | DATE | Yes | - | YYYY-MM-DD | Date | Derived | Due date on monthly cycle |
| `opening_balance`| DECIMAL(12,2)| Yes | - | >= 0.00 | INR | Derived | Prior closing balance (or Disbursed Principal) |
| `principal_amount`| DECIMAL(12,2)| Yes| - | >= 0.00 | INR | Derived | Amortized principal portion |
| `interest_amount` | DECIMAL(12,2)| Yes | - | >= 0.00 | INR | Derived | Monthly interest portion |
| `installment_amount`| DECIMAL(12,2)| Yes| - | = principal + interest | INR | Derived | Total monthly repayment amount |
| `closing_balance`| DECIMAL(12,2)| Yes | - | >= 0.00 (Final = 0.00) | INR | Derived | `opening_balance - principal_amount` |
| `payment_status`| VARCHAR(24) | Yes | - | `SCHEDULED`, `PAID`, `OVERDUE`, `PARTIALLY_PAID` | Enum | Source | Default `SCHEDULED` |
| `paid_amount` | DECIMAL(12,2)| Yes | - | >= 0.00 | INR | Source | Default 0.00 |
| `paid_date` | DATE | No | - | Null or Date | Date | Source | Date when payment cleared |

---

## 2. Supporting Ledgers & Audit Tables

### Table: `application_status_history`
- `history_id` (PK, VARCHAR(48)): Unique ledger identifier.
- `application_id` (FK, VARCHAR(32)): References `loan_applications.application_id`.
- `previous_status` (VARCHAR(24)): State before transition.
- `new_status` (VARCHAR(24)): State after transition.
- `changed_at` (TIMESTAMP): Transition timestamp.
- `changed_by` (VARCHAR(64)): User, system service, or agent ID.
- `notes` (TEXT): Rationale for manual or automated state transition.

### Table: `document_verification_history`
- `history_id` (PK, VARCHAR(48)): Unique log identifier.
- `document_id` (FK, VARCHAR(48)): References `documents.document_id`.
- `previous_status` (VARCHAR(24)): Verification state prior to event.
- `new_status` (VARCHAR(24)): Updated verification state.
- `verified_at` (TIMESTAMP): Verification timestamp.
- `verified_by` (VARCHAR(64)): Reviewer or OCR service ID.
- `reason` (VARCHAR(255)): Verification notes or rejection cause.

### Table: `decision_rules`
- `rule_id` (PK, VARCHAR(32)): Unique identifier (e.g. `RULE_01`).
- `rule_name` (VARCHAR(64)): Descriptive title.
- `rule_version` (VARCHAR(16)): Policy version tag.
- `priority` (INTEGER): Execution evaluation order (1 = highest).
- `severity` (VARCHAR(16)): `HARD_FAIL` (Reject), `SOFT_FAIL` (Manual Review), `INFO`.
- `description` (TEXT): Business definition and logic.
- `is_active` (BOOLEAN): Toggle for active evaluation.

### Table: `decision_rule_executions`
- `execution_id` (PK, VARCHAR(48)): Unique execution trace identifier.
- `decision_id` (FK, VARCHAR(48)): References `decisions.decision_id`.
- `rule_id` (VARCHAR(32)): Evaluated rule identifier.
- `rule_version` (VARCHAR(16)): Version of the evaluated rule.
- `evaluated_values` (TEXT): JSON snapshot of applicant parameters evaluated.
- `is_triggered` (BOOLEAN): True if the rule condition matched.
- `triggered_action` (VARCHAR(24)): Proposed action (`APPROVE`, `REJECT`, `MANUAL_REVIEW`).

### Table: `decision_override_history`
- `override_id` (PK, VARCHAR(48)): Format `OVR-DEC-YYYY-XXXXXX-timestamp`.
- `decision_id` (FK, VARCHAR(48)): References `decisions.decision_id`.
- `application_id` (FK, VARCHAR(32)): References `loan_applications.application_id`.
- `previous_status` (VARCHAR(24)): Decision state prior to underwriter action (e.g. `MANUAL_REVIEW`).
- `overridden_status` (VARCHAR(24)): Overridden final state (`APPROVED` or `REJECT`).
- `underwriter_id` (VARCHAR(64)): Identifier of the human credit officer executing the override.
- `override_reason` (TEXT): Mandatory justifying narrative for audit and regulatory compliance.
- `overridden_at` (TIMESTAMP): UTC timestamp when override was logged.


### Table: `disbursements`
- `disbursement_id` (PK, VARCHAR(48)): Format `DISB-LOAN-2026-XXXXXX`.
- `application_id` (FK, VARCHAR(32), UNIQUE): References `loan_applications.application_id`.
- `disbursed_amount` (DECIMAL(12,2)): Sanctioned net disbursed principal.
- `disbursement_date` (DATE): Payment release date.
- `disbursement_status` (VARCHAR(24)): `PENDING`, `DISBURSED`, `FAILED`, `REVERSED`.
- `bank_reference` (VARCHAR(64)): Transaction reference number.
- `created_at` (TIMESTAMP): Record creation timestamp.

### Table: `disbursement_events`
- `event_id` (PK, VARCHAR(48)): Format `DISB-EVT-XXXXXX`.
- `disbursement_id` (FK, VARCHAR(48)): References `disbursements.disbursement_id`.
- `event_type` (VARCHAR(32)): `ELIGIBILITY_CHECKED`, `ELIGIBLE`, `DISBURSEMENT_INITIATED`, `DISBURSED`, `FAILED`, `REVERSED`.
- `event_timestamp` (TIMESTAMP): Event recording time.
- `event_payload` (TEXT): JSON serialized event metadata.

### Table: `audit_logs`
- `log_id` (PK, VARCHAR(48)): Format `AUDIT-XXXXXX`.
- `entity_name` (VARCHAR(64)): Target domain entity table name.
- `record_id` (VARCHAR(64)): Primary key of the affected record.
- `action` (VARCHAR(16)): `INSERT`, `UPDATE`, `DELETE`, `STATUS_CHANGE`.
- `actor_id` (VARCHAR(64)): User, subagent, or system process identifier.
- `timestamp` (TIMESTAMP): Log entry creation time.
- `diff` (TEXT): JSON serialized previous and new state values.

### Table: `dataset_generation_runs`
- `run_id` (PK, VARCHAR(48)): Execution ID.
- `seed` (BIGINT): Pseudorandom seed utilized (`20261022`).
- `profile` (VARCHAR(16)): Mode (`starter`, `medium`, `full`).
- `applicant_count` (INTEGER): Total applicants synthesized.
- `application_count` (INTEGER): Total loan applications synthesized.
- `anomaly_count` (INTEGER): Total anomalies injected.
- `config_hash` (VARCHAR(64)): SHA-256 hash of `generation.yaml`.
- `started_at` (TIMESTAMP): Execution start timestamp.
- `completed_at` (TIMESTAMP): Execution finish timestamp.

### Table: `ground_truth_anomalies` (Isolated Ground Truth)
- `anomaly_id` (PK, VARCHAR(32)): Format `ANOM-2026-XXXXXX`.
- `entity_name` (VARCHAR(64)): Affected table name.
- `record_id` (VARCHAR(64)): Target record identifier.
- `issue_type` (VARCHAR(32)): `INVALID_TERM`, `SCHEDULE_RECONCILIATION_FAILURE`, `DECISION_BEFORE_CHECKS`, `INCOME_SOURCE_CONFLICT`, `DUPLICATE_DISBURSEMENT`.
- `expected_label` (VARCHAR(32)): Ground truth class (`ANOMALY`).
- `severity` (VARCHAR(16)): `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
- `expected_detection` (BOOLEAN): True.
- `explanation` (TEXT): Root cause description for anomaly validation.
- `injection_timestamp` (TIMESTAMP): When the anomaly was injected.

