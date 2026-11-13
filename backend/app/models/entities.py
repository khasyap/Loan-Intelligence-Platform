import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, String, Integer, Numeric, Date, DateTime, Boolean, Text, ForeignKey,
    UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from backend.app.database.connection import Base

# ==============================================================================
# ENTITY A: Applicant
# ==============================================================================
class Applicant(Base):
    __tablename__ = "applicants"

    applicant_id = Column(String(32), primary_key=True)  # APP-2026-XXXXXX
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    email = Column(String(128), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    city = Column(String(64), nullable=False)
    state = Column(String(64), nullable=False)
    postal_code = Column(String(12), nullable=False)
    applicant_status = Column(String(24), nullable=False, default="ACTIVE")
    credit_score = Column(Integer, nullable=False)  # 300 to 900
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    # Relationships
    employments = relationship("Employment", back_populates="applicant", cascade="all, delete-orphan")
    income_records = relationship("IncomeRecord", back_populates="applicant", cascade="all, delete-orphan")
    credit_facilities = relationship("CreditFacility", back_populates="applicant", cascade="all, delete-orphan")
    credit_profiles = relationship("CreditProfile", back_populates="applicant", cascade="all, delete-orphan")
    loan_applications = relationship("LoanApplication", back_populates="applicant", cascade="all, delete-orphan")


# ==============================================================================
# ENTITY B: Employment
# ==============================================================================
class Employment(Base):
    __tablename__ = "employments"

    employment_id = Column(String(32), primary_key=True)  # EMP-2026-XXXXXX
    applicant_id = Column(String(32), ForeignKey("applicants.applicant_id", ondelete="RESTRICT"), nullable=False, index=True)
    employer_name = Column(String(128), nullable=False)
    employment_type = Column(String(32), nullable=False)  # SALARIED, SELF_EMPLOYED, etc.
    industry = Column(String(64), nullable=False)
    job_title = Column(String(64), nullable=False)
    employment_start_date = Column(Date, nullable=False)
    employment_end_date = Column(Date, nullable=True)
    monthly_salary = Column(Numeric(12, 2), nullable=False)
    employment_status = Column(String(24), nullable=False, default="CURRENT")
    verification_status = Column(String(24), nullable=False, default="PENDING")

    applicant = relationship("Applicant", back_populates="employments")
    income_records = relationship("IncomeRecord", back_populates="employment")


# ==============================================================================
# ENTITY C: IncomeRecord
# ==============================================================================
class IncomeRecord(Base):
    __tablename__ = "income_records"

    income_record_id = Column(String(32), primary_key=True)  # INC-2026-XXXXXX
    applicant_id = Column(String(32), ForeignKey("applicants.applicant_id", ondelete="RESTRICT"), nullable=False, index=True)
    employment_id = Column(String(32), ForeignKey("employments.employment_id", ondelete="SET NULL"), nullable=True)
    income_source = Column(String(32), nullable=False)  # PRIMARY_SALARY, BUSINESS_PROFITS, etc.
    gross_monthly_income = Column(Numeric(12, 2), nullable=False)
    net_monthly_income = Column(Numeric(12, 2), nullable=False)
    additional_income = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    income_period_start = Column(Date, nullable=False)
    income_period_end = Column(Date, nullable=False)
    verification_status = Column(String(24), nullable=False, default="PENDING")
    source_reference = Column(String(64), nullable=False)

    applicant = relationship("Applicant", back_populates="income_records")
    employment = relationship("Employment", back_populates="income_records")


# ==============================================================================
# ENTITY D: CreditFacility
# ==============================================================================
class CreditFacility(Base):
    __tablename__ = "credit_facilities"

    credit_facility_id = Column(String(32), primary_key=True)  # FAC-2026-XXXXXX
    applicant_id = Column(String(32), ForeignKey("applicants.applicant_id", ondelete="RESTRICT"), nullable=False, index=True)
    facility_type = Column(String(32), nullable=False)  # CREDIT_CARD, AUTO_LOAN, etc.
    lender_reference = Column(String(64), nullable=False)
    credit_limit = Column(Numeric(12, 2), nullable=False)
    outstanding_balance = Column(Numeric(12, 2), nullable=False)
    monthly_emi = Column(Numeric(12, 2), nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=False)
    payment_status = Column(String(24), nullable=False, default="CURRENT")
    opened_date = Column(Date, nullable=False)
    closed_date = Column(Date, nullable=True)

    applicant = relationship("Applicant", back_populates="credit_facilities")


# ==============================================================================
# ENTITY D2: CreditProfile (Historical Credit Profile & Behavioral Derivation)
# ==============================================================================
class CreditProfile(Base):
    __tablename__ = "credit_profiles"

    credit_profile_id = Column(String(32), primary_key=True)  # CP-2026-XXXXXX
    applicant_id = Column(String(32), ForeignKey("applicants.applicant_id", ondelete="RESTRICT"), nullable=False, index=True)
    synthetic_credit_score = Column(Integer, nullable=False)  # 300 to 900
    score_band = Column(String(24), nullable=False)  # EXCELLENT, VERY_GOOD, GOOD, FAIR, POOR
    payment_history = Column(Numeric(5, 2), nullable=False)  # On-time payment percentage (e.g. 98.50%)
    credit_utilization = Column(Numeric(5, 2), nullable=False)  # Balance/Limit percentage
    active_facility_count = Column(Integer, nullable=False, default=0)
    assessment_date = Column(Date, nullable=False)
    score_version = Column(String(16), nullable=False, default="v1.0.0")
    source_type = Column(String(32), nullable=False, default="SYNTHETIC_BUREAU_V1")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    applicant = relationship("Applicant", back_populates="credit_profiles")


# ==============================================================================
# ENTITY E: LoanProduct
# ==============================================================================
class LoanProduct(Base):
    __tablename__ = "loan_products"

    product_id = Column(String(16), primary_key=True)  # PROD-001..004
    product_name = Column(String(64), nullable=False)
    product_type = Column(String(32), nullable=False)
    min_principal = Column(Numeric(12, 2), nullable=False)
    max_principal = Column(Numeric(12, 2), nullable=False)
    min_term_months = Column(Integer, nullable=False)
    max_term_months = Column(Integer, nullable=False)
    annual_interest_rate = Column(Numeric(5, 2), nullable=False)
    processing_fee_rate = Column(Numeric(5, 2), nullable=False)
    maximum_dti = Column(Numeric(5, 2), nullable=False)
    maximum_foir = Column(Numeric(5, 2), nullable=False)
    minimum_credit_score = Column(Integer, nullable=False)
    product_status = Column(String(24), nullable=False, default="ACTIVE")
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)

    loan_applications = relationship("LoanApplication", back_populates="product")


