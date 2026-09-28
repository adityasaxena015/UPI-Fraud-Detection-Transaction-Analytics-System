"""
IQR (Interquartile Range) Statistical Anomaly Detector
Calculates quartile boundaries and flags extreme statistical outliers
for both batch historical data and single incoming transactions.
"""
import os
import sys
import json
import pandas as pd
import numpy as np

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

class IQRAnomalyDetector:
    def __init__(self, multiplier=config.IQR_MULTIPLIER, features=config.IQR_FEATURES):
        self.multiplier = multiplier
        self.features = features
        self.bounds = {}

    def fit(self, df):
        """
        Fits Q1, Q3, and IQR bounds on the training dataset.
        """
        for feature in self.features:
            if feature not in df.columns:
                continue
            series = pd.to_numeric(df[feature], errors="coerce").dropna()
            q1 = float(np.percentile(series, 25))
            q3 = float(np.percentile(series, 75))
            iqr = q3 - q1
            effective_iqr = max(iqr, 1.0)
            lower_bound = max(0.0, float(q1 - self.multiplier * effective_iqr))
            upper_bound = float(q3 + self.multiplier * effective_iqr)

            # Apply domain-sensible bounds for discrete count features
            if feature == "transactions_last_hour":
                upper_bound = max(upper_bound, 3.0)
            elif feature == "transactions_last_24h":
                upper_bound = max(upper_bound, 5.0)
            elif feature == "recipient_transaction_count":
                upper_bound = max(upper_bound, 3.0)
            
            self.bounds[feature] = {
                "q1": round(q1, 3),
                "q3": round(q3, 3),
                "iqr": round(iqr, 3),
                "lower_bound": round(lower_bound, 3),
                "upper_bound": round(upper_bound, 3)
            }
        return self

    def save(self, filepath=config.IQR_METADATA_PATH):
        """
        Saves computed bounds to a JSON file.
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump({
                "multiplier": self.multiplier,
                "features": self.features,
                "bounds": self.bounds
            }, f, indent=2)
        print(f"IQR bounds saved to {filepath}")

    def load(self, filepath=config.IQR_METADATA_PATH):
        """
        Loads precomputed bounds from JSON file.
        """
        with open(filepath, "r") as f:
            data = json.load(f)
            self.multiplier = data["multiplier"]
            self.features = data["features"]
            self.bounds = data["bounds"]
        return self

    def detect_single(self, tx_dict):
        """
        Evaluates a single transaction against fitted IQR bounds.
        Returns:
            is_anomaly (int 0 or 1)
            iqr_score (float 0 to 100)
            flagged_features (dict with details of breached boundaries)
        """
        breaches = {}
        total_severity = 0.0

        for feature in self.features:
            if feature not in self.bounds:
                continue
            val = float(tx_dict.get(feature, 0.0))
            f_meta = self.bounds[feature]
            ub = f_meta["upper_bound"]
            lb = f_meta["lower_bound"]
            iqr_val = max(f_meta["iqr"], 1.0)

            # UPI fraud outliers are predominantly positive spikes (amount, rate, recipient count)
            if val > ub:
                excess = val - ub
                severity = excess / iqr_val
                breaches[feature] = {
                    "value": round(val, 2),
                    "upper_bound": ub,
                    "excess": round(excess, 2),
                    "multiplier_over_iqr": round(severity, 2)
                }
                total_severity += severity

        is_anomaly = 1 if len(breaches) > 0 else 0
        
        # Normalize total severity into a smooth 0-100 score
        # A severity of 4+ translates to high IQR score
        iqr_score = float(np.clip((1 - np.exp(-0.45 * total_severity)) * 100, 0.0, 100.0))
        if is_anomaly and iqr_score < 30.0:
            iqr_score = 35.0  # minimum threshold if boundary breached

        return is_anomaly, round(iqr_score, 1), breaches

    def predict_batch(self, df):
        """
        Applies IQR detection to a DataFrame.
        Adds columns:
            iqr_anomaly (0 or 1)
            iqr_score (0.0 to 100.0)
            iqr_breach_count (int)
        """
        df = df.copy()
        n = len(df)
        is_anom_arr = np.zeros(n, dtype=int)
        score_arr = np.zeros(n, dtype=float)
        breach_count_arr = np.zeros(n, dtype=int)

        for i, row in df.iterrows():
            row_dict = row.to_dict()
            anom, score, breaches = self.detect_single(row_dict)
            is_anom_arr[i] = anom
            score_arr[i] = score
            breach_count_arr[i] = len(breaches)

        df["iqr_anomaly"] = is_anom_arr
        df["iqr_score"] = score_arr
        df["iqr_breach_count"] = breach_count_arr
        return df

if __name__ == "__main__":
    df = pd.read_csv(config.PROCESSED_DATA_PATH)
    detector = IQRAnomalyDetector()
    detector.fit(df)
    detector.save()
    
    df_eval = detector.predict_batch(df)
    print(f"IQR Detection completed:")
    print(f"Anomalies flagged: {df_eval['iqr_anomaly'].sum()} / {len(df_eval)}")
    print(f"Average IQR score for flagged: {df_eval[df_eval['iqr_anomaly']==1]['iqr_score'].mean():.2f}")
