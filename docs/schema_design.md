# Relational Schema Design & Constraints Specification

## 1. Architectural Tenets

The persistence layer is engineered with enterprise relational guarantees:
1. **Primary Key Nomenclature**:
   - `applicants`: `APP-2026-XXXXXX`
   - `employments`: `EMP-2026-XXXXXX`
   - `income_records`: `INC-2026-XXXXXX`
   - `credit_facilities`: `FAC-2026-XXXXXX`
   - `credit_profiles`: `CP-2026-XXXXXX`
   - `loan_products`: `PROD-001` through `PROD-004`
   - `loan_applications`: `LOAN-2026-XXXXXX`
   - `documents`: `DOC-LOAN-2026-XXXXXX-XXX`
   - `affordability_checks`: `AFF-LOAN-2026-XXXXXX-XX`
   - `decisions`: `DEC-LOAN-2026-XXXXXX-XX`
   - `decision_override_history`: `OVR-DEC-YYYY-XXXXXX-timestamp`
   - `repayment_schedules`: `SCH-LOAN-2026-XXXXXX-XXX`
   - `disbursements`: `DISB-LOAN-2026-XXXXXX`
   - `ground_truth_anomalies`: `ANOM-2026-XXXXXX`

2. **Foreign Key Integrity**:
   - Master entities (`applicants`, `loan_products`) have `ON DELETE RESTRICT` to prevent accidental deletion of borrower records.
   - Transactional sub-records (`documents`, `affordability_checks`, `decisions`, `repayment_schedules`, `credit_profiles`, `decision_override_history`) cascade on delete.

3. **Disbursement Uniqueness**:
   - `disbursements.application_id` has a strict database `UNIQUE` constraint preventing duplicate payouts.

4. **Historical State Immutability**:
   - `application_status_history` logs state transitions chronologically.
   - `decisions` appends re-evaluations with an incremented `decision_sequence`.
   - `decision_override_history` records all human underwriter actions and notes.

---

## 2. Entity Constraints & Definitions

### `credit_profiles`
- `credit_profile_id` VARCHAR(32) PRIMARY KEY
- `applicant_id` VARCHAR(32) NOT NULL REFERENCES `applicants(applicant_id)` ON DELETE CASCADE
- `synthetic_credit_score` INTEGER NOT NULL CHECK (`synthetic_credit_score` BETWEEN 300 AND 900)
- `score_band` VARCHAR(24) NOT NULL CHECK (`score_band` IN ('EXCELLENT', 'VERY_GOOD', 'GOOD', 'FAIR', 'POOR'))
- `payment_history` DECIMAL(5,2) NOT NULL CHECK (`payment_history` BETWEEN 0.00 AND 100.00)
- `credit_utilization` DECIMAL(5,2) NOT NULL CHECK (`credit_utilization` >= 0.00)
- `active_facility_count` INTEGER NOT NULL CHECK (`active_facility_count` >= 0)
- `assessment_date` DATE NOT NULL
- `score_version` VARCHAR(16) NOT NULL
- `source_type` VARCHAR(32) NOT NULL DEFAULT 'SYNTHETIC_BUREAU_V1'

### `decision_override_history`
- `override_id` VARCHAR(48) PRIMARY KEY
- `decision_id` VARCHAR(48) NOT NULL REFERENCES `decisions(decision_id)` ON DELETE CASCADE
- `application_id` VARCHAR(32) NOT NULL REFERENCES `loan_applications(application_id)` ON DELETE CASCADE
- `previous_status` VARCHAR(24) NOT NULL
- `overridden_status` VARCHAR(24) NOT NULL CHECK (`overridden_status` IN ('APPROVED', 'REJECT'))
- `underwriter_id` VARCHAR(64) NOT NULL
- `override_reason` TEXT NOT NULL
- `overridden_at` TIMESTAMP NOT NULL

---

## 3. Anomaly Staging Layer vs. Operational Integrity

To reconcile the conflicting requirements of **strict relational constraints** (such as `UNIQUE` on `disbursements.application_id`) and **deliberate malformed anomaly scenarios** (such as duplicate disbursements):

1. **Operational Database**: Maintained 100% compliant with relational schemas, unique keys, and referential constraints.
2. **Anomaly Staging Layer (`data/anomalies/` and `staged_records`)**: Deliberately malformed or duplicate records are isolated in an exception audit queue.
3. **Dual Audit by Independent Detector**: The anomaly detector evaluates both the operational dataset and staged exception payloads without accessing ground-truth labels.
4. **Evaluation Isolation**: Precision, recall, and F1 metrics are calculated by an independent evaluation service comparing detector output to `data/ground_truth.csv`.