# ==============================================================================
# ENTITY F: LoanApplication
# ==============================================================================
class LoanApplication(Base):
    __tablename__ = "loan_applications"

    application_id = Column(String(32), primary_key=True)  # LOAN-2026-XXXXXX
    applicant_id = Column(String(32), ForeignKey("applicants.applicant_id", ondelete="RESTRICT"), nullable=False, index=True)
    product_id = Column(String(16), ForeignKey("loan_products.product_id", ondelete="RESTRICT"), nullable=False, index=True)
    requested_principal = Column(Numeric(12, 2), nullable=False)
    requested_term_months = Column(Integer, nullable=False)
    application_date = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    application_status = Column(String(24), nullable=False, default="SUBMITTED", index=True)
    submission_channel = Column(String(24), nullable=False, default="ONLINE_PORTAL")
    application_version = Column(Integer, nullable=False, default=1)

    applicant = relationship("Applicant", back_populates="loan_applications")
    product = relationship("LoanProduct", back_populates="loan_applications")
    documents = relationship("Document", back_populates="loan_application", cascade="all, delete-orphan")
    affordability_checks = relationship("AffordabilityCheck", back_populates="loan_application", cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="loan_application", cascade="all, delete-orphan")
    repayment_schedules = relationship("RepaymentSchedule", back_populates="loan_application", cascade="all, delete-orphan")
    disbursement = relationship("Disbursement", back_populates="loan_application", uselist=False)
    status_history = relationship("ApplicationStatusHistory", back_populates="loan_application", cascade="all, delete-orphan")


