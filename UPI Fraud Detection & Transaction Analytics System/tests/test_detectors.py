"""
Unit Tests for Detection Models (IQR, Isolation Forest, Time Series, Risk Engine)
"""
import os
import sys
import pytest

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config
from src.iqr_detector import IQRAnomalyDetector
from src.isolation_forest import UPIIsolationForestDetector
from src.time_series_detector import TimeSeriesAnomalyDetector
from src.risk_engine import RiskEngine

@pytest.fixture(scope="module")
def loaded_detectors():
    iqr = IQRAnomalyDetector().load(config.IQR_METADATA_PATH)
    iso = UPIIsolationForestDetector().load(
        model_path=config.MODEL_PATH,
        scaler_path=config.SCALER_PATH,
        metadata_path=config.MODEL_METADATA_PATH
    )
    ts = TimeSeriesAnomalyDetector().load(config.MODELS_DIR / "time_series_metadata.json")
    engine = RiskEngine()
    return {"iqr": iqr, "iso": iso, "ts": ts, "engine": engine}

def test_iqr_detector_bounds_and_single(loaded_detectors):
    """Verifies IQR bounds are loaded and correctly flags extreme amounts."""
    iqr = loaded_detectors["iqr"]
    assert "amount" in iqr.bounds
    assert iqr.bounds["amount"]["upper_bound"] > 0

    # Normal transaction: ₹500
    anom_norm, score_norm, _ = iqr.detect_single({
        "amount": 500.0, "amount_deviation": 1.0,
        "transactions_last_hour": 1, "transactions_last_24h": 2,
        "recipient_transaction_count": 1
    })
    assert anom_norm == 0
    assert 0.0 <= score_norm <= 35.0

    # Extreme outlier: ₹95,000 with 60x deviation
    anom_high, score_high, breaches = iqr.detect_single({
        "amount": 95000.0, "amount_deviation": 60.0,
        "transactions_last_hour": 1, "transactions_last_24h": 2,
        "recipient_transaction_count": 1
    })
    assert anom_high == 1
    assert score_high >= 70.0
    assert "amount" in breaches

def test_isolation_forest_prediction(loaded_detectors):
    """Verifies Isolation Forest predictions and calibrated 0-100 risk score."""
    iso = loaded_detectors["iso"]

    # Normal sample
    norm_dict = {
        "amount": 1200.0, "amount_deviation": 1.1,
        "transactions_last_hour": 1, "transactions_last_24h": 2,
        "time_since_last_transaction": 180.0, "recipient_transaction_count": 1,
        "device_changed": 0, "location_changed": 0, "hour_of_day": 14
    }
    pred_norm, score_norm, raw_norm = iso.predict_single(norm_dict)
    assert pred_norm == 0
    assert 0.0 <= score_norm <= 40.0

    # Extreme multivariate anomaly: Midnight, 80k amount, new device, new city, burst
    anom_dict = {
        "amount": 88000.0, "amount_deviation": 50.0,
        "transactions_last_hour": 14, "transactions_last_24h": 22,
        "time_since_last_transaction": 1.5, "recipient_transaction_count": 5,
        "device_changed": 1, "location_changed": 1, "hour_of_day": 2
    }
    pred_anom, score_anom, raw_anom = iso.predict_single(anom_dict)
    assert pred_anom == 1
    assert score_anom >= 75.0

def test_time_series_detector(loaded_detectors):
    """Verifies detection of sudden velocity bursts."""
    ts = loaded_detectors["ts"]
    
    # Burst condition: 12 transactions in 1 hour
    anom, score, details = ts.detect_single({
        "transactions_last_hour": 12,
        "transactions_last_24h": 15,
        "time_since_last_transaction": 1.5,
        "amount": 4000.0,
        "hour_of_day": 15
    })
    assert anom == 1
    assert score >= 60.0
    assert details["transaction_volume_spike"] == 1

def test_risk_engine_score_bounds(loaded_detectors):
    """Verifies that consolidated fraud risk scores strictly stay within [0, 100]."""
    engine = loaded_detectors["engine"]

    # Edge cases
    assert engine.calculate_score(0.0, 0.0, 0.0, 0, 0) == 0.0
    assert engine.calculate_score(100.0, 100.0, 100.0, 3, 5) == 100.0

    # Intermediate score
    score = engine.calculate_score(50.0, 50.0, 50.0, 1, 1)
    assert 0.0 <= score <= 100.0
    
    # Tier mapping
    assert engine.get_risk_level(15.0) == "Low"
    assert engine.get_risk_level(45.0) == "Medium"
    assert engine.get_risk_level(70.0) == "High"
    assert engine.get_risk_level(95.0) == "Critical"
