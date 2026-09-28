"""
Model and System Evaluation Module
Calculates classification metrics (Confusion Matrix, Precision, Recall, F1, ROC-AUC, FPR, FNR)
for individual detectors and the ensemble Risk Engine using synthetic ground truth.
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from sklearn.metrics import (
    confusion_matrix, precision_score, recall_score,
    f1_score, accuracy_score, roc_auc_score, roc_curve
)

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

def compute_detailed_metrics(y_true, y_pred, y_scores=None):
    """
    Computes confusion matrix, precision, recall, F1, accuracy, FPR, FNR, and ROC-AUC.
    """
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()

    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    accuracy = float(accuracy_score(y_true, y_pred))

    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

    auc = None
    if y_scores is not None:
        try:
            auc = float(roc_auc_score(y_true, y_scores))
        except Exception:
            auc = None

    return {
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp)
        },
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "accuracy": round(accuracy, 4),
        "false_positive_rate": round(fpr, 4),
        "false_negative_rate": round(fnr, 4),
        "roc_auc": round(auc, 4) if auc is not None else "N/A"
    }

def run_evaluation(df):
    """
    Evaluates each detector and the ensemble risk engine against ground_truth_fraud.
    """
    y_true = df["ground_truth_fraud"].values

    results = {
        "disclaimer": (
            "CRITICAL NOTE: Anomaly detection in UPI payments is fundamentally an "
            "unsupervised problem. In real banking systems, ground-truth labels are delayed, "
            "sparse, or incomplete. The metrics presented here are evaluated against our controlled "
            "synthetic benchmark (10,000 transactions) for portfolio validation and research only, "
            "and should not be claimed as guaranteed production banking performance."
        ),
        "dataset_summary": {
            "total_samples": len(df),
            "normal_samples": int((y_true == 0).sum()),
            "fraud_samples": int((y_true == 1).sum()),
            "fraud_prevalence": round(float((y_true == 1).mean() * 100), 2)
        },
        "detectors": {}
    }

    # 1. IQR Detector
    if "iqr_anomaly" in df.columns:
        results["detectors"]["IQR"] = compute_detailed_metrics(
            y_true, df["iqr_anomaly"].values, df.get("iqr_score", None)
        )

    # 2. Isolation Forest
    if "isolation_prediction" in df.columns:
        results["detectors"]["Isolation_Forest"] = compute_detailed_metrics(
            y_true, df["isolation_prediction"].values, df.get("isolation_score", None)
        )

    # 3. Time Series Detector
    if "time_series_anomaly" in df.columns:
        results["detectors"]["Time_Series"] = compute_detailed_metrics(
            y_true, df["time_series_anomaly"].values, df.get("time_series_score", None)
        )

    # 4. Ensemble Risk Engine
    if "final_anomaly_flag" in df.columns:
        results["detectors"]["Ensemble_Risk_Engine"] = compute_detailed_metrics(
            y_true, df["final_anomaly_flag"].values, df.get("fraud_risk_score", None)
        )

    # Scenario-wise detection rate
    if "fraud_pattern" in df.columns:
        scenario_breakdown = {}
        fraud_df = df[df["ground_truth_fraud"] == 1]
        for pattern, group in fraud_df.groupby("fraud_pattern"):
            detected_count = int(group["final_anomaly_flag"].sum())
            total = len(group)
            scenario_breakdown[pattern] = {
                "total": total,
                "detected": detected_count,
                "detection_rate": round(detected_count / total * 100, 1),
                "avg_risk_score": round(float(group["fraud_risk_score"].mean()), 1)
            }
        results["scenario_detection_rates"] = scenario_breakdown

    return results

def evaluate_and_save(processed_csv=config.PROCESSED_DATA_PATH, output_json=config.MODELS_DIR / "evaluation_results.json"):
    """
    Loads processed data, runs all detector evaluations, and persists JSON report.
    """
    from src.iqr_detector import IQRAnomalyDetector
    from src.isolation_forest import UPIIsolationForestDetector
    from src.time_series_detector import TimeSeriesAnomalyDetector
    from src.risk_engine import RiskEngine

    df = pd.read_csv(processed_csv)

    # Run predictions
    df = IQRAnomalyDetector().load().predict_batch(df)
    df = UPIIsolationForestDetector().load().predict_batch(df)
    df = TimeSeriesAnomalyDetector().load().predict_batch(df)
    df = RiskEngine().evaluate_batch(df)

    eval_results = run_evaluation(df)

    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w") as f:
        json.dump(eval_results, f, indent=2)
    print(f"Evaluation report successfully saved to {output_json}")

    # Print clean summary table
    print("\n" + "="*70)
    print("UPI FRAUD DETECTION SYSTEM — MODEL BENCHMARK RESULTS")
    print("="*70)
    print(f"{'Detector':<24} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'ROC-AUC':<8}")
    print("-" * 70)
    for name, m in eval_results["detectors"].items():
        auc_str = f"{m['roc_auc']:.4f}" if isinstance(m['roc_auc'], (int, float)) else str(m['roc_auc'])
        print(f"{name:<24} | {m['precision']:<10.4f} | {m['recall']:<10.4f} | {m['f1_score']:<10.4f} | {auc_str:<8}")
    print("="*70)
    
    print("\nSCENARIO DETECTION RATES:")
    for sc, sc_info in eval_results.get("scenario_detection_rates", {}).items():
        print(f"  • {sc:<22}: {sc_info['detected']}/{sc_info['total']} ({sc_info['detection_rate']}%) - Avg Score: {sc_info['avg_risk_score']}")
    print("="*70)

    # Save final enriched DataFrame back to processed CSV so database seeder can ingest all final scores
    df.to_csv(processed_csv, index=False)
    print(f"Updated {processed_csv} with all detector scores and risk predictions.")
    return eval_results

if __name__ == "__main__":
    evaluate_and_save()
