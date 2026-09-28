"""
Fraud Risk Scoring Engine
Combines statistical IQR, ML Isolation Forest, and rolling Time Series detection
into a normalized 0-100 fraud risk score, risk level, and operational recommendation.
"""
import os
import sys
import pandas as pd
import numpy as np

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config
from src.explainability import generate_transaction_explanation

class RiskEngine:
    def __init__(
        self,
        iqr_weight=config.IQR_WEIGHT,
        isolation_weight=config.ISOLATION_WEIGHT,
        time_series_weight=config.TIME_SERIES_WEIGHT,
        thresholds=config.RISK_THRESHOLDS,
        recommendations=config.RECOMMENDATIONS
    ):
        self.iqr_weight = iqr_weight
        self.isolation_weight = isolation_weight
        self.time_series_weight = time_series_weight
        self.thresholds = thresholds
        self.recommendations = recommendations

    def get_risk_level(self, score):
        """
        Maps a 0-100 risk score to Low, Medium, High, or Critical risk tier.
        """
        for level, (low, high) in self.thresholds.items():
            if low <= score <= high:
                return level
        return "Critical" if score > 100 else "Low"

    def calculate_score(self, iqr_score, isolation_score, time_series_score, detectors_flagged_count=0, risk_signals_count=0):
        """
        Computes weighted score with non-linear compound penalty for multi-detector consensus.
        """
        raw_weighted = (
            (self.iqr_weight * iqr_score) +
            (self.isolation_weight * isolation_score) +
            (self.time_series_weight * time_series_score)
        )

        # Multi-detector consensus boost:
        # If multiple independent techniques corroborate the anomaly, confidence increases significantly.
        boost = 0.0
        if detectors_flagged_count == 3:
            boost = 15.0
        elif detectors_flagged_count == 2:
            boost = 8.0

        if risk_signals_count >= 3:
            boost += 5.0

        final_score = float(np.clip(raw_weighted + boost, 0.0, 100.0))
        return round(final_score, 1)

    def evaluate_single_transaction(
        self,
        tx_dict,
        iqr_anomaly,
        iqr_score,
        iqr_breaches,
        isolation_pred,
        isolation_score,
        time_series_anomaly,
        time_series_score,
        ts_details=None
    ):
        """
        Evaluates full anomaly consensus for a single transaction.
        """
        flagged_count = int(iqr_anomaly) + int(isolation_pred) + int(time_series_anomaly)
        risk_signals = int(tx_dict.get("risk_signals_count", 0))

        risk_score = self.calculate_score(
            iqr_score=iqr_score,
            isolation_score=isolation_score,
            time_series_score=time_series_score,
            detectors_flagged_count=flagged_count,
            risk_signals_count=risk_signals
        )

        risk_level = self.get_risk_level(risk_score)
        recommendation = self.recommendations.get(risk_level, "Review transaction.")

        # Determine detection methods summary label
        active_methods = []
        if iqr_anomaly:
            active_methods.append("IQR")
        if isolation_pred:
            active_methods.append("Isolation Forest")
        if time_series_anomaly:
            active_methods.append("Time Series")

        if len(active_methods) == 0:
            detection_method_label = "None"
        elif len(active_methods) == 1:
            detection_method_label = active_methods[0]
        else:
            detection_method_label = " + ".join(active_methods)

        # Final anomaly flag: High/Critical or multi-detector consensus
        final_anomaly_flag = 1 if (risk_score >= 60.0 or flagged_count >= 2) else 0

        # Generate explainability
        reasons, factor_tags = generate_transaction_explanation(
            tx_dict=tx_dict,
            iqr_breaches=iqr_breaches,
            ts_details=ts_details,
            isolation_pred=isolation_pred
        )

        return {
            "fraud_risk_score": risk_score,
            "risk_level": risk_level,
            "final_anomaly_flag": final_anomaly_flag,
            "detectors_flagged_count": flagged_count,
            "detection_method": detection_method_label,
            "recommendation": recommendation,
            "reasons": reasons,
            "factor_tags": factor_tags,
            "detector_scores": {
                "iqr": {
                    "score": iqr_score,
                    "anomaly": bool(iqr_anomaly),
                    "breaches": iqr_breaches
                },
                "isolation_forest": {
                    "score": isolation_score,
                    "anomaly": bool(isolation_pred)
                },
                "time_series": {
                    "score": time_series_score,
                    "anomaly": bool(time_series_anomaly),
                    "details": ts_details
                }
            }
        }

    def evaluate_batch(self, df):
        """
        Evaluates the full batch DataFrame that has been annotated with:
        iqr_anomaly, iqr_score
        isolation_prediction, isolation_score
        time_series_anomaly, time_series_score
        """
        df = df.copy()
        n = len(df)
        
        risk_scores = np.zeros(n, dtype=float)
        risk_levels = []
        final_anomalies = np.zeros(n, dtype=int)
        flagged_counts = np.zeros(n, dtype=int)
        detection_methods = []

        for i, row in df.iterrows():
            iqr_a = int(row.get("iqr_anomaly", 0))
            iqr_s = float(row.get("iqr_score", 0.0))
            iso_a = int(row.get("isolation_prediction", 0))
            iso_s = float(row.get("isolation_score", 0.0))
            ts_a = int(row.get("time_series_anomaly", 0))
            ts_s = float(row.get("time_series_score", 0.0))
            r_sigs = int(row.get("risk_signals_count", 0))

            f_count = iqr_a + iso_a + ts_a
            score = self.calculate_score(iqr_s, iso_s, ts_s, f_count, r_sigs)
            level = self.get_risk_level(score)
            final_anom = 1 if (score >= 60.0 or f_count >= 2) else 0

            methods = []
            if iqr_a:
                methods.append("IQR")
            if iso_a:
                methods.append("Isolation Forest")
            if ts_a:
                methods.append("Time Series")
            method_str = " + ".join(methods) if methods else "None"

            risk_scores[i] = score
            risk_levels.append(level)
            final_anomalies[i] = final_anom
            flagged_counts[i] = f_count
            detection_methods.append(method_str)

        df["fraud_risk_score"] = risk_scores
        df["risk_level"] = risk_levels
        df["final_anomaly_flag"] = final_anomalies
        df["detectors_flagged_count"] = flagged_counts
        df["detection_method"] = detection_methods

        return df

if __name__ == "__main__":
    from src.iqr_detector import IQRAnomalyDetector
    from src.isolation_forest import UPIIsolationForestDetector
    from src.time_series_detector import TimeSeriesAnomalyDetector

    print("Running end-to-end Risk Engine on processed dataset...")
    df = pd.read_csv(config.PROCESSED_DATA_PATH)

    iqr_det = IQRAnomalyDetector().load()
    df = iqr_det.predict_batch(df)

    iso_det = UPIIsolationForestDetector().load()
    df = iso_det.predict_batch(df)

    ts_det = TimeSeriesAnomalyDetector().load()
    df = ts_det.predict_batch(df)

    engine = RiskEngine()
    df = engine.evaluate_batch(df)

    print("\nRisk Level Distribution:")
    print(df["risk_level"].value_counts())
    print("\nFinal Anomaly Flag Count:")
    print(df["final_anomaly_flag"].value_counts())
    print("\nMean Fraud Risk Score by Ground Truth:")
    print(df.groupby("ground_truth_fraud")["fraud_risk_score"].mean())
