-- =============================================================================
-- Loan Intelligence Platform: Master Database Schema
-- Standard ANSI SQL / PostgreSQL & SQLite compatible
-- =============================================================================

-- Clean up existing tables in reverse dependency order
DROP TABLE IF EXISTS ground_truth_anomalies;
DROP TABLE IF EXISTS dataset_generation_runs;
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS disbursement_events;
DROP TABLE IF EXISTS disbursements;
DROP TABLE IF EXISTS decision_override_history;
DROP TABLE IF EXISTS decision_rule_executions;
DROP TABLE IF EXISTS decision_rules;
DROP TABLE IF EXISTS document_verification_history;
DROP TABLE IF EXISTS application_status_history;
DROP TABLE IF EXISTS repayment_schedules;
DROP TABLE IF EXISTS decisions;
DROP TABLE IF EXISTS affordability_checks;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS loan_applications;
DROP TABLE IF EXISTS loan_products;
DROP TABLE IF EXISTS credit_profiles;
DROP TABLE IF EXISTS credit_facilities;
DROP TABLE IF EXISTS income_records;
DROP TABLE IF EXISTS employments;
DROP TABLE IF EXISTS applicants;

-- -----------------------------------------------------------------------------
-- Entity A: Applicants
-- -----------------------------------------------------------------------------
CREATE TABLE applicants (
    applicant_id VARCHAR(32) PRIMARY KEY,
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64) NOT NULL,
    date_of_birth DATE NOT NULL,
    email VARCHAR(128) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    city VARCHAR(64) NOT NULL,
    state VARCHAR(64) NOT NULL,
    postal_code VARCHAR(12) NOT NULL,
    applicant_status VARCHAR(24) NOT NULL DEFAULT 'ACTIVE',
    credit_score INTEGER NOT NULL CHECK (credit_score BETWEEN 300 AND 900),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_applicant_email ON applicants(email);
CREATE INDEX idx_applicant_status ON applicants(applicant_status);

-- -----------------------------------------------------------------------------
-- Entity B: Employments
-- -----------------------------------------------------------------------------
CREATE TABLE employments (
    employment_id VARCHAR(32) PRIMARY KEY,
    applicant_id VARCHAR(32) NOT NULL REFERENCES applicants(applicant_id) ON DELETE RESTRICT,
    employer_name VARCHAR(128) NOT NULL,
    employment_type VARCHAR(32) NOT NULL,
    industry VARCHAR(64) NOT NULL,
    job_title VARCHAR(64) NOT NULL,
    employment_start_date DATE NOT NULL,
    employment_end_date DATE,
    monthly_salary DECIMAL(12,2) NOT NULL CHECK (monthly_salary >= 0),
    employment_status VARCHAR(24) NOT NULL DEFAULT 'CURRENT',
    verification_status VARCHAR(24) NOT NULL DEFAULT 'PENDING'
);
CREATE INDEX idx_employment_applicant ON employments(applicant_id);

-- -----------------------------------------------------------------------------
-- Entity C: Income Records
-- -----------------------------------------------------------------------------
CREATE TABLE income_records (
    income_record_id VARCHAR(32) PRIMARY KEY,
    applicant_id VARCHAR(32) NOT NULL REFERENCES applicants(applicant_id) ON DELETE RESTRICT,
    employment_id VARCHAR(32) REFERENCES employments(employment_id) ON DELETE SET NULL,
    income_source VARCHAR(32) NOT NULL,
    gross_monthly_income DECIMAL(12,2) NOT NULL CHECK (gross_monthly_income >= 0),
    net_monthly_income DECIMAL(12,2) NOT NULL CHECK (net_monthly_income >= 0),
    additional_income DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    income_period_start DATE NOT NULL,
    income_period_end DATE NOT NULL,
    verification_status VARCHAR(24) NOT NULL DEFAULT 'PENDING',
    source_reference VARCHAR(64) NOT NULL
);
CREATE INDEX idx_income_applicant ON income_records(applicant_id);

