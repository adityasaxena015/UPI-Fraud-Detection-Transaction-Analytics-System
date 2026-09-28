"""
Unit Tests for Feature Engineering & Preprocessing Logic
"""
import os
import sys
from datetime import datetime
import pandas as pd
import pytest

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config
from src.feature_engineering import (
    extract_calendar_features, compute_derived_ratios,
    engineer_features_for_single_transaction
)
from src.preprocessing import validate_single_transaction_input

def test_calendar_features():
    """Tests temporal feature extraction."""
    sample_df = pd.DataFrame({
        "timestamp": ["2026-09-29 02:30:00", "2026-09-27 15:45:00"] # 27th is Sunday
    })
    enriched = extract_calendar_features(sample_df)
    
    assert enriched["hour_of_day"].iloc[0] == 2
    assert enriched["unusual_hour_flag"].iloc[0] == 1
    assert enriched["unusual_hour_flag"].iloc[1] == 0
    assert enriched["weekend_flag"].iloc[1] == 1

def test_amount_deviation_calculation():
    """Tests correct calculation of amount deviation ratio."""
    sample_df = pd.DataFrame({
        "amount": [50000.0, 1000.0],
        "historical_avg_amount": [1000.0, 1000.0],
        "transactions_last_hour": [1, 1],
        "transactions_last_24h": [1, 1],
        "recipient_transaction_count": [1, 1],
        "unusual_hour_flag": [0, 0],
        "device_changed": [0, 0],
        "location_changed": [0, 0]
    })
    res = compute_derived_ratios(sample_df)
    assert res["amount_deviation"].iloc[0] == 50.0
    assert res["amount_deviation"].iloc[1] == 1.0

def test_single_transaction_feature_engineering():
    """Tests real-time feature derivation for an incoming API dictionary."""
    payload = {
        "sender_id": "U1099",
        "receiver_id": "R2001",
        "amount": 25000.0,
        "device_type": "Android",
        "location": "Mumbai",
        "timestamp": "2026-09-29T03:15:00"
    }
    user_history = {
        "historical_avg_amount": 1000.0,
        "historical_transaction_count": 10,
        "primary_device": "iOS",
        "primary_location": "Delhi",
        "transactions_last_hour": 6,
        "transactions_last_24h": 12,
        "recipient_transaction_count": 4
    }
    enriched = engineer_features_for_single_transaction(payload, user_history=user_history)
    
    assert enriched["amount_deviation"] == 25.0
    assert enriched["device_changed"] == 1
    assert enriched["location_changed"] == 1
    assert enriched["unusual_hour_flag"] == 1
    assert enriched["burst_hour_flag"] == 1
    assert enriched["frequent_recipient_flag"] == 1
    assert enriched["risk_signals_count"] >= 5

def test_input_validation():
    """Tests schema validation and error handling for malformed payloads."""
    # Missing required field
    is_valid, msg, _ = validate_single_transaction_input({"sender_id": "U1001", "amount": 500})
    assert not is_valid
    assert "receiver_id" in msg

    # Negative amount
    is_valid, msg, _ = validate_single_transaction_input({"sender_id": "U1001", "receiver_id": "R2001", "amount": -100})
    assert not is_valid
    assert "greater than 0" in msg

    # Valid payload
    is_valid, msg, cleaned = validate_single_transaction_input({"sender_id": "U1001", "receiver_id": "R2001", "amount": "1250.50"})
    assert is_valid
    assert cleaned["amount"] == 1250.50