# ==============================================================================
# ENTITY G: Document
# ==============================================================================
class Document(Base):
    __tablename__ = "documents"

    document_id = Column(String(48), primary_key=True)  # DOC-LOAN-2026-XXXXXX-XXX
    application_id = Column(String(32), ForeignKey("loan_applications.application_id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(32), nullable=False)  # IDENTITY_PROOF, INCOME_PROOF, etc.
    submission_status = Column(String(24), nullable=False, default="SUBMITTED")
    verification_status = Column(String(24), nullable=False, default="PENDING")
    submitted_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    expiry_date = Column(Date, nullable=True)
    rejection_reason = Column(String(255), nullable=True)
    document_reference = Column(String(64), nullable=False)

    loan_application = relationship("LoanApplication", back_populates="documents")
    verification_history = relationship("DocumentVerificationHistory", back_populates="document", cascade="all, delete-orphan")


# ==============================================================================
# ENTITY H: AffordabilityCheck
# ==============================================================================
class AffordabilityCheck(Base):
    __tablename__ = "affordability_checks"

    affordability_check_id = Column(String(48), primary_key=True)  # AFF-LOAN-2026-XXXXXX-XX
    application_id = Column(String(32), ForeignKey("loan_applications.application_id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    monthly_net_income = Column(Numeric(12, 2), nullable=False)
    existing_monthly_debt = Column(Numeric(12, 2), nullable=False)
    proposed_monthly_emi = Column(Numeric(12, 2), nullable=False)
    debt_to_income_ratio = Column(Numeric(6, 2), nullable=False)
    fixed_obligation_ratio = Column(Numeric(6, 2), nullable=False)
    disposable_income = Column(Numeric(12, 2), nullable=False)
    affordability_status = Column(String(24), nullable=False)  # PASSED, BORDERLINE, FAILED
    rule_version = Column(String(16), nullable=False, default="v1.0.0")
    calculation_details = Column(Text, nullable=False)

    loan_application = relationship("LoanApplication", back_populates="affordability_checks")


# ==============================================================================
# ENTITY I: Decision
# ==============================================================================
class Decision(Base):
    __tablename__ = "decisions"

    decision_id = Column(String(48), primary_key=True)  # DEC-LOAN-2026-XXXXXX-XX
    application_id = Column(String(32), ForeignKey("loan_applications.application_id", ondelete="CASCADE"), nullable=False, index=True)
    decision_sequence = Column(Integer, nullable=False, default=1)
    decision_status = Column(String(24), nullable=False)  # APPROVED, REJECTED, MANUAL_REVIEW, PENDING_INFORMATION
    decision_timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    decision_reason_code = Column(String(32), nullable=False)
    decision_explanation = Column(Text, nullable=False)
    risk_score = Column(Integer, nullable=False)
    rules_triggered = Column(Text, nullable=False)  # JSON array
    reviewer_id = Column(String(32), nullable=True)
    rule_version = Column(String(16), nullable=False, default="v1.0.0")

    loan_application = relationship("LoanApplication", back_populates="decisions")
    rule_executions = relationship("DecisionRuleExecution", back_populates="decision", cascade="all, delete-orphan")
    overrides = relationship("DecisionOverrideHistory", back_populates="decision", cascade="all, delete-orphan")


# ==============================================================================
# ENTITY J: RepaymentSchedule
# ==============================================================================
class RepaymentSchedule(Base):
    __tablename__ = "repayment_schedules"

    schedule_id = Column(String(48), primary_key=True)  # SCH-LOAN-2026-XXXXXX-XXX
    application_id = Column(String(32), ForeignKey("loan_applications.application_id", ondelete="CASCADE"), nullable=False, index=True)
    installment_number = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False)
    opening_balance = Column(Numeric(12, 2), nullable=False)
    principal_amount = Column(Numeric(12, 2), nullable=False)
    interest_amount = Column(Numeric(12, 2), nullable=False)
    installment_amount = Column(Numeric(12, 2), nullable=False)
    closing_balance = Column(Numeric(12, 2), nullable=False)
    payment_status = Column(String(24), nullable=False, default="SCHEDULED")
    paid_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    paid_date = Column(Date, nullable=True)

    loan_application = relationship("LoanApplication", back_populates="repayment_schedules")

    __table_args__ = (
        UniqueConstraint("application_id", "installment_number", name="uq_app_installment"),
    )


# ==============================================================================
# SUPPORTING AUDIT & EVENT TABLES
# ==============================================================================
class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"

    history_id = Column(String(48), primary_key=True)
    application_id = Column(String(32), ForeignKey("loan_applications.application_id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status = Column(String(24), nullable=True)
    new_status = Column(String(24), nullable=False)
    changed_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    changed_by = Column(String(64), nullable=False)
    notes = Column(Text, nullable=True)

    loan_application = relationship("LoanApplication", back_populates="status_history")


class DocumentVerificationHistory(Base):
    __tablename__ = "document_verification_history"

    history_id = Column(String(48), primary_key=True)
    document_id = Column(String(48), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status = Column(String(24), nullable=True)
    new_status = Column(String(24), nullable=False)
    verified_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    verified_by = Column(String(64), nullable=False)
    reason = Column(String(255), nullable=True)

    document = relationship("Document", back_populates="verification_history")


class DecisionRule(Base):
    __tablename__ = "decision_rules"

    rule_id = Column(String(32), primary_key=True)
    rule_name = Column(String(64), nullable=False)
    rule_version = Column(String(16), nullable=False, default="v1.0.0")
    priority = Column(Integer, nullable=False)
    severity = Column(String(16), nullable=False)
    description = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)


class DecisionRuleExecution(Base):
    __tablename__ = "decision_rule_executions"

    execution_id = Column(String(48), primary_key=True)
    decision_id = Column(String(48), ForeignKey("decisions.decision_id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(String(32), nullable=False)
    rule_version = Column(String(16), nullable=False, default="v1.0.0")
    evaluated_values = Column(Text, nullable=False)  # JSON snapshot
    is_triggered = Column(Boolean, nullable=False)
    triggered_action = Column(String(24), nullable=True)

    decision = relationship("Decision", back_populates="rule_executions")


class DecisionOverrideHistory(Base):
    __tablename__ = "decision_override_history"

    override_id = Column(String(48), primary_key=True)  # OVR-DEC-...
    decision_id = Column(String(48), ForeignKey("decisions.decision_id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(String(32), ForeignKey("loan_applications.application_id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status = Column(String(24), nullable=False)
    overridden_status = Column(String(24), nullable=False)  # APPROVED, REJECT
    underwriter_id = Column(String(64), nullable=False)
    override_reason = Column(Text, nullable=False)
    overridden_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    decision = relationship("Decision", back_populates="overrides")


class Disbursement(Base):
    __tablename__ = "disbursements"

    disbursement_id = Column(String(48), primary_key=True)
    application_id = Column(String(32), ForeignKey("loan_applications.application_id", ondelete="RESTRICT"), nullable=False, unique=True, index=True)
    disbursed_amount = Column(Numeric(12, 2), nullable=False)
    disbursement_date = Column(Date, nullable=False)
    disbursement_status = Column(String(24), nullable=False, default="DISBURSED")
    bank_reference = Column(String(64), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    loan_application = relationship("LoanApplication", back_populates="disbursement")
    events = relationship("DisbursementEvent", back_populates="disbursement", cascade="all, delete-orphan")


class DisbursementEvent(Base):
    __tablename__ = "disbursement_events"

    event_id = Column(String(48), primary_key=True)
    disbursement_id = Column(String(48), ForeignKey("disbursements.disbursement_id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(32), nullable=False)  # ELIGIBILITY_CHECKED, ELIGIBLE, DISBURSED, FAILED
    event_timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    event_payload = Column(Text, nullable=True)

    disbursement = relationship("Disbursement", back_populates="events")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(String(48), primary_key=True)
    entity_name = Column(String(64), nullable=False)
    record_id = Column(String(64), nullable=False)
    action = Column(String(16), nullable=False)  # INSERT, UPDATE, STATUS_CHANGE
    actor_id = Column(String(64), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    diff = Column(Text, nullable=True)


class DatasetGenerationRun(Base):
    __tablename__ = "dataset_generation_runs"

    run_id = Column(String(48), primary_key=True)
    seed = Column(Integer, nullable=False)
    profile = Column(String(16), nullable=False)
    applicant_count = Column(Integer, nullable=False)
    application_count = Column(Integer, nullable=False)
    anomaly_count = Column(Integer, nullable=False)
    config_hash = Column(String(64), nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=False)


class GroundTruthAnomaly(Base):
    __tablename__ = "ground_truth_anomalies"

    anomaly_id = Column(String(32), primary_key=True)  # ANOM-2026-XXXXXX
    entity_name = Column(String(64), nullable=False)
    record_id = Column(String(64), nullable=False)
    issue_type = Column(String(32), nullable=False)
    expected_label = Column(String(32), nullable=False, default="ANOMALY")
    severity = Column(String(16), nullable=False)
    expected_detection = Column(Boolean, nullable=False, default=True)
    expected_decision = Column(String(24), nullable=True)
    explanation = Column(Text, nullable=False)
    injection_timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

