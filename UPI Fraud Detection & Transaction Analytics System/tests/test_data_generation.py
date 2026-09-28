"""
Unit Tests for Synthetic UPI Dataset Generation
"""
import os
import sys
import pandas as pd
import pytest

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

@pytest.fixture(scope="module")
def raw_dataset():
    if not os.path.exists(config.RAW_DATA_PATH):
        pytest.fail(f"Raw dataset file missing at {config.RAW_DATA_PATH}")
    return pd.read_csv(config.RAW_DATA_PATH)

def test_dataset_size(raw_dataset):
    """Verifies that the dataset contains exactly 10,000 transactions."""
    assert len(raw_dataset) == 10000, f"Expected 10,000 transactions, found {len(raw_dataset)}"

def test_required_columns_exist(raw_dataset):
    """Verifies that all 24 required fields exist in the generated dataset."""
    required_columns = [
        "transaction_id", "timestamp", "sender_id", "receiver_id",
        "amount", "merchant_category", "transaction_type", "location",
        "device_type", "upi_channel", "hour_of_day", "day_of_week",
        "historical_avg_amount", "historical_transaction_count",
        "time_since_last_transaction", "recipient_transaction_count",
        "device_changed", "location_changed", "amount_deviation",
        "transactions_last_hour", "transactions_last_24h", "fraud_pattern",
        "ground_truth_fraud", "anomaly_flag"
    ]
    for col in required_columns:
        assert col in raw_dataset.columns, f"Required column '{col}' is missing from raw dataset"

def test_no_duplicate_transaction_ids(raw_dataset):
    """Verifies there are no duplicate transaction IDs."""
    duplicates = raw_dataset["transaction_id"].duplicated().sum()
    assert duplicates == 0, f"Found {duplicates} duplicate transaction IDs"

def test_fraud_scenarios_simulated(raw_dataset):
    """Verifies that all 8 fraud scenarios are represented in the dataset."""
    expected_scenarios = [
        "High Amount Fraud",
        "Transaction Burst",
        "Repeated Recipient",
        "Unusual Time",
        "Device Change",
        "Location Change",
        "Spending Burst",
        "Multiple Signals"
    ]
    unique_patterns = set(raw_dataset["fraud_pattern"].unique())
    for scenario in expected_scenarios:
        assert scenario in unique_patterns, f"Scenario '{scenario}' missing from generated patterns"

def test_valid_numerical_ranges(raw_dataset):
    """Verifies that transaction amounts and rates are strictly positive."""
    assert (raw_dataset["amount"] > 0).all(), "Found non-positive transaction amounts"
    assert (raw_dataset["historical_avg_amount"] > 0).all(), "Found non-positive historical averages"
    assert (raw_dataset["amount_deviation"] > 0).all(), "Found non-positive amount deviations"
