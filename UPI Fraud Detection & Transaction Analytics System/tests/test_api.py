"""
Integration Tests for Flask REST API Endpoints
"""
import os
import sys
import json
import pytest

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    """Tests GET /api/health."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["models_ready"] is True

def test_stats_endpoint(client):
    """Tests GET /api/stats."""
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    kpis = data["kpis"]
    assert kpis["total_transactions"] >= 10000
    assert "fraud_percentage" in kpis
    assert "risk_distribution" in data
    assert "daily_trends" in data

def test_transactions_endpoint_and_filters(client):
    """Tests GET /api/transactions with filtering and pagination."""
    response = client.get("/api/transactions?limit=10&risk_level=High")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert len(data["transactions"]) <= 10
    for tx in data["transactions"]:
        assert tx["risk_level"] == "High"

def test_analyze_valid_transaction(client):
    """Tests POST /api/analyze with valid high-risk payload."""
    payload = {
        "sender_id": "U1023",
        "receiver_id": "R2045",
        "amount": 75000.0,
        "merchant_category": "Financial Services",
        "transaction_type": "P2M",
        "location": "Indore",
        "device_type": "Android",
        "upi_channel": "PhonePe",
        "timestamp": "2026-09-29T02:15:00"
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert "transaction_id" in data
    assert 0.0 <= data["risk_score"] <= 100.0
    assert data["risk_level"] in ["Low", "Medium", "High", "Critical"]
    assert isinstance(data["reasons"], list)
    assert len(data["reasons"]) > 0

def test_analyze_invalid_payload(client):
    """Tests POST /api/analyze rejection of malformed or invalid inputs."""
    # Negative amount
    res = client.post("/api/analyze", json={"sender_id": "U1001", "receiver_id": "R2001", "amount": -50.0})
    assert res.status_code == 422
    assert "greater than 0" in res.get_json()["message"]

    # Missing receiver_id
    res = client.post("/api/analyze", json={"sender_id": "U1001", "amount": 500.0})
    assert res.status_code == 422
    assert "receiver_id" in res.get_json()["message"]

def test_simulate_endpoint(client):
    """Tests POST /api/simulate for both Normal and High Amount Fraud."""
    # Test normal simulation
    res_norm = client.post("/api/simulate", json={"scenario": "Normal"})
    assert res_norm.status_code == 200
    data_norm = res_norm.get_json()
    assert data_norm["simulated_scenario"] == "Normal"
    assert data_norm["analysis"]["risk_level"] in ["Low", "Medium"]

    # Test High Amount Fraud simulation
    res_fraud = client.post("/api/simulate", json={"scenario": "High Amount Fraud"})
    assert res_fraud.status_code == 200
    data_fraud = res_fraud.get_json()
    assert data_fraud["simulated_scenario"] == "High Amount Fraud"
    assert data_fraud["analysis"]["risk_score"] >= 60.0

def test_alerts_endpoint(client):
    """Tests GET /api/alerts and POST /api/alerts/<id>/status."""
    res = client.get("/api/alerts?limit=5")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    if len(data["alerts"]) > 0:
        alert_id = data["alerts"][0]["alert_id"]
        # Update status
        update_res = client.post(f"/api/alerts/{alert_id}/status", json={"status": "Reviewing", "notes": "Investigating user profile"})
        assert update_res.status_code == 200
        assert update_res.get_json()["alert"]["status"] == "Reviewing"
