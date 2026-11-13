import os
import json
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from backend.app.services.security import require_role

router = APIRouter(prefix="/system", tags=["System Operations & Audits"])

@router.get("/manifest", response_model=Dict[str, Any])
def get_source_manifest():
    """Retrieve official synthetic data provenance and open license manifest."""
    manifest_path = "data/source_manifest.json"
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Source manifest not found")

@router.get("/validation", response_model=Dict[str, Any])
def get_validation_summary():
    """Retrieve automated structural, relational, lifecycle, and arithmetic validation results."""
    val_path = "reports/validation_summary.json"
    if os.path.exists(val_path):
        with open(val_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Validation summary not yet generated")

@router.get("/comprehensive-evaluation", response_model=Dict[str, Any])
def get_comprehensive_evaluation():
    """Retrieve holistic compliance, math accuracy, reconciliation, and turnaround metrics."""
    comp_path = "reports/comprehensive_evaluation.json"
    if os.path.exists(comp_path):
        with open(comp_path, "r", encoding="utf-8") as f:
            return json.load(f)
    # If not yet generated, fallback to anomaly evaluation
    anom_path = "reports/anomaly_evaluation.json"
    if os.path.exists(anom_path):
        with open(anom_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Evaluation reports not yet generated")

@router.get("/exports/manifest", response_model=Dict[str, Any])
def get_exports_manifest():
    """Retrieve exported dataset file checksums, record counts, and paths."""
    manifest_path = "data/exports/manifest.json"
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Exports manifest not found")

