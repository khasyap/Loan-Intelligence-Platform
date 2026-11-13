# API Documentation & REST Interface Specification

## 1. Overview
The platform exposes RESTful endpoints under `/api/v1` built with FastAPI and documented via interactive Swagger UI at `/docs`.

---

## 2. Endpoints Reference

### 2.1 Loan Products
- `GET /api/v1/products`
  - Returns the 4 configured loan products and their underwriting parameters.

### 2.2 Applicants
- `GET /api/v1/applicants`
  - Query parameters: `skip` (default 0), `limit` (default 50), `search` (optional string).
  - Returns paginated list of applicants.
- `GET /api/v1/applicants/{applicant_id}`
  - Returns complete applicant profile including employment history, credit facilities, and income records.

### 2.3 Applications
- `GET /api/v1/applications`
  - Query parameters: `status` (optional), `product_id` (optional), `skip`, `limit`.
  - Returns filtered applications list.
- `GET /api/v1/applications/{application_id}`
  - Returns application details, applicant, product, documents, affordability check, decision trace, and repayment installments.
- `POST /api/v1/applications`
  - Payload: `{ applicant_id, product_id, requested_principal, requested_term_months, submission_channel }`
  - Live underwrites the application in real time, calculating affordability, running the 10 decision rules, and generating amortization installments if approved.

### 2.4 Repayment Schedules
- `GET /api/v1/repayments/{application_id}`
  - Returns the complete installment schedule with opening/closing balances and verified penny-reconciliation audit report.

### 2.5 Anomalies & Evaluation
- `GET /api/v1/anomalies/evaluation`
  - Returns precision, recall, F1 score, and 5-category breakdown against ground truth.
- `GET /api/v1/anomalies/ground-truth`
  - Returns the segregated ground-truth exception register for audits.

### 2.6 Analytics & Dashboards
- `GET /api/v1/analytics/executive`
  - Returns portfolio volume, approval/rejection rates, requested/approved/disbursed capital.
- `GET /api/v1/analytics/risk`
  - Returns credit score, DTI, FOIR, and decision reason code distributions.
- `GET /api/v1/analytics/operations`
  - Returns application lifecycle funnel and document verification status counts.

