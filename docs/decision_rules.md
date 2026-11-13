# Decision Rules Specification & Explainability Engine

## 1. Principles of Fair & Deterministic Decisioning

The Decision Engine implements an explainable, deterministic rule-based architecture. Every loan application evaluated by the platform produces a transparent, reproducible decision trail.

### Non-Negotiable Compliance Guarantees:
1. **Zero Protected Attributes**: Demographic attributes such as gender, race, color, ethnicity, religion, disability, marital status, or sexual orientation are strictly prohibited from all decision logic, eligibility filters, and risk models.
2. **Deterministic Evaluation**: Given the exact same inputs (application amount, term, applicant credit profile, verified income, existing debt obligations, and document verification results), the engine produces the identical decision output.
3. **Traceability & Versioning**: Every decision records the rules evaluated, rules triggered, exact input and calculated values, reviewer ID, timestamp, and rule policy version (`v1.0.0`).
4. **Non-Destructive Decision Ledger**: Re-evaluations (e.g. following document resubmission or manual underwriter override) append a new `Decision` record with an incremented `decision_sequence`, leaving prior decisions intact.

---

## 2. Decision Outcomes & Status Hierarchy

When evaluated, an application is assigned one of four primary decision states:

- **`APPROVED`**: All eligibility and affordability criteria are met. Mandatory documents are verified. No blocking risk flags triggered. Eligible for disbursement upon final authorization.
- **`REJECTED`**: Application violates hard policy constraints (e.g. credit score below product cutoff, principal out of bounds, severe debt overburden). Cannot proceed.
- **`MANUAL_REVIEW`**: Application presents borderline metrics or non-blocking policy exceptions requiring underwriter discretion (e.g. borderline credit score, minor tenure gaps, duplicate active submissions).
- **`PENDING_INFORMATION`**: One or more mandatory documents are missing, unreadable, expired, or rejected. Application is placed on hold awaiting customer resubmission.

---

## 3. The 10 Deterministic Decision Rules

The engine evaluates rules in strict priority order (Priority 1 = Highest / First). Hard-fail rules immediately abort subsequent approvals.

| Priority | Rule ID | Rule Name | Severity | Condition / Trigger Logic | Outcome if Triggered | Reason Code |
|:---:|:---|:---|:---:|:---|:---:|:---|
| **1** | `RULE_01` | Product Limits Check | `HARD_FAIL` | `requested_principal < min_principal` OR `requested_principal > max_principal` OR `requested_term_months < min_term_months` OR `requested_term_months > max_term_months` | `REJECT` | `REJ_PRODUCT_LIMITS_BREACH` |
| **2** | `RULE_02` | Minimum Credit Score | `HARD_FAIL` | `credit_score < product.minimum_credit_score` | `REJECT` | `REJ_CREDIT_SCORE_BELOW_MIN` |
| **3** | `RULE_03` | Debt-to-Income (DTI) Limit | `HARD_FAIL` / `SOFT_FAIL` | If `DTI > product.maximum_dti * 1.25` -> `REJECT`<br>Else if `DTI > product.maximum_dti` -> `MANUAL_REVIEW` | `REJECT` / `MANUAL_REVIEW` | `REJ_DTI_EXCEEDED` / `REV_DTI_BORDERLINE` |
| **4** | `RULE_04` | Fixed Obligation (FOIR) Limit | `HARD_FAIL` / `SOFT_FAIL` | If `FOIR > product.maximum_foir * 1.15` -> `REJECT`<br>Else if `FOIR > product.maximum_foir` -> `MANUAL_REVIEW` | `REJECT` / `MANUAL_REVIEW` | `REJ_FOIR_EXCEEDED` / `REV_FOIR_BORDERLINE` |
| **5** | `RULE_05` | Mandatory Income Proof | `SOFT_FAIL` | Missing or unverified `INCOME_PROOF` or `BANK_STATEMENT` | `PENDING_INFO` / `MANUAL_REVIEW` | `REV_INCOME_PROOF_MISSING` |
| **6** | `RULE_06` | Employment Stability | `SOFT_FAIL` | Continuous employment tenure < 6 months OR `employment_status == 'UNEMPLOYED'` | `MANUAL_REVIEW` | `REV_EMPLOYMENT_UNSTABLE` |
| **7** | `RULE_07` | Duplicate Active Application | `SOFT_FAIL` | Applicant has another application in `SUBMITTED`, `UNDER_REVIEW`, or `APPROVED` | `MANUAL_REVIEW` | `REV_DUPLICATE_APPLICATION` |
| **8** | `RULE_08` | Borderline Credit Score | `SOFT_FAIL` | `credit_score` is within 25 points above `product.minimum_credit_score` | `MANUAL_REVIEW` | `REV_CREDIT_SCORE_BORDERLINE` |
| **9** | `RULE_09` | Document Verification Failure | `HARD_FAIL` / `SOFT_FAIL` | Mandatory document has `verification_status == 'REJECTED'` or `EXPIRED` | `REJECT` / `PENDING_INFO` | `REJ_DOC_VERIF_FAILED` |
| **10** | `RULE_10` | Clean Application Approval | `PASS` | No `HARD_FAIL` or `SOFT_FAIL` rules triggered; all mandatory checks verified | `APPROVED` | `APP_CLEAN_APPROVAL` |

