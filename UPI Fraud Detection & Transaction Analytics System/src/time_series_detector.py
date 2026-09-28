"""
Time Series Anomaly Detector
Detects sudden temporal bursts, abnormal transaction frequency spikes,
and volume deviations using rolling statistics and Z-scores.
"""
import os
import sys
import json
import pandas as pd
import numpy as np

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

class TimeSeriesAnomalyDetector:
    def __init__(self, rolling_window=config.TIME_SERIES_ROLLING_WINDOW, z_threshold=config.Z_SCORE_THRESHOLD):
        self.rolling_window = rolling_window
        self.z_threshold = z_threshold
        self.hourly_stats = {}
        self.global_baselines = {}

    def fit_and_analyze_timeline(self, df):
        """
        Aggregates batch dataset by hour, computes rolling statistics,
        and flags hourly volume/amount anomalies.
        """
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Create 1-hour interval bins
        df["hour_bucket"] = df["timestamp"].dt.floor("h")

        # Aggregate metrics per hour
        hourly = df.groupby("hour_bucket").agg(
            tx_count=("transaction_id", "count"),
            total_amount=("amount", "sum"),
            avg_amount=("amount", "mean"),
            unique_senders=("sender_id", "nunique"),
            burst_count=("transactions_last_hour", lambda s: (s >= 5).sum())
        ).reset_index()

        hourly = hourly.sort_values(by="hour_bucket").reset_index(drop=True)

        # Rolling statistics (rolling mean and std)
        w = self.rolling_window
        hourly["count_rolling_mean"] = hourly["tx_count"].rolling(window=w, min_periods=1).mean()
        hourly["count_rolling_std"] = hourly["tx_count"].rolling(window=w, min_periods=1).std().fillna(1.0).replace(0, 1.0)

        hourly["amount_rolling_mean"] = hourly["total_amount"].rolling(window=w, min_periods=1).mean()
        hourly["amount_rolling_std"] = hourly["total_amount"].rolling(window=w, min_periods=1).std().fillna(1.0).replace(0, 1.0)

        # Compute Z-Scores for volume and amount
        hourly["z_score_volume"] = (hourly["tx_count"] - hourly["count_rolling_mean"]) / hourly["count_rolling_std"]
        hourly["z_score_amount"] = (hourly["total_amount"] - hourly["amount_rolling_mean"]) / hourly["amount_rolling_std"]

        # Flag spikes
        hourly["transaction_volume_spike"] = (hourly["z_score_volume"] > self.z_threshold).astype(int)
        hourly["amount_volume_spike"] = (hourly["z_score_amount"] > self.z_threshold).astype(int)
        hourly["hourly_time_series_anomaly"] = (
            (hourly["transaction_volume_spike"] == 1) | (hourly["amount_volume_spike"] == 1)
        ).astype(int)

        # Compute summary global baselines for real-time reference
        self.global_baselines = {
            "mean_hourly_count": float(hourly["tx_count"].mean()),
            "std_hourly_count": float(hourly["tx_count"].std() if len(hourly) > 1 else 5.0),
            "mean_hourly_amount": float(hourly["total_amount"].mean()),
            "std_hourly_amount": float(hourly["total_amount"].std() if len(hourly) > 1 else 10000.0),
            "total_hourly_buckets": len(hourly),
            "anomalous_hours_count": int(hourly["hourly_time_series_anomaly"].sum())
        }

        # Store dictionary for quick hourly lookup
        self.hourly_stats = {
            ts.isoformat(): {
                "tx_count": int(row["tx_count"]),
                "total_amount": float(row["total_amount"]),
                "z_score_volume": round(float(row["z_score_volume"]), 2),
                "z_score_amount": round(float(row["z_score_amount"]), 2),
                "transaction_volume_spike": int(row["transaction_volume_spike"]),
                "amount_volume_spike": int(row["amount_volume_spike"]),
                "time_series_anomaly": int(row["hourly_time_series_anomaly"])
            }
            for ts, row in hourly.set_index("hour_bucket").iterrows()
        }

        return hourly

    def save(self, filepath=config.MODELS_DIR / "time_series_metadata.json"):
        """
        Saves time series baselines and configurations to JSON.
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump({
                "rolling_window": self.rolling_window,
                "z_threshold": self.z_threshold,
                "global_baselines": self.global_baselines
            }, f, indent=2)
        print(f"Time series detector metadata saved to {filepath}")

    def load(self, filepath=config.MODELS_DIR / "time_series_metadata.json"):
        """
        Loads saved metadata.
        """
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                data = json.load(f)
                self.rolling_window = data["rolling_window"]
                self.z_threshold = data["z_threshold"]
                self.global_baselines = data.get("global_baselines", {})
        return self

    def detect_single(self, tx_dict):
        """
        Evaluates a single transaction for temporal burst and velocity anomalies.
        Considers:
        1. High transaction frequency in last 1 hour (>= 5 tx/hr is a severe burst)
        2. High transaction frequency in last 24 hours (>= 12 tx/24h)
        3. Extremely rapid succession (< 3 minutes since prior transaction with high amount)
        4. Unusual time of day (1 AM - 5 AM) combined with volume spike
        
        Returns:
            is_anomaly (int 0 or 1)
            time_series_score (float 0 to 100)
            details (dict of temporal signals)
        """
        tx_1h = int(tx_dict.get("transactions_last_hour", 1))
        tx_24h = int(tx_dict.get("transactions_last_24h", 1))
        time_diff = float(tx_dict.get("time_since_last_transaction", 120.0))
        hour = int(tx_dict.get("hour_of_day", 12))
        amount = float(tx_dict.get("amount", 0.0))

        signals = []
        score = 0.0

        # 1. Immediate burst test
        if tx_1h >= 10:
            signals.append(f"Extreme transaction burst: {tx_1h} transactions within 1 hour")
            score += 65.0
        elif tx_1h >= 5:
            signals.append(f"Elevated frequency: {tx_1h} transactions within 1 hour")
            score += 40.0

        # 2. 24h velocity test
        if tx_24h >= 18:
            signals.append(f"Abnormal daily frequency: {tx_24h} transactions in 24 hours")
            score += 35.0
        elif tx_24h >= 10:
            signals.append(f"High 24h frequency: {tx_24h} transactions in 24 hours")
            score += 15.0

        # 3. Micro-interval burst with high amount (rapid drain attack)
        if time_diff < 5.0 and amount > 5000:
            signals.append(f"Rapid successive transaction: only {time_diff:.1f} mins since prior transaction")
            score += 30.0

        # 4. Off-hours burst
        if (1 <= hour <= 5) and (tx_1h >= 3 or amount > 10000):
            signals.append(f"Unusual nocturnal activity at {hour:02d}:00 with high velocity/amount")
            score += 25.0

        is_anomaly = 1 if (tx_1h >= 5 or score >= 40.0) else 0
        final_score = float(np.clip(score, 0.0, 100.0))

        return is_anomaly, round(final_score, 1), {
            "transaction_volume_spike": 1 if tx_1h >= 5 else 0,
            "amount_volume_spike": 1 if (amount > 30000 and tx_1h >= 2) else 0,
            "signals": signals
        }

    def predict_batch(self, df):
        """
        Applies time series anomaly detection across the batch DataFrame.
        """
        df = df.copy()
        n = len(df)
        ts_anom_arr = np.zeros(n, dtype=int)
        ts_score_arr = np.zeros(n, dtype=float)
        vol_spike_arr = np.zeros(n, dtype=int)
        amt_spike_arr = np.zeros(n, dtype=int)

        for i, row in df.iterrows():
            row_dict = row.to_dict()
            anom, score, details = self.detect_single(row_dict)
            ts_anom_arr[i] = anom
            ts_score_arr[i] = score
            vol_spike_arr[i] = details["transaction_volume_spike"]
            amt_spike_arr[i] = details["amount_volume_spike"]

        df["time_series_anomaly"] = ts_anom_arr
        df["time_series_score"] = ts_score_arr
        df["transaction_volume_spike"] = vol_spike_arr
        df["amount_volume_spike"] = amt_spike_arr
        return df

if __name__ == "__main__":
    df = pd.read_csv(config.PROCESSED_DATA_PATH)
    detector = TimeSeriesAnomalyDetector()
    hourly_df = detector.fit_and_analyze_timeline(df)
    detector.save()
    
    df_eval = detector.predict_batch(df)
    print(f"Time Series Anomaly Detection complete:")
    print(f"Flagged temporal anomalies: {df_eval['time_series_anomaly'].sum()} / {len(df_eval)}")
    print(f"Volume spikes: {df_eval['transaction_volume_spike'].sum()}")
    print(f"Amount volume spikes: {df_eval['amount_volume_spike'].sum()}")
