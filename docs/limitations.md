# Platform Scope, Assumptions & Limitations

## 1. Synthetic Data & Provenance
- **100% Synthetic Identity**: All applicants, employers, contact numbers, and identification numbers are generated pseudorandomly using Faker and deterministic seeds (`20261022`). No real consumer personally identifiable information (PII) is ingested or utilized.
- **Behavioral Credit Profile Derivation**: Unlike arbitrary Gaussian score assignments, credit scores ($300-900$) are derived deterministically using a documented behavioral scoring formula:
  $$\text{Score} = \text{round}\left(680 + (\text{OnTimePct} - 90.0) \times 11.5 - \max(0, (\text{UtilPct} - 30.0) \times 1.8) - \text{DelinqPenalty} + \text{TenureBonus}\right)$$
  clamped to $[300, 900]$. Score bands (`EXCELLENT`, `VERY_GOOD`, `GOOD`, `FAIR`, `POOR`) directly mirror borrower credit facilities and payment delinquency histories.
- **Controlled Staging Layer**: Deliberately malformed records are isolated in an exception staging layer to protect operational database integrity while allowing full auditability.

## 2. Regulatory & Fair Lending Boundary
- Protected demographic attributes (gender, race, ethnicity, religion, marital status) are strictly omitted from the data model, credit scoring models, and underwriting decision rules to prevent disparate impact and algorithmic bias.

## 3. Financial Assumptions
- Default currency is Indian Rupee (INR, ₹), configurable via `config/generation.yaml`.
- Amortization operates on a monthly standard cycle with reducing balance compounding and penny-rounding reconciliation.
- Disbursements simulate NEFT/IMPS clearing events through state machines rather than interacting with live banking payment rails.
