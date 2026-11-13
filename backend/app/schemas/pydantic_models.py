from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from decimal import Decimal
import datetime

# ------------------------------------------------------------------------------
# Loan Product Schemas
# ------------------------------------------------------------------------------
class ProductSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: str
    product_name: str
    product_type: str
    min_principal: float
    max_principal: float
    min_term_months: int
    max_term_months: int
    annual_interest_rate: float
    processing_fee_rate: float
    maximum_dti: float
    maximum_foir: float
    minimum_credit_score: int
    product_status: str

# ------------------------------------------------------------------------------
# Applicant Schemas
# ------------------------------------------------------------------------------
class ApplicantBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    applicant_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    city: str
    state: str
    postal_code: str
    credit_score: int
    applicant_status: str

# ------------------------------------------------------------------------------
# Application Schemas
# ------------------------------------------------------------------------------
class ApplicationCreate(BaseModel):
    applicant_id: str
    product_id: str
    requested_principal: float
    requested_term_months: int
    submission_channel: Optional[str] = "ONLINE_PORTAL"

class ApplicationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_id: str
    applicant_id: str
    product_id: str
    requested_principal: float
    requested_term_months: int
    application_date: datetime.datetime
    application_status: str
    submission_channel: str

class DocumentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    document_type: str
    submission_status: str
    verification_status: str
    rejection_reason: Optional[str] = None

class AffordabilitySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    affordability_check_id: str
    monthly_net_income: float
    existing_monthly_debt: float
    proposed_monthly_emi: float
    debt_to_income_ratio: float
    fixed_obligation_ratio: float
    disposable_income: float
    affordability_status: str
    calculation_details: str

class DecisionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    decision_id: str
    decision_status: str
    decision_timestamp: datetime.datetime
    decision_reason_code: str
    decision_explanation: str
    risk_score: int
    rules_triggered: str
    rule_version: str

class InstallmentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    schedule_id: str
    installment_number: int
    due_date: datetime.date
    opening_balance: float
    principal_amount: float
    interest_amount: float
    installment_amount: float
    closing_balance: float
    payment_status: str

class ApplicationDetail(ApplicationSummary):
    applicant: ApplicantBase
    product: ProductSchema
    documents: List[DocumentSchema]
    affordability: Optional[AffordabilitySchema] = None
    decision: Optional[DecisionSchema] = None
    installments: List[InstallmentSchema] = []