---

## 4. Detailed Specification of Each Rule

### RULE_01: Product Eligibility Limits
- **Intent**: Ensure requested terms conform to the product's sanctioned credit boundaries.
- **Inputs**:
  - `application.requested_principal`
  - `application.requested_term_months`
  - `product.min_principal`, `product.max_principal`
  - `product.min_term_months`, `product.max_term_months`
- **Logic**:
  ```python
  if requested_principal < product.min_principal or requested_principal > product.max_principal:
      return Triggered(action="REJECT", code="REJ_PRINCIPAL_OUT_OF_BOUNDS", 
                       msg=f"Requested principal {requested_principal} outside product range [{product.min_principal}, {product.max_principal}]")
  if requested_term_months < product.min_term_months or requested_term_months > product.max_term_months:
      return Triggered(action="REJECT", code="REJ_TERM_OUT_OF_BOUNDS",
                       msg=f"Requested term {requested_term_months} months outside product range [{product.min_term_months}, {product.max_term_months}]")
  ```

### RULE_02: Minimum Credit Score
- **Intent**: Reject borrowers whose credit history poses unacceptably high default probability.
- **Inputs**:
  - `applicant.credit_score`
  - `product.minimum_credit_score`
- **Logic**:
  ```python
  if applicant.credit_score < product.minimum_credit_score:
      return Triggered(action="REJECT", code="REJ_CREDIT_SCORE_BELOW_MIN",
                       msg=f"Applicant credit score {applicant.credit_score} is below product cutoff of {product.minimum_credit_score}")
  ```

### RULE_03: Debt-to-Income (DTI) Threshold
- **Intent**: Cap pre-existing debt obligations relative to gross income.
- **Formula**:
  $$\text{DTI} = \left(\frac{\text{Existing Monthly Debt Obligations}}{\text{Monthly Gross Income}}\right) \times 100$$
- **Logic**:
  - If $\text{DTI} > 1.25 \times \text{product.maximum\_dti}$: `REJECT` (`REJ_DTI_SEVERE_OVERBURDEN`)
  - Else if $\text{DTI} > \text{product.maximum\_dti}$: `MANUAL_REVIEW` (`REV_DTI_EXCEEDS_BENCHMARK`)

### RULE_04: Fixed Obligation to Income Ratio (FOIR)
- **Intent**: Assess comprehensive repayment capacity including the proposed new loan installment.
- **Formula**:
  $$\text{FOIR} = \left(\frac{\text{Existing Monthly Debt Obligations} + \text{Proposed Monthly EMI}}{\text{Monthly Net Income}}\right) \times 100$$
- **Logic**:
  - If $\text{FOIR} > 1.15 \times \text{product.maximum\_foir}$: `REJECT` (`REJ_FOIR_UNSUSTAINABLE`)
  - Else if $\text{FOIR} > \text{product.maximum\_foir}$: `MANUAL_REVIEW` (`REV_FOIR_BORDERLINE`)

### RULE_05: Mandatory Income Proof
- **Intent**: Guard against undocumented or unverifiable cash flows.
- **Logic**:
  - Check for existence of verified `INCOME_PROOF` or `BANK_STATEMENT` within the last 90 days.
  - If absent: Action `PENDING_INFORMATION`, code `REV_INCOME_PROOF_MISSING`.

### RULE_06: Employment Stability
- **Intent**: Mitigate income volatility from unstable or interrupted employment.
- **Logic**:
  - Calculate active employment tenure = `current_date - employment_start_date`.
  - If tenure < 6 months and applicant is not seasoned self-employed (> 2 years in industry): Trigger `MANUAL_REVIEW`, code `REV_EMPLOYMENT_TENURE_SHORT`.

### RULE_07: Duplicate Active Application
- **Intent**: Prevent fraud or accidental multi-channel submission.
- **Logic**:
  - Query active applications for the same `applicant_id` with statuses in `['SUBMITTED', 'UNDER_REVIEW', 'APPROVED']`.
  - If count > 1: Trigger `MANUAL_REVIEW`, code `REV_DUPLICATE_APPLICATION_FLAG`.

### RULE_08: Borderline Credit Score
- **Intent**: Ensure human risk analyst reviews near-cutoff applicants.
- **Logic**:
  - If `product.minimum_credit_score <= applicant.credit_score < product.minimum_credit_score + 25`: Trigger `MANUAL_REVIEW`, code `REV_CREDIT_SCORE_BORDERLINE`.

