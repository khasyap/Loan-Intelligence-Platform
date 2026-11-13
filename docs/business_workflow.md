# Business Workflow: Loan Origination, Risk Assessment & Disbursement Lifecycle

## 1. End-to-End Origination Lifecycle

The lending workflow transitions through strictly ordered, immutable operational stages:

```
[Customer Submission]
       │
       ▼
[Document Ingestion & Verification] ──(Missing/Expired)──► [Pending Information]
       │                                                         │
   (Verified)                                                    │ (Resubmitted)
       ▼                                                         ▼
[Affordability & Debt Assessment] ◄──────────────────────────────┘
  (DTI, FOIR, Reducing-Balance EMI)
       │
       ▼
[Explainable Decision Rules Engine] ──(Borderline/Soft)──► [Manual Underwriter Review]
       │                                                         │
   (Hard Decision)                                           (Override)
       ├─────────────────────────────────┬───────────────────────┤
       ▼                                 ▼                       ▼
   [APPROVED]                        [REJECT]               [APPROVED]
       │                                 │                       │
       │                                 ▼                       │
       ▼                            [Case Closed]                ▼
[Disbursement Eligibility Gate] ◄────────────────────────────────┘
  - Verified Documents Check
  - Zero Prior Disbursed Check
  - Terms Boundary Audit
       │
   (Eligible)
       ▼
[Amortization Schedule Generation]
  - Penny-Reconciled Repayment Plan
  - Reducing Balance Schedule
       │
       ▼
[Disbursement Payout Event]
  - Single Successful Payout Control
  - Immutable Event Ledger
```

---

## 2. Five Independent Lifecycle State Machines

To prevent unauthorized transitions, maintain clean separation of concerns, and decouple approval from disbursement eligibility, the platform implements five independent state machines:

### 2.1 Loan Application State Machine
- **States**: `DRAFT`, `SUBMITTED`, `DOCUMENT_PENDING`, `UNDER_REVIEW`, `PENDING_INFORMATION`, `MANUAL_REVIEW`, `APPROVED`, `DISBURSED`, `REJECTED`, `CANCELLED`
- **Valid Transitions**:
  - `DRAFT` $\rightarrow$ `SUBMITTED`, `CANCELLED`
  - `SUBMITTED` $\rightarrow$ `UNDER_REVIEW`, `DOCUMENT_PENDING`, `CANCELLED`
  - `DOCUMENT_PENDING` $\rightarrow$ `UNDER_REVIEW`, `CANCELLED`
  - `UNDER_REVIEW` $\rightarrow$ `APPROVED`, `REJECTED`, `MANUAL_REVIEW`, `DOCUMENT_PENDING`, `PENDING_INFORMATION`
  - `PENDING_INFORMATION` $\rightarrow$ `UNDER_REVIEW`, `CANCELLED`
  - `MANUAL_REVIEW` $\rightarrow$ `APPROVED`, `REJECTED`, `PENDING_INFORMATION`
  - `APPROVED` $\rightarrow$ `DISBURSED`, `CANCELLED`
- **Terminal States**: `DISBURSED`, `REJECTED`, `CANCELLED`

### 2.2 Decision State Machine
- **States**: `PENDING`, `EVALUATED`, `UNDERWRITER_REVIEW`, `OVERRIDDEN`, `FINALIZED`
- **Valid Transitions**:
  - `PENDING` $\rightarrow$ `EVALUATED`
  - `EVALUATED` $\rightarrow$ `UNDERWRITER_REVIEW`, `FINALIZED`, `OVERRIDDEN`
  - `UNDERWRITER_REVIEW` $\rightarrow$ `OVERRIDDEN`, `FINALIZED`
  - `OVERRIDDEN` $\rightarrow$ `FINALIZED`
- **Terminal State**: `FINALIZED`

### 2.3 Document Verification State Machine
- **States**: `NOT_SUBMITTED`, `SUBMITTED`, `UNDER_REVIEW`, `VERIFIED`, `REJECTED`, `EXPIRED`
- **Valid Transitions**:
  - `NOT_SUBMITTED` $\rightarrow$ `SUBMITTED`
  - `SUBMITTED` $\rightarrow$ `UNDER_REVIEW`
  - `UNDER_REVIEW` $\rightarrow$ `VERIFIED`, `REJECTED`, `EXPIRED`
  - `REJECTED` $\rightarrow$ `SUBMITTED` (Allows applicant resubmission)
  - `EXPIRED` $\rightarrow$ `SUBMITTED` (Allows applicant resubmission)
  - `VERIFIED` $\rightarrow$ `EXPIRED`

### 2.4 Disbursement Payout State Machine
- **States**: `NOT_ELIGIBLE`, `ELIGIBILITY_CHECKED`, `ELIGIBLE`, `DISBURSEMENT_INITIATED`, `DISBURSED`, `FAILED`, `REVERSED`
- **Valid Transitions**:
  - `NOT_ELIGIBLE` $\rightarrow$ `ELIGIBILITY_CHECKED`
  - `ELIGIBILITY_CHECKED` $\rightarrow$ `ELIGIBLE`, `NOT_ELIGIBLE`
  - `ELIGIBLE` $\rightarrow$ `DISBURSEMENT_INITIATED`, `NOT_ELIGIBLE`
  - `DISBURSEMENT_INITIATED` $\rightarrow$ `DISBURSED`, `FAILED`
  - `FAILED` $\rightarrow$ `DISBURSEMENT_INITIATED`, `REVERSED`
  - `DISBURSED` $\rightarrow$ `REVERSED`
- **Terminal State**: `REVERSED`

### 2.5 Repayment Servicing State Machine
- **States**: `PENDING_DISBURSEMENT`, `ACTIVE`, `DELINQUENT`, `DEFAULTED`, `PAID_OFF`
- **Valid Transitions**:
  - `PENDING_DISBURSEMENT` $\rightarrow$ `ACTIVE`
  - `ACTIVE` $\rightarrow$ `PAID_OFF`, `DELINQUENT`
  - `DELINQUENT` $\rightarrow$ `ACTIVE`, `DEFAULTED`, `PAID_OFF`
  - `DEFAULTED` $\rightarrow$ `PAID_OFF`
- **Terminal State**: `PAID_OFF`

---

## 3. Strict Disbursement Prerequisite Gate

Disbursement eligibility is never assumed automatically upon approval. The function `evaluate_disbursement_prerequisites` acts as an automated gate asserting:

1. **Approved Decision Exists**: A decision record exists with `decision_status == 'APPROVED'`. Rejections or pending review block payout.
2. **100% Mandatory Documents Verified**: All submitted checklist items have `verification_status == 'VERIFIED'`. Any `PENDING`, `REJECTED`, or `EXPIRED` document blocks payout.
3. **Affordability Passed**: An affordability assessment exists with `affordability_status == 'PASSED'`.
4. **Zero Prior Successful Disbursement**: Queries the operational disbursements ledger for existing records with `disbursement_status == 'DISBURSED'` for the given application.
