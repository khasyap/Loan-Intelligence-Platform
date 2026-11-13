"""
Anomaly Evaluation Service: Compares independent anomaly detector outputs
against segregated ground-truth labels.
Computes True Positives, False Positives, False Negatives, Precision, Recall, and F1 Score.
"""

from typing import List, Dict, Any

def evaluate_anomalies(
    ground_truth_records: List[Dict[str, Any]],
    detected_anomalies: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Evaluates detector performance.
    Matches primarily on (record_id, issue_type).
    """
    gt_map = {(gt["record_id"], gt["issue_type"]): gt for gt in ground_truth_records}
    dt_map = {(dt["record_id"], dt["issue_type"]): dt for dt in detected_anomalies}

    tp_keys = set(gt_map.keys()) & set(dt_map.keys())
    fn_keys = set(gt_map.keys()) - set(dt_map.keys())
    fp_keys = set(dt_map.keys()) - set(gt_map.keys())

    tp = len(tp_keys)
    fn = len(fn_keys)
    fp = len(fp_keys)

    precision = (tp / (tp + fp)) if (tp + fp) > 0 else 1.0
    recall = (tp / (tp + fn)) if (tp + fn) > 0 else 1.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    # Per-category evaluation
    categories = [
        "INVALID_TERM",
        "SCHEDULE_RECONCILIATION_FAILURE",
        "DECISION_BEFORE_CHECKS",
        "INCOME_SOURCE_CONFLICT",
        "DUPLICATE_DISBURSEMENT"
    ]

    category_breakdown = {}
    for cat in categories:
        cat_gt = [k for k in gt_map.keys() if k[1] == cat]
        cat_dt = [k for k in dt_map.keys() if k[1] == cat]
        cat_tp = set(cat_gt) & set(cat_dt)
        cat_fn = set(cat_gt) - set(cat_dt)
        cat_fp = set(cat_dt) - set(cat_gt)

        c_tp = len(cat_tp)
        c_fn = len(cat_fn)
        c_fp = len(cat_fp)
        c_prec = (c_tp / (c_tp + c_fp)) if (c_tp + c_fp) > 0 else 1.0
        c_rec = (c_tp / (c_tp + c_fn)) if (c_tp + c_fn) > 0 else 1.0
        c_f1 = (2 * c_prec * c_rec / (c_prec + c_rec)) if (c_prec + c_rec) > 0 else 0.0

        category_breakdown[cat] = {
            "ground_truth_count": len(cat_gt),
            "detected_count": len(cat_dt),
            "true_positives": c_tp,
            "false_negatives": c_fn,
            "false_positives": c_fp,
            "precision": round(c_prec, 4),
            "recall": round(c_rec, 4),
            "f1_score": round(c_f1, 4)
        }

    return {
        "summary": {
            "total_ground_truth": len(ground_truth_records),
            "total_detected": len(detected_anomalies),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4)
        },
        "category_breakdown": category_breakdown
    }

