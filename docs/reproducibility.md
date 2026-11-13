# Reproducibility Guide & Seed Verification

## 1. Reproducibility Mandate

To satisfy banking compliance and scientific benchmarking, every synthetic record, calculated metric, decision trace, and anomaly injection is bit-for-bit deterministic under the fixed global seed:

$$\text{SEED} = 20261022$$

Full data provenance, generator configuration, transformation rules, and license terms are formally documented in `data/source_manifest.json`.

---

## 2. Verification Protocol

The verification script (`scripts/test_reproducibility.py`):
1. Executes Run 1 with seed `20261022`.
2. Exports all 14 CSV files into `data/reproducibility/run1/`.
3. Executes Run 2 with seed `20261022`.
4. Exports all 14 CSV files into `data/reproducibility/run2/`.
5. Computes cryptographic SHA-256 hashes for all 14 files and asserts:
   $$\text{Hash}(\text{Run1}[f]) == \text{Hash}(\text{Run2}[f]) \quad \forall f \in \text{Datasets}$$
6. Saves validation outcomes to `reports/reproducibility_report.json`.

---

## 3. How to Execute Reproducibility Testing

```bash
python scripts/test_reproducibility.py
```

### Verified Output Across 14 Datasets:
```
================================================================================
RUNNING REPRODUCIBILITY TEST SUITE
Seed: 20261022 | Profile: starter
================================================================================
  [PASS] affordability_checks.csv: e09897ade7e7... == e09897ade7e7...
  [PASS] applicants.csv: 25ca8f807063... == 25ca8f807063...
  [PASS] application_status_history.csv: 98be5b5928fa... == 98be5b5928fa...
  [PASS] credit_facilities.csv: bf8fc71b09d1... == bf8fc71b09d1...
  [PASS] credit_profiles.csv: 77e0283d32cc... == 77e0283d32cc...
  [PASS] decisions.csv: 62339b78f9be... == 62339b78f9be...
  [PASS] disbursements.csv: ae3e782c1925... == ae3e782c1925...
  [PASS] documents.csv: af043df1f708... == af043df1f708...
  [PASS] employments.csv: 6bd8636929e6... == 6bd8636929e6...
  [PASS] ground_truth.csv: 71ec35f75e5e... == 71ec35f75e5e...
  [PASS] income_records.csv: d31abcba6f35... == d31abcba6f35...
  [PASS] loan_applications.csv: b79121615a5e... == b79121615a5e...
  [PASS] loan_products.csv: cebc17440973... == cebc17440973...
  [PASS] repayment_schedules.csv: 63578f85d505... == 63578f85d505...

================================================================================
REPRODUCIBILITY VERIFICATION: 100% PASSED
Report written to reports/reproducibility_report.json
================================================================================
```
