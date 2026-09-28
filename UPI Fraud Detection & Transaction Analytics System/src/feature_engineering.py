"""
Feature Engineering Module for UPI Fraud Detection
Generates behavioral, temporal, and interaction features for batch data
and real-time API transactions.
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

def extract_calendar_features(df):
    """
    Extracts time-based calendar features from timestamp column.
    """
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df["hour_of_day"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.day_name()
    df["day_of_month"] = df["timestamp"].dt.day
    df["weekend_flag"] = df["timestamp"].dt.weekday.apply(lambda x: 1 if x >= 5 else 0)
    # Unusual hours for financial transactions (midnight to 5 AM)
    df["unusual_hour_flag"] = df["hour_of_day"].apply(lambda h: 1 if 1 <= h <= 5 else 0)
    return df

def compute_derived_ratios(df):
    """
    Computes robust deviation ratios and behavioral boundary flags.
    """
    df = df.copy()
    
    # Safe historical average (prevent zero division)
    safe_hist_avg = df["historical_avg_amount"].apply(lambda x: max(float(x), 50.0))
    df["amount_deviation"] = (df["amount"] / safe_hist_avg).round(3)
    
    # Rapid burst flags
    df["burst_hour_flag"] = df["transactions_last_hour"].apply(lambda x: 1 if x >= 5 else 0)
    df["burst_24h_flag"] = df["transactions_last_24h"].apply(lambda x: 1 if x >= 15 else 0)
    
    # Recipient repetition flag
    df["frequent_recipient_flag"] = df["recipient_transaction_count"].apply(lambda x: 1 if x >= 3 else 0)
    
    # Multiple risk indicator counter
    df["risk_signals_count"] = (
        df["unusual_hour_flag"] +
        df["device_changed"] +
        df["location_changed"] +
        df["burst_hour_flag"] +
        df["frequent_recipient_flag"] +
        (df["amount_deviation"] > 4.0).astype(int)
    )
    
    return df

def apply_feature_engineering_pipeline(df):
    """
    Full feature engineering pipeline for batch DataFrame.
    """
    df = extract_calendar_features(df)
    df = compute_derived_ratios(df)
    return df

def engineer_features_for_single_transaction(tx_dict, user_history=None):
    """
    Enriches a single incoming transaction dict (from API) with behavioral
    and historical features.
    
    user_history can supply:
    - baseline_avg_amount
    - last_timestamp
    - primary_device
    - primary_location
    - transactions_last_hour
    - transactions_last_24h
    - recipient_count_24h
    """
    tx = dict(tx_dict)
    
    # Parse timestamp
    ts_val = tx.get("timestamp")
    if isinstance(ts_val, str):
        try:
            ts = datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
        except Exception:
            ts = datetime.now()
    elif isinstance(ts_val, datetime):
        ts = ts_val
    else:
        ts = datetime.now()
        
    tx["timestamp"] = ts
    amount = float(tx.get("amount", 0.0))
    device = str(tx.get("device_type", "Android"))
    location = str(tx.get("location", "Mumbai"))
    receiver_id = str(tx.get("receiver_id", "R2001"))

    # Compute from user history or baseline fallbacks
    if user_history:
        baseline_avg = float(user_history.get("historical_avg_amount", 1200.0))
        tx_count = int(user_history.get("historical_transaction_count", 5))
        last_ts = user_history.get("last_timestamp")
        primary_dev = user_history.get("primary_device", device)
        primary_loc = user_history.get("primary_location", location)
        
        tx_1h = int(user_history.get("transactions_last_hour", 1))
        tx_24h = int(user_history.get("transactions_last_24h", 1))
        rec_cnt = int(user_history.get("recipient_transaction_count", 1))
        
        if last_ts:
            if isinstance(last_ts, str):
                last_dt = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
            else:
                last_dt = last_ts
            time_diff = max(0.1, (ts - last_dt).total_seconds() / 60.0)
        else:
            time_diff = 120.0
            
        dev_changed = 1 if device != primary_dev else 0
        loc_changed = 1 if location != primary_loc else 0
    else:
        # Default reasonable priors if user has no prior database history
        baseline_avg = float(tx.get("historical_avg_amount", 1500.0))
        tx_count = int(tx.get("historical_transaction_count", 1))
        time_diff = float(tx.get("time_since_last_transaction", 240.0))
        tx_1h = int(tx.get("transactions_last_hour", 1))
        tx_24h = int(tx.get("transactions_last_24h", 1))
        rec_cnt = int(tx.get("recipient_transaction_count", 1))
        dev_changed = int(tx.get("device_changed", 0))
        loc_changed = int(tx.get("location_changed", 0))

    tx["historical_avg_amount"] = baseline_avg
    tx["historical_transaction_count"] = tx_count
    tx["time_since_last_transaction"] = time_diff
    tx["recipient_transaction_count"] = rec_cnt
    tx["device_changed"] = dev_changed
    tx["location_changed"] = loc_changed
    
    safe_avg = max(baseline_avg, 50.0)
    tx["amount_deviation"] = round(amount / safe_avg, 3)
    tx["transactions_last_hour"] = tx_1h
    tx["transactions_last_24h"] = tx_24h
    
    # Calendar features
    tx["hour_of_day"] = ts.hour
    tx["day_of_week"] = ts.strftime("%A")
    tx["day_of_month"] = ts.day
    tx["weekend_flag"] = 1 if ts.weekday() >= 5 else 0
    tx["unusual_hour_flag"] = 1 if 1 <= ts.hour <= 5 else 0
    tx["burst_hour_flag"] = 1 if tx_1h >= 5 else 0
    tx["burst_24h_flag"] = 1 if tx_24h >= 15 else 0
    tx["frequent_recipient_flag"] = 1 if rec_cnt >= 3 else 0
    tx["risk_signals_count"] = (
        tx["unusual_hour_flag"] +
        tx["device_changed"] +
        tx["location_changed"] +
        tx["burst_hour_flag"] +
        tx["frequent_recipient_flag"] +
        (1 if tx["amount_deviation"] > 4.0 else 0)
    )

    return tx
