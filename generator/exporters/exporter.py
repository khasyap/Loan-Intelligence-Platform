"""
Multi-Format Exporters: Exports all domain datasets into validated CSV, JSON and SQL files.
Generates checksum manifests to ensure data integrity and reproducibility.
"""

import os
import csv
import json
import hashlib
from typing import List, Dict, Any

def compute_file_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def export_to_csv(data: List[Dict[str, Any]], filepath: str):
    if not data:
        return
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    fieldnames = list(data[0].keys())
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            # Serialize complex structures to string
            clean_row = {}
            for k, v in row.items():
                if isinstance(v, (list, dict)):
                    clean_row[k] = json.dumps(v)
                else:
                    clean_row[k] = str(v) if v is not None else ""
            writer.writerow(clean_row)


def export_to_json(data: List[Dict[str, Any]], filepath: str):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def export_to_sql_insert(data: List[Dict[str, Any]], table_name: str, filepath: str):
    if not data:
        return
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    fieldnames = list(data[0].keys())
    cols = ", ".join(fieldnames)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"-- SQL Seed Script for {table_name}\n")
        f.write(f"-- Total rows: {len(data)}\n\n")
        for row in data:
            vals = []
            for k in fieldnames:
                v = row[k]
                if v is None:
                    vals.append("NULL")
                elif isinstance(v, (int, float)):
                    vals.append(str(v))
                elif isinstance(v, (list, dict)):
                    escaped = json.dumps(v).replace("'", "''")
                    vals.append(f"'{escaped}'")
                else:
                    escaped = str(v).replace("'", "''")
                    vals.append(f"'{escaped}'")
            line = f"INSERT INTO {table_name} ({cols}) VALUES ({', '.join(vals)});\n"
            f.write(line)


def export_all_datasets(datasets: Dict[str, List[Dict[str, Any]]], base_dir: str = "data") -> Dict[str, Any]:
    csv_dir = os.path.join(base_dir, "exports", "csv")
    json_dir = os.path.join(base_dir, "exports", "json")
    sql_dir = os.path.join(base_dir, "exports", "sql")

    manifest = {"files": [], "total_records": 0}

    for name, records in datasets.items():
        if name == "ground_truth":
            # Segregated ground truth storage
            gt_csv = os.path.join(base_dir, "ground_truth.csv")
            gt_json = os.path.join(base_dir, "ground_truth.json")
            export_to_csv(records, gt_csv)
            export_to_json(records, gt_json)
            manifest["files"].append({
                "table": name,
                "csv_path": gt_csv,
                "csv_sha256": compute_file_sha256(gt_csv),
                "record_count": len(records)
            })
            continue

        c_path = os.path.join(csv_dir, f"{name}.csv")
        j_path = os.path.join(json_dir, f"{name}.json")
        s_path = os.path.join(sql_dir, f"{name}.sql")

        export_to_csv(records, c_path)
        export_to_json(records, j_path)
        export_to_sql_insert(records, name, s_path)

        manifest["total_records"] += len(records)
        manifest["files"].append({
            "table": name,
            "csv_path": c_path,
            "csv_sha256": compute_file_sha256(c_path),
            "record_count": len(records)
        })

    # Save manifest
    manifest_path = os.path.join(base_dir, "exports", "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest

