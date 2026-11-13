# Loan Intelligence Platform

**End-to-End Loan Origination, Risk Assessment, Decision Management & Anomaly Detection System**

An enterprise-grade lending platform engineered with reproducible synthetic data generation, automated affordability assessments, deterministic underwriting decision rules, penny-reconciled repayment amortization, and an isolated edge-case anomaly detection framework.

---

## 1. Key Features

- **Deterministic Synthetic Generation**: Parametric multi-scale generation (`starter`: 200/120, `medium`: 2,000/1,200, `full`: 10,000 applicants & 6,000 applications) with bit-for-bit reproducibility via fixed seed (`20261022`).
- **Explainable Decision Rules Engine**: 10 prioritized underwriting rules with formal severity tiers (`HARD_FAIL` $\rightarrow$ `SOFT_FAIL_PENDING` $\rightarrow$ `SOFT_FAIL_REVIEW` $\rightarrow$ `PASS`), traceable reason codes, human underwriter override protocol, and zero usage of protected demographic attributes.
- **Precision Financial Math**: Reducing-balance monthly EMI, Existing & Total Debt-to-Income (DTI), Fixed Obligation to Income Ratio (FOIR), Disposable Income, and penny-reconciled schedule amortization.
- **Behavioral Credit Profile Derivation**: `CreditProfile` entity deterministically calculated from credit facilities, on-time payment ratio, card utilization, and delinquencies, clamped to $[300, 900]$.
- **Anomaly Staging Layer & Isolated Ground Truth**: 5 mandatory edge-case anomaly categories staged in an exception queue to protect operational database integrity while allowing independent auditing with 100% precision and recall.
- **Five Independent State Machines**: Formal lifecycle guards for Loan Application, Underwriting Decision, Document Verification, Disbursement Payout, and Repayment Servicing.
- **Role-Based Access Control (RBAC)**: Secure PBKDF2-HMAC-SHA256 password hashing with signed Bearer authentication across 4 primary banking personas.
- **Full-Stack REST & UI Architecture**: FastAPI backend with Pydantic v2 validation + React 18, TypeScript, Tailwind CSS, and Recharts financial dashboards with an interactive origination simulator.
- **Multi-Format Persistence & Portability**: Generates production CSV (14 datasets), JSON, and SQL exports (273,645 rows in Full mode), with dual runtime support for SQLite and PostgreSQL 16.

---

## 2. Technology Stack

- **Backend**: Python 3.11+ / 3.13, FastAPI, Pydantic v2, SQLAlchemy 2.0
- **Data Engineering**: Pandas, NumPy, Faker, PyYAML
- **Frontend**: React 18, TypeScript, Tailwind CSS, Recharts, Lucide Icons, Vite
- **Database**: PostgreSQL 16 (Docker) / SQLite (Local zero-setup mode)
- **Quality Assurance**: Pytest (56 passing tests across math, rules, credit profiles, lifecycles, security, anomalies, and reproducibility)
- **DevOps**: Docker, Docker Compose

---

## 3. Project Directory Structure