### RULE_09: Document Verification Status
- **Intent**: Halt origination when fraud, forgery, or expiry is detected in submitted records.
- **Logic**:
  - If any submitted document is marked `REJECTED`: Trigger `MANUAL_REVIEW` or `REJECT` based on rejection cause.
  - If any mandatory document is `EXPIRED`: Trigger `PENDING_INFORMATION`.

### RULE_10: Clean Application Approval
- **Intent**: Automatically approve high-quality, fully compliant applications.
- **Logic**:
  - Executed only if Rules 1 through 9 yielded no `HARD_FAIL` or `SOFT_FAIL`.
  - Action `APPROVED`, code `APP_CLEAN_APPROVAL`, explanation "All underwriting rules passed successfully."

---

## 5. Decision Reason Codes Catalog

| Code | Type | Description |
|:---|:---|:---|
| `APP_CLEAN_APPROVAL` | Success | Complete compliance with product, credit, and affordability policies. |
| `REJ_PRODUCT_LIMITS_BREACH` | Hard Fail | Requested loan amount or term violates sanctioned product guidelines. |
| `REJ_CREDIT_SCORE_BELOW_MIN`| Hard Fail | Credit bureau score fails to meet the minimum risk appetite threshold. |
| `REJ_DTI_EXCEEDED` | Hard Fail | Pre-existing debt burden leaves insufficient cash flow for loan servicing. |
| `REJ_FOIR_EXCEEDED` | Hard Fail | Total monthly obligations exceed allowable percentage of net earnings. |
| `REJ_DOC_VERIF_FAILED` | Hard Fail | Identity or KYC documents failed authentication or integrity checks. |
| `REV_DTI_BORDERLINE` | Review | DTI exceeds standard limit but falls within secondary tolerance buffer. |
| `REV_FOIR_BORDERLINE` | Review | FOIR exceeds standard limit but applicant exhibits high disposable reserves. |
| `REV_CREDIT_SCORE_BORDERLINE`| Review | Score is marginally above threshold; requires manual review of repayment history. |
| `REV_EMPLOYMENT_UNSTABLE` | Review | Recent change of employment or probationary status requires underwriter sign-off. |
| `REV_DUPLICATE_APPLICATION` | Review | Multi-channel application collision detected. |
| `REV_INCOME_PROOF_MISSING` | Info | Mandatory income verification document not yet received or processed. |

---

## 6. Formal Decision-Rule Precedence & Conflict Resolution

When multiple rules trigger conflicting recommendations for a single application, the engine resolves the final status according to strict severity tiers:

```
+-------------------------------------------------------------------------------+
|  TIER 1: HARD_FAIL (Strict Block)                                             |
|  Outcome: REJECT | Reason Code: First triggering hard-fail code               |
|  Overrides ALL other rule proposals. Requires complete re-application.        |
+-------------------------------------------------------------------------------+
                                       |
                                       v
+-------------------------------------------------------------------------------+
|  TIER 2: SOFT_FAIL_PENDING (Missing Documentation)                            |
|  Outcome: PENDING_INFORMATION | Reason Code: Primary missing doc requirement   |
|  Halts processing until customer resubmits required proofs.                   |
+-------------------------------------------------------------------------------+
                                       |
                                       v
+-------------------------------------------------------------------------------+
|  TIER 3: SOFT_FAIL_REVIEW (Discretionary Exception)                           |
|  Outcome: MANUAL_REVIEW | Reason Code: Primary borderline / review issue       |
|  Routes application to Human Senior Underwriter queue for detailed assessment.|
+-------------------------------------------------------------------------------+
                                       |
                                       v
+-------------------------------------------------------------------------------+
|  TIER 4: PASS (Full Policy Compliance)                                        |
|  Outcome: APPROVED | Reason Code: APP_CLEAN_APPROVAL                          |
|  Authorizes generation of repayment schedules and eligibility for payout.     |
+-------------------------------------------------------------------------------+
```

---

## 7. Underwriter Review & Human Override Workflow

Applications routed to `MANUAL_REVIEW` may only be resolved by an authorized credit underwriter:

1. **Authorization**: Only users with the `RISK_REVIEWER` or `ADMIN` role are permitted to execute an override.
2. **Supported Transitions**:
   - `MANUAL_REVIEW` $\rightarrow$ `APPROVED` (with mandatory compensating factor documentation).
   - `MANUAL_REVIEW` $\rightarrow$ `REJECT` (formal adverse action notice).
3. **Audit Ledger**:
   - Every override automatically logs an entry in `decision_override_history` (`override_id`, `decision_id`, `application_id`, `previous_status`, `overridden_status`, `underwriter_id`, `override_reason`, `overridden_at`).
   - The decision explanation is augmented with: `Manual underwriter override by <underwriter_id>: <reason>`.
4. **Reproducibility Guarantee**:
   - The original automated rule execution snapshot in `decision_rule_executions` is never modified or deleted, preserving 100% auditability for banking regulators.


