"""
Data Preprocessing Pipeline for UPI Fraud Detection
Performs data cleaning, validation, scaling, and prepares datasets for modeling.
"""
import os
import sys
import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config
from src.feature_engineering import apply_feature_engineering_pipeline

def clean_and_validate_dataframe(df):
    """
    Cleans raw DataFrame: removes duplicates, imputes missing values,
    and enforces valid financial ranges.
    """
    initial_count = len(df)
    
    # 1. Remove duplicate transaction IDs
    df = df.drop_duplicates(subset=["transaction_id"]).copy()
    
    # 2. Enforce timestamp conversion
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    # 3. Numeric validation
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(500.0)
    df = df[df["amount"] > 0].copy()
    
    numeric_cols = [
        "historical_avg_amount", "historical_transaction_count",
        "time_since_last_transaction", "recipient_transaction_count",
        "amount_deviation", "transactions_last_hour", "transactions_last_24h"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(1.0)
            df[col] = df[col].clip(lower=0)

    # 4. Binary flags
    binary_cols = ["device_changed", "location_changed", "ground_truth_fraud", "anomaly_flag"]
    for col in binary_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)

    # 5. String columns cleanup
    str_cols = ["sender_id", "receiver_id", "merchant_category", "transaction_type", "location", "device_type", "upi_channel", "fraud_pattern"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    print(f"Data cleaning complete: {len(df)} valid records retained (removed {initial_count - len(df)}).")
    return df

def fit_and_save_scaler(df, features=config.ISOLATION_FEATURES, scaler_path=config.SCALER_PATH):
    """
    Fits a StandardScaler on training features and persists it using joblib.
    """
    os.makedirs(os.path.dirname(scaler_path), exist_ok=True)
    scaler = StandardScaler()
    scaler.fit(df[features])
    joblib.dump(scaler, scaler_path)
    print(f"StandardScaler fitted on {features} and saved to {scaler_path}")
    return scaler

def preprocess_and_save(raw_path=config.RAW_DATA_PATH, processed_path=config.PROCESSED_DATA_PATH):
    """
    Full preprocessing execution pipeline.
    """
    print(f"Reading raw data from {raw_path}...")
    df = pd.read_csv(raw_path)
    
    # Clean data
    df = clean_and_validate_dataframe(df)
    
    # Apply feature engineering
    df = apply_feature_engineering_pipeline(df)
    
    # Fit scaler
    fit_and_save_scaler(df)
    
    # Save processed dataset
    os.makedirs(os.path.dirname(processed_path), exist_ok=True)
    df.to_csv(processed_path, index=False)
    print(f"Saved processed dataset ({len(df)} rows) to {processed_path}")
    return df

def validate_single_transaction_input(payload):
    """
    Validates input schema and types for incoming API request.
    Returns (is_valid, error_message, cleaned_dict)
    """
    if not isinstance(payload, dict):
        return False, "Payload must be a JSON object.", None
        
    required_fields = ["sender_id", "receiver_id", "amount"]
    for field in required_fields:
        if field not in payload or payload[field] is None:
            return False, f"Missing required field: '{field}'", None

    try:
        amount = float(payload["amount"])
        if amount <= 0:
            return False, "Transaction amount must be strictly greater than 0.", None
        if amount > 10000000:
            return False, "Transaction amount exceeds system limit (₹1,00,00,000).", None
    except (ValueError, TypeError):
        return False, "Transaction 'amount' must be a valid positive number.", None

    cleaned = dict(payload)
    cleaned["amount"] = round(float(payload["amount"]), 2)
    cleaned["sender_id"] = str(payload["sender_id"]).strip()
    cleaned["receiver_id"] = str(payload["receiver_id"]).strip()
    cleaned["merchant_category"] = str(payload.get("merchant_category", "Personal Transfer")).strip()
    cleaned["transaction_type"] = str(payload.get("transaction_type", "P2P")).strip()
    cleaned["location"] = str(payload.get("location", "Mumbai")).strip()
    cleaned["device_type"] = str(payload.get("device_type", "Android")).strip()
    cleaned["upi_channel"] = str(payload.get("upi_channel", "Google Pay")).strip()
    
    return True, None, cleaned

if __name__ == "__main__":
    preprocess_and_save()
