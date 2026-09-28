"""
Isolation Forest Machine Learning Anomaly Detector
Trains an unsupervised IsolationForest model using Scikit-Learn to detect
multivariate behavioral anomalies across UPI transactions.
"""
import os
import sys
import json
from datetime import datetime
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

class UPIIsolationForestDetector:
    def __init__(self, contamination=config.ISOLATION_CONTAMINATION, features=config.ISOLATION_FEATURES):
        self.contamination = contamination
        self.features = features
        self.model = None
        self.scaler = None
        self.metadata = {}

    def fit(self, df):
        """
        Trains the Isolation Forest model on feature matrix without ground truth labels.
        """
        X = df[self.features].copy()
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Initialize and train Isolation Forest
        self.model = IsolationForest(
            n_estimators=150,
            max_samples="auto",
            contamination=self.contamination,
            random_state=config.RANDOM_SEED,
            n_jobs=-1
        )
        self.model.fit(X_scaled)
        
        # Compute baseline decision function distribution for calibrated score scaling
        decision_scores = self.model.decision_function(X_scaled)
        self.metadata = {
            "model_type": "IsolationForest",
            "n_estimators": 150,
            "contamination": self.contamination,
            "features": self.features,
            "trained_at": datetime.now().isoformat(),
            "sample_count": len(df),
            "score_min": float(np.min(decision_scores)),
            "score_max": float(np.max(decision_scores)),
            "score_median": float(np.median(decision_scores)),
            "score_q10": float(np.percentile(decision_scores, 10))
        }
        return self

    def save(self, model_path=config.MODEL_PATH, scaler_path=config.SCALER_PATH, metadata_path=config.MODEL_METADATA_PATH):
        """
        Saves trained model, scaler, and metadata to disk.
        """
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)
        
        with open(metadata_path, "w") as f:
            json.dump(self.metadata, f, indent=2)
        print(f"Model saved to {model_path}")
        print(f"Scaler saved to {scaler_path}")
        print(f"Metadata saved to {metadata_path}")

    def load(self, model_path=config.MODEL_PATH, scaler_path=config.SCALER_PATH, metadata_path=config.MODEL_METADATA_PATH):
        """
        Loads pre-trained model and scaler from disk.
        """
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                self.metadata = json.load(f)
        return self

    def _convert_decision_to_risk_score(self, decision_scores):
        """
        Converts sklearn decision_function outputs into an interpretable [0, 100] risk score.
        decision_function < 0 is an outlier (high anomaly risk).
        """
        # Sklearn: negative values are outliers, positive are normal
        # Typical range is approx -0.35 to +0.25
        # We invert so negative decision yields high risk (70-100) and positive yields low risk (0-30)
        # Using a sigmoid-like logistic transformation
        # z = -12 * decision_function gives centered probability around boundary 0
        z = -14.0 * decision_scores
        prob = 1.0 / (1.0 + np.exp(-z))
        risk_score = prob * 100.0
        return np.clip(risk_score, 0.0, 100.0)

    def predict_single(self, tx_dict):
        """
        Predicts anomaly status and risk score for a single transaction dict.
        Returns:
            isolation_prediction (0 or 1)
            isolation_score (0.0 to 100.0)
            raw_decision (float)
        """
        vals = [float(tx_dict.get(f, 0.0)) for f in self.features]
        X = pd.DataFrame([[float(tx_dict.get(f, 0.0)) for f in self.features]], columns=self.features)
        X_scaled = self.scaler.transform(X)
        
        # sklearn predict: 1 is inlier, -1 is outlier
        raw_pred = self.model.predict(X_scaled)[0]
        isolation_pred = 1 if raw_pred == -1 else 0
        
        raw_decision = float(self.model.decision_function(X_scaled)[0])
        isolation_score = float(self._convert_decision_to_risk_score(np.array([raw_decision]))[0])
        
        return isolation_pred, round(isolation_score, 1), round(raw_decision, 4)

    def predict_batch(self, df):
        """
        Predicts on a batch DataFrame.
        Adds columns:
            isolation_prediction (0 or 1)
            isolation_score (0.0 to 100.0)
            isolation_raw_decision (float)
        """
        df = df.copy()
        X = df[self.features].copy()
        X_scaled = self.scaler.transform(X)
        
        preds = self.model.predict(X_scaled)
        decisions = self.model.decision_function(X_scaled)
        
        df["isolation_prediction"] = np.where(preds == -1, 1, 0)
        df["isolation_raw_decision"] = np.round(decisions, 4)
        df["isolation_score"] = np.round(self._convert_decision_to_risk_score(decisions), 1)
        return df

if __name__ == "__main__":
    df = pd.read_csv(config.PROCESSED_DATA_PATH)
    print("Training Isolation Forest on 10,000 transactions...")
    detector = UPIIsolationForestDetector()
    detector.fit(df)
    detector.save()
    
    df_eval = detector.predict_batch(df)
    anom_count = df_eval["isolation_prediction"].sum()
    print(f"Isolation Forest predictions complete:")
    print(f"Flagged anomalies: {anom_count} / {len(df_eval)} ({anom_count / len(df_eval) * 100:.2f}%)")
    print(f"Mean score for anomalies: {df_eval[df_eval['isolation_prediction'] == 1]['isolation_score'].mean():.2f}")
    print(f"Mean score for normal: {df_eval[df_eval['isolation_prediction'] == 0]['isolation_score'].mean():.2f}")
