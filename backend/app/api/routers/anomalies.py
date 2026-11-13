import os
import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from backend.app.database.connection import get_db
from backend.app.models.entities import GroundTruthAnomaly

router = APIRouter(prefix="/anomalies", tags=["Anomalies & Evaluation"])

@router.get("/evaluation", response_model=Dict[str, Any])
def get_anomaly_evaluation():
    """Retrieve precision, recall, F1 score and per-category breakdown of the anomaly detection engine."""
    report_path = "reports/anomaly_evaluation.json"
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"message": "Anomaly evaluation report not yet generated. Run generator first."}


@router.get("/ground-truth", response_model=List[Dict[str, Any]])
def get_ground_truth(db: Session = Depends(get_db)):
    """Retrieve isolated ground truth labels for auditing and research."""
    records = db.query(GroundTruthAnomaly).all()
    return [
        {
            "anomaly_id": g.anomaly_id,
            "entity_name": g.entity_name,
            "record_id": g.record_id,
            "issue_type": g.issue_type,
            "severity": g.severity,
            "expected_decision": g.expected_decision,
            "explanation": g.explanation
        } for g in records
    ]