-- -----------------------------------------------------------------------------
-- Entity D: Credit Facilities
-- -----------------------------------------------------------------------------
CREATE TABLE credit_facilities (
    credit_facility_id VARCHAR(32) PRIMARY KEY,
    applicant_id VARCHAR(32) NOT NULL REFERENCES applicants(applicant_id) ON DELETE RESTRICT,
    facility_type VARCHAR(32) NOT NULL,
    lender_reference VARCHAR(64) NOT NULL,
    credit_limit DECIMAL(12,2) NOT NULL CHECK (credit_limit >= 0),
    outstanding_balance DECIMAL(12,2) NOT NULL CHECK (outstanding_balance >= 0),
    monthly_emi DECIMAL(12,2) NOT NULL CHECK (monthly_emi >= 0),
    interest_rate DECIMAL(5,2) NOT NULL,
    payment_status VARCHAR(24) NOT NULL DEFAULT 'CURRENT',
    opened_date DATE NOT NULL,
    closed_date DATE
);
CREATE INDEX idx_credit_applicant ON credit_facilities(applicant_id);

-- -----------------------------------------------------------------------------
-- Supporting Entity: Credit Profiles (Historical & Behavioral Bureau Scores)
-- -----------------------------------------------------------------------------
CREATE TABLE credit_profiles (
    credit_profile_id VARCHAR(32) PRIMARY KEY,
    applicant_id VARCHAR(32) NOT NULL REFERENCES applicants(applicant_id) ON DELETE RESTRICT,
    synthetic_credit_score INTEGER NOT NULL CHECK (synthetic_credit_score BETWEEN 300 AND 900),
    score_band VARCHAR(24) NOT NULL,
    payment_history DECIMAL(5,2) NOT NULL,
    credit_utilization DECIMAL(5,2) NOT NULL,
    active_facility_count INTEGER NOT NULL DEFAULT 0,
    assessment_date DATE NOT NULL,
    score_version VARCHAR(16) NOT NULL DEFAULT 'v1.0.0',
    source_type VARCHAR(32) NOT NULL DEFAULT 'SYNTHETIC_BUREAU_V1',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_credit_profile_applicant ON credit_profiles(applicant_id);

-- -----------------------------------------------------------------------------
-- Entity E: Loan Products
-- -----------------------------------------------------------------------------
CREATE TABLE loan_products (
    product_id VARCHAR(16) PRIMARY KEY,
    product_name VARCHAR(64) NOT NULL,
    product_type VARCHAR(32) NOT NULL,
    min_principal DECIMAL(12,2) NOT NULL,
    max_principal DECIMAL(12,2) NOT NULL,
    min_term_months INTEGER NOT NULL,
    max_term_months INTEGER NOT NULL,
    annual_interest_rate DECIMAL(5,2) NOT NULL,
    processing_fee_rate DECIMAL(5,2) NOT NULL,
    maximum_dti DECIMAL(5,2) NOT NULL,
    maximum_foir DECIMAL(5,2) NOT NULL,
    minimum_credit_score INTEGER NOT NULL,
    product_status VARCHAR(24) NOT NULL DEFAULT 'ACTIVE',
    effective_from DATE NOT NULL,
    effective_to DATE
);

-- -----------------------------------------------------------------------------
-- Entity F: Loan Applications
-- -----------------------------------------------------------------------------
CREATE TABLE loan_applications (
    application_id VARCHAR(32) PRIMARY KEY,
    applicant_id VARCHAR(32) NOT NULL REFERENCES applicants(applicant_id) ON DELETE RESTRICT,
    product_id VARCHAR(16) NOT NULL REFERENCES loan_products(product_id) ON DELETE RESTRICT,
    requested_principal DECIMAL(12,2) NOT NULL CHECK (requested_principal > 0),
    requested_term_months INTEGER NOT NULL CHECK (requested_term_months > 0),
    application_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    application_status VARCHAR(24) NOT NULL DEFAULT 'SUBMITTED',
    submission_channel VARCHAR(24) NOT NULL DEFAULT 'ONLINE_PORTAL',
    application_version INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX idx_app_applicant ON loan_applications(applicant_id);
CREATE INDEX idx_app_product ON loan_applications(product_id);
CREATE INDEX idx_app_status ON loan_applications(application_status);

-- -----------------------------------------------------------------------------
-- Entity G: Documents
-- -----------------------------------------------------------------------------
CREATE TABLE documents (
    document_id VARCHAR(48) PRIMARY KEY,
    application_id VARCHAR(32) NOT NULL REFERENCES loan_applications(application_id) ON DELETE CASCADE,
    document_type VARCHAR(32) NOT NULL,
    submission_status VARCHAR(24) NOT NULL DEFAULT 'SUBMITTED',
    verification_status VARCHAR(24) NOT NULL DEFAULT 'PENDING',
    submitted_at TIMESTAMP,
    verified_at TIMESTAMP,
    expiry_date DATE,
    rejection_reason VARCHAR(255),
    document_reference VARCHAR(64) NOT NULL
);
CREATE INDEX idx_doc_app ON documents(application_id);

-- -----------------------------------------------------------------------------
-- Entity H: Affordability Checks
-- -----------------------------------------------------------------------------
CREATE TABLE affordability_checks (
    affordability_check_id VARCHAR(48) PRIMARY KEY,
    application_id VARCHAR(32) NOT NULL REFERENCES loan_applications(application_id) ON DELETE CASCADE,
    assessment_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    monthly_net_income DECIMAL(12,2) NOT NULL,
    existing_monthly_debt DECIMAL(12,2) NOT NULL,
    proposed_monthly_emi DECIMAL(12,2) NOT NULL,
    debt_to_income_ratio DECIMAL(6,2) NOT NULL,
    fixed_obligation_ratio DECIMAL(6,2) NOT NULL,
    disposable_income DECIMAL(12,2) NOT NULL,
    affordability_status VARCHAR(24) NOT NULL,
    rule_version VARCHAR(16) NOT NULL DEFAULT 'v1.0.0',
    calculation_details TEXT NOT NULL
);
CREATE INDEX idx_afford_app ON affordability_checks(application_id);

-- -----------------------------------------------------------------------------
-- Entity I: Decisions
-- -----------------------------------------------------------------------------
CREATE TABLE decisions (
    decision_id VARCHAR(48) PRIMARY KEY,
    application_id VARCHAR(32) NOT NULL REFERENCES loan_applications(application_id) ON DELETE CASCADE,
    decision_sequence INTEGER NOT NULL DEFAULT 1,
    decision_status VARCHAR(24) NOT NULL,
    decision_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    decision_reason_code VARCHAR(32) NOT NULL,
    decision_explanation TEXT NOT NULL,
    risk_score INTEGER NOT NULL,
    rules_triggered TEXT NOT NULL,
    reviewer_id VARCHAR(32),
    rule_version VARCHAR(16) NOT NULL DEFAULT 'v1.0.0'
);
CREATE INDEX idx_decision_app ON decisions(application_id);

-- -----------------------------------------------------------------------------
-- Entity J: Repayment Schedules
-- -----------------------------------------------------------------------------
CREATE TABLE repayment_schedules (
    schedule_id VARCHAR(48) PRIMARY KEY,
    application_id VARCHAR(32) NOT NULL REFERENCES loan_applications(application_id) ON DELETE CASCADE,
    installment_number INTEGER NOT NULL,
    due_date DATE NOT NULL,
    opening_balance DECIMAL(12,2) NOT NULL,
    principal_amount DECIMAL(12,2) NOT NULL,
    interest_amount DECIMAL(12,2) NOT NULL,
    installment_amount DECIMAL(12,2) NOT NULL,
    closing_balance DECIMAL(12,2) NOT NULL,
    payment_status VARCHAR(24) NOT NULL DEFAULT 'SCHEDULED',
    paid_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    paid_date DATE,
    CONSTRAINT uq_app_installment UNIQUE (application_id, installment_number)
);
CREATE INDEX idx_sched_app ON repayment_schedules(application_id);

-- -----------------------------------------------------------------------------
-- Supporting Ledgers
-- -----------------------------------------------------------------------------
CREATE TABLE application_status_history (
    history_id VARCHAR(48) PRIMARY KEY,
    application_id VARCHAR(32) NOT NULL REFERENCES loan_applications(application_id) ON DELETE CASCADE,
    previous_status VARCHAR(24),
    new_status VARCHAR(24) NOT NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(64) NOT NULL,
    notes TEXT
);
CREATE INDEX idx_status_hist_app ON application_status_history(application_id);

CREATE TABLE document_verification_history (
    history_id VARCHAR(48) PRIMARY KEY,
    document_id VARCHAR(48) NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    previous_status VARCHAR(24),
    new_status VARCHAR(24) NOT NULL,
    verified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verified_by VARCHAR(64) NOT NULL,
    reason VARCHAR(255)
);

CREATE TABLE decision_rules (
    rule_id VARCHAR(32) PRIMARY KEY,
    rule_name VARCHAR(64) NOT NULL,
    rule_version VARCHAR(16) NOT NULL DEFAULT 'v1.0.0',
    priority INTEGER NOT NULL,
    severity VARCHAR(16) NOT NULL,
    description TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE decision_rule_executions (
    execution_id VARCHAR(48) PRIMARY KEY,
    decision_id VARCHAR(48) NOT NULL REFERENCES decisions(decision_id) ON DELETE CASCADE,
    rule_id VARCHAR(32) NOT NULL,
    rule_version VARCHAR(16) NOT NULL DEFAULT 'v1.0.0',
    evaluated_values TEXT NOT NULL,
    is_triggered BOOLEAN NOT NULL,
    triggered_action VARCHAR(24)
);
CREATE INDEX idx_rule_exec_decision ON decision_rule_executions(decision_id);

CREATE TABLE decision_override_history (
    override_id VARCHAR(48) PRIMARY KEY,
    decision_id VARCHAR(48) NOT NULL REFERENCES decisions(decision_id) ON DELETE CASCADE,
    application_id VARCHAR(32) NOT NULL REFERENCES loan_applications(application_id) ON DELETE CASCADE,
    previous_status VARCHAR(24) NOT NULL,
    overridden_status VARCHAR(24) NOT NULL,
    underwriter_id VARCHAR(64) NOT NULL,
    override_reason TEXT NOT NULL,
    overridden_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_override_app ON decision_override_history(application_id);

CREATE TABLE disbursements (
    disbursement_id VARCHAR(48) PRIMARY KEY,
    application_id VARCHAR(32) NOT NULL UNIQUE REFERENCES loan_applications(application_id) ON DELETE RESTRICT,
    disbursed_amount DECIMAL(12,2) NOT NULL,
    disbursement_date DATE NOT NULL,
    disbursement_status VARCHAR(24) NOT NULL DEFAULT 'DISBURSED',
    bank_reference VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_disb_app ON disbursements(application_id);

CREATE TABLE disbursement_events (
    event_id VARCHAR(48) PRIMARY KEY,
    disbursement_id VARCHAR(48) NOT NULL REFERENCES disbursements(disbursement_id) ON DELETE CASCADE,
    event_type VARCHAR(32) NOT NULL,
    event_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_payload TEXT
);

CREATE TABLE audit_logs (
    log_id VARCHAR(48) PRIMARY KEY,
    entity_name VARCHAR(64) NOT NULL,
    record_id VARCHAR(64) NOT NULL,
    action VARCHAR(16) NOT NULL,
    actor_id VARCHAR(64) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    diff TEXT
);
CREATE INDEX idx_audit_entity ON audit_logs(entity_name, record_id);

CREATE TABLE dataset_generation_runs (
    run_id VARCHAR(48) PRIMARY KEY,
    seed INTEGER NOT NULL,
    profile VARCHAR(16) NOT NULL,
    applicant_count INTEGER NOT NULL,
    application_count INTEGER NOT NULL,
    anomaly_count INTEGER NOT NULL,
    config_hash VARCHAR(64) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP NOT NULL
);

CREATE TABLE ground_truth_anomalies (
    anomaly_id VARCHAR(32) PRIMARY KEY,
    entity_name VARCHAR(64) NOT NULL,
    record_id VARCHAR(64) NOT NULL,
    issue_type VARCHAR(32) NOT NULL,
    expected_label VARCHAR(32) NOT NULL DEFAULT 'ANOMALY',
    severity VARCHAR(16) NOT NULL,
    expected_detection BOOLEAN NOT NULL DEFAULT TRUE,
    expected_decision VARCHAR(24),
    explanation TEXT NOT NULL,
    injection_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

