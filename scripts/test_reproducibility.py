"""
Reproducibility Verification Script: Runs the generator twice with seed 20261022,
computes stable SHA-256 checksums across all datasets, and verifies 100% bit-for-bit determinism.
Generates: reports/reproducibility_report.json
"""

import os
import sys
import json
import hashlib
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from generator.generate import run_pipeline

def hash_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def verify_reproducibility(seed: int = 20261022, profile: str = "starter"):
    print("=" * 80)
    print("RUNNING REPRODUCIBILITY TEST SUITE")
    print(f"Seed: {seed} | Profile: {profile}")
    print("=" * 80)

    run1_dir = "data/reproducibility/run1"
    run2_dir = "data/reproducibility/run2"
    os.makedirs(run1_dir, exist_ok=True)
    os.makedirs(run2_dir, exist_ok=True)

    # Execution 1
    print("\nExecuting Run 1...")
    run_pipeline(profile=profile, custom_seed=seed, seed_db=False)
    # Copy exported CSV files to run1
    for f in os.listdir("data/exports/csv"):
        shutil.copy(os.path.join("data/exports/csv", f), os.path.join(run1_dir, f))
    shutil.copy("data/ground_truth.csv", os.path.join(run1_dir, "ground_truth.csv"))

    # Execution 2
    print("\nExecuting Run 2...")
    run_pipeline(profile=profile, custom_seed=seed, seed_db=False)
    # Copy exported CSV files to run2
    for f in os.listdir("data/exports/csv"):
        shutil.copy(os.path.join("data/exports/csv", f), os.path.join(run2_dir, f))
    shutil.copy("data/ground_truth.csv", os.path.join(run2_dir, "ground_truth.csv"))

    # Compare checksums
    print("\nComparing cryptographic file hashes across executions...")
    comparison = []
    all_matched = True

    files = sorted(os.listdir(run1_dir))
    for fname in files:
        h1 = hash_file(os.path.join(run1_dir, fname))
        h2 = hash_file(os.path.join(run2_dir, fname))
        match = (h1 == h2)
        if not match:
            all_matched = False
        print(f"  [{'PASS' if match else 'FAIL'}] {fname}: {h1[:12]}... == {h2[:12]}...")
        comparison.append({
            "file": fname,
            "run1_sha256": h1,
            "run2_sha256": h2,
            "match": match
        })

    report = {
        "seed": seed,
        "profile": profile,
        "total_files_compared": len(files),
        "all_checksums_matched": all_matched,
        "status": "PASSED" if all_matched else "FAILED",
        "file_comparisons": comparison
    }

    os.makedirs("reports", exist_ok=True)
    with open("reports/reproducibility_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 80)
    print(f"REPRODUCIBILITY VERIFICATION: {'100% PASSED' if all_matched else 'FAILED'}")
    print("Report written to reports/reproducibility_report.json")
    print("=" * 80)

    # Clean up temp run dirs
    shutil.rmtree("data/reproducibility", ignore_errors=True)
    return all_matched

if __name__ == "__main__":
    verify_reproducibility()