```
loan-intelligence-platform/
│
├── backend/
│   ├── app/
│   │   ├── api/routers/           # 12 REST routers: auth, apps, applicants, products, decisions, repayments, anomalies
│   │   ├── calculations/          # DTI, FOIR, reducing-balance EMI, schedule amortization
│   │   ├── database/              # SQLAlchemy session and SQLite/Postgres connection
│   │   ├── models/                # 20 relational entities + audit tables
│   │   ├── rules_engine/          # 10 prioritized rules + underwriter override protocol
│   │   ├── services/              # 5 lifecycle state machines + RBAC security & PBKDF2 hashing
│   │   ├── anomaly_detection/     # Independent operational anomaly detector (zero GT leakage)
│   │   ├── evaluation/            # Precision, recall, F1, and comprehensive evaluation metrics
│   │   ├── validation/            # Structural, relational, lifecycle & arithmetic validator
│   │   ├── schemas/               # Pydantic v2 request/response models
│   │   └── main.py                # FastAPI entry point & SPA frontend host
│   └── tests/                     # 56 automated unit, integration, and mandatory suite tests
│
├── frontend/
│   ├── src/
│   │   ├── components/            # Executive, Risk, Operations, Anomaly & Repayment dashboards
│   │   ├── services/api.ts        # REST API integration client
│   │   ├── types/                 # TypeScript interfaces
│   │   ├── App.tsx                # SPA tab coordinator and live loan origination modal
│   │   └── main.tsx               # React entry point
│   ├── package.json
│   └── vite.config.ts
│
├── generator/
│   ├── master_data/               # Applicants, Products, Employment, Income, Credit Facilities, Credit Profiles
│   ├── transaction_data/          # Applications, Documents, Affordability, Decisions, Repayments, Disbursements
│   ├── anomaly_injection/         # Anomaly Staging Layer for 5 mandatory categories
│   ├── exporters/                 # CSV, JSON, SQL seed exporters & checksum manifests
│   └── generate.py                # Master CLI orchestrator
│
├── config/
│   ├── generation.yaml            # Seed, distributions, profiles, export paths
│   └── business_rules.yaml        # 4 products & 10 decision rules thresholds
│
├── database/
│   └── schema.sql                 # ANSI SQL / PostgreSQL / SQLite DDL schema (20 tables)
│
├── data/
│   ├── source_manifest.json       # Synthetic data provenance, generator seed, and licensing
│   ├── exports/ (csv/, json/, sql/)
│   ├── ground_truth.csv           # Segregated anomaly ground truth (14 CSVs total)
│   └── ground_truth.json
│
├── reports/
│   ├── comprehensive_evaluation.json # Regulatory compliance, math error rate, and anomaly metrics
│   ├── validation_summary.json    # Automated structural and arithmetic validation results
│   ├── anomaly_evaluation.json    # Precision, recall, F1, and category metrics
│   └── reproducibility_report.json# Double-run cryptographic checksum comparison
│
├── docs/                          # Comprehensive technical documentation & gap analysis
├── scripts/                       # Reproducibility and verification runner scripts
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## 4. Quick Start & Execution Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ & pnpm (or npm)

### 1. Generate Synthetic Data & Seed Database
```bash
# Generate starter dataset (200 applicants, 120 applications, 25 anomalies)
python generator/generate.py --profile starter

# Or generate full hackathon benchmark (10,000 applicants, 6,000 applications, 300 anomalies)
python generator/generate.py --profile full
```

### 2. Run Automated Pytest Suite (56 Tests)
```bash
python -m pytest backend/tests/ -v
```

### 3. Verify 100% Cryptographic Reproducibility Across 14 Datasets
```bash
python scripts/test_reproducibility.py
```

### 4. Start the Application Backend & UI
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
- Web Application: **http://127.0.0.1:8000/**
- Interactive Swagger API: **http://127.0.0.1:8000/docs**

### Demo Accounts for Role-Based Access:
- **System Administrator**: `admin@bank.org` / `AdminDemo@2026`
- **Senior Underwriting Officer**: `reviewer@bank.org` / `ReviewerDemo@2026`
- **Operations Analyst**: `ops@bank.org` / `OpsDemo@2026`
- **Borrower / Applicant**: `customer@bank.org` / `CustomerDemo@2026`

---

## 5. Docker Deployment

Deploy with PostgreSQL 16 and automated database seeding in one command:
```bash
docker-compose up --build
```
Access the application at `http://localhost:8000`.

---

## 6. Verification Results

- **Automated Tests**: 56/56 passed (100% pass rate) in 1.88s.
- **Validation Engine**: 48,969 / 48,969 checks passed (0 referential integrity failures, 0 arithmetic failures, 0 lifecycle violations).
- **Quality & Regulatory Metrics**:
  - Decision Rule Consistency: **100.0%**
  - Financial Calculation Error Rate: **0.0%**
  - Repayment Reconciliation Rate: **100.0%**
  - Referential Integrity Rate: **100.0%**
  - Prohibited Features Evaluated: **0** (Fair Lending Pass)
- **Anomaly Detection Performance**:
  - Precision: **100.00%**
  - Recall: **100.00%**
  - F1 Score: **1.0000**
- **Reproducibility**: 14/14 CSV files match SHA-256 hashes identically across consecutive runs under seed `20261022`.
- **Full Benchmark Throughput**: 10,000 applicants, 6,000 applications, and 273,645 records generated in 27.32s (0.68 ms/app).
