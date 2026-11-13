export interface ExecutiveKPIs {
  total_applicants: number;
  total_applications: number;
  dataset_profile?: string;
  approved_count: number;
  rejected_count: number;
  manual_review_count: number;
  pending_info_count: number;
  approval_rate: number;
  rejection_rate: number;
  total_requested_principal: number;
  total_approved_principal: number;
  total_disbursed_principal: number;
}

export interface DistributionItem {
  range?: string;
  code?: string;
  status?: string;
  count: number;
}

export interface RiskAnalytics {
  credit_score_distribution: { range: string; count: number }[];
  dti_distribution: { range: string; count: number }[];
  foir_distribution: { range: string; count: number }[];
  reason_code_distribution: { code: string; count: number }[];
}

export interface OperationsAnalytics {
  lifecycle_funnel: { status: string; count: number }[];
  document_verification_summary: { status: string; count: number }[];
}

export interface AnomalyCategoryMetric {
  ground_truth_count: number;
  detected_count: number;
  true_positives: number;
  false_negatives: number;
  false_positives: number;
  precision: number;
  recall: number;
  f1_score: number;
}

export interface AnomalyEvaluation {
  summary: {
    total_ground_truth: number;
    total_detected: number;
    true_positives: number;
    false_positives: number;
    false_negatives: number;
    precision: number;
    recall: number;
    f1_score: number;
  };
  category_breakdown: Record<string, AnomalyCategoryMetric>;
}

export interface GroundTruthItem {
  anomaly_id: string;
  entity_name: string;
  record_id: string;
  issue_type: string;
  severity: string;
  expected_decision: string;
  explanation: string;
}

export interface ApplicationItem {
  application_id: string;
  applicant_id: string;
  product_id: string;
  requested_principal: number;
  requested_term_months: number;
  application_date: string;
  application_status: string;
  submission_channel: string;
}

export interface ProductItem {
  product_id: string;
  product_name: string;
  product_type: string;
  min_principal: number;
  max_principal: number;
  min_term_months: number;
  max_term_months: number;
  annual_interest_rate: number;
  processing_fee_rate: number;
  maximum_dti: number;
  maximum_foir: number;
  minimum_credit_score: number;
  product_status: string;
}

export interface InstallmentItem {
  schedule_id: string;
  installment_number: number;
  due_date: string;
  opening_balance: number;
  principal_amount: number;
  interest_amount: number;
  installment_amount: number;
  closing_balance: number;
  payment_status: string;
}

export interface RepaymentDetails {
  application_id: string;
  disbursed_principal: number;
  total_installments: number;
  is_reconciled: boolean;
  audit_details: {
    disbursed_principal: number;
    total_principal_repaid: number;
    total_interest: number;
    total_installments: number;
    principal_difference: number;
    final_closing_balance: number;
    is_reconciled: boolean;
  };
  installments: InstallmentItem[];
}


export type UserRole = "ADMIN" | "RISK_REVIEWER" | "OPERATIONS_ANALYST" | "CUSTOMER";

export interface UserProfile {
  email: string;
  name: string;
  role: UserRole;
  applicant_id?: string | null;
  access_token: string;
}
