"""
Real-Time UPI Transaction Simulator
Generates realistic normal and suspicious UPI transaction payloads
representing all 8 simulated fraud vectors for live API testing and dashboard demonstration.
"""
import os
import sys
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config
from database.db import SessionFactory, TransactionModel

SCENARIOS = [
    "High Amount Fraud",
    "Transaction Burst",
    "Repeated Recipient",
    "Unusual Time",
    "Device Change",
    "Location Change",
    "Spending Burst",
    "Multiple Signals"
]

def get_random_existing_user():
    """
    Fetches a real sender from the database with their historical profile stats.
    Falls back to a synthetic profile if database is unseeded.
    """
    session = SessionFactory()
    try:
        sample_tx = session.query(TransactionModel).order_by(TransactionModel.id.desc()).first()
        if sample_tx:
            # Pick a random transaction to get a real sender
            random_offset = random.randint(0, min(500, 1000))
            tx = session.query(TransactionModel).offset(random_offset).first()
            if tx:
                return {
                    "sender_id": tx.sender_id,
                    "historical_avg_amount": float(tx.historical_avg_amount),
                    "primary_device": tx.device_type,
                    "primary_location": tx.location,
                    "primary_channel": tx.upi_channel,
                    "receiver_id": tx.receiver_id
                }
    except Exception:
        pass
    finally:
        session.close()

    # Fallback profile
    user_num = random.randint(1001, 1500)
    return {
        "sender_id": f"U{user_num}",
        "historical_avg_amount": 1200.0,
        "primary_device": "Android",
        "primary_location": "Mumbai",
        "primary_channel": "Google Pay",
        "receiver_id": "R2050"
    }

def generate_normal_transaction():
    """
    Generates a benign, normal UPI transaction payload consistent with regular user habits.
    """
    user = get_random_existing_user()
    avg_amt = user["historical_avg_amount"]
    
    # Amount distributed close to normal average (₹100 to 2.2x average)
    amt = max(50.0, float(np.random.normal(avg_amt, avg_amt * 0.25)))
    amt = round(amt, 2)
    
    now = datetime.now()
    # Normal hours (9 AM to 10 PM)
    normal_hour = random.randint(9, 22)
    ts = now.replace(hour=normal_hour, minute=random.randint(0, 59), second=random.randint(0, 59))

    category = random.choices(
        config.MERCHANT_CATEGORIES,
        weights=[0.25, 0.25, 0.10, 0.15, 0.10, 0.05, 0.05, 0.03, 0.01, 0.01],
        k=1
    )[0]

    return {
        "sender_id": user["sender_id"],
        "receiver_id": f"R{random.randint(2001, 2800)}",
        "amount": amt,
        "merchant_category": category,
        "transaction_type": "P2M" if category != "Personal Transfer" else "P2P",
        "location": user["primary_location"],
        "device_type": user["primary_device"],
        "upi_channel": user["primary_channel"],
        "timestamp": ts.isoformat(),
        "historical_avg_amount": avg_amt,
        "historical_transaction_count": random.randint(5, 50),
        "time_since_last_transaction": round(random.uniform(60.0, 720.0), 1),
        "recipient_transaction_count": 1,
        "device_changed": 0,
        "location_changed": 0,
        "transactions_last_hour": 1,
        "transactions_last_24h": random.randint(1, 4),
        "simulated_scenario": "Normal"
    }

def generate_suspicious_transaction(scenario=None):
    """
    Generates an intentionally fraudulent or suspicious transaction payload
    simulating one of the 8 core fraud vectors.
    """
    if not scenario or scenario not in SCENARIOS:
        scenario = random.choice(SCENARIOS)

    user = get_random_existing_user()
    avg_amt = user["historical_avg_amount"]
    now = datetime.now()

    other_devices = [d for d in config.DEVICES if d != user["primary_device"]]
    other_cities = [c for c in config.INDIAN_CITIES if c != user["primary_location"]]

    tx = {
        "sender_id": user["sender_id"],
        "receiver_id": f"R{random.randint(2001, 2800)}",
        "amount": round(float(np.random.normal(avg_amt, avg_amt * 0.2)), 2),
        "merchant_category": "Personal Transfer",
        "transaction_type": "P2P",
        "location": user["primary_location"],
        "device_type": user["primary_device"],
        "upi_channel": user["primary_channel"],
        "timestamp": now.isoformat(),
        "historical_avg_amount": avg_amt,
        "historical_transaction_count": random.randint(8, 60),
        "time_since_last_transaction": round(random.uniform(60.0, 360.0), 1),
        "recipient_transaction_count": 1,
        "device_changed": 0,
        "location_changed": 0,
        "transactions_last_hour": 1,
        "transactions_last_24h": 2,
        "simulated_scenario": scenario
    }

    if scenario == "High Amount Fraud":
        # Sudden 30x - 60x spending spike
        tx["amount"] = round(random.uniform(55000.0, 95000.0), 2)
        tx["merchant_category"] = "Financial Services"
        tx["transaction_type"] = "P2M"

    elif scenario == "Transaction Burst":
        # Sudden flood of 12-16 transactions within the hour
        tx["transactions_last_hour"] = random.randint(12, 18)
        tx["transactions_last_24h"] = tx["transactions_last_hour"] + random.randint(2, 6)
        tx["time_since_last_transaction"] = round(random.uniform(0.5, 2.5), 1)
        tx["amount"] = round(random.uniform(2500.0, 8500.0), 2)

    elif scenario == "Repeated Recipient":
        # 6 rapid transfers targeted at the exact same receiver
        target_rx = f"R{random.randint(2801, 2850)}"
        tx["receiver_id"] = target_rx
        tx["recipient_transaction_count"] = random.randint(5, 8)
        tx["time_since_last_transaction"] = round(random.uniform(1.0, 4.0), 1)
        tx["amount"] = round(random.uniform(12000.0, 24000.0), 2)

    elif scenario == "Unusual Time":
        # Midnight / 3 AM transaction
        unusual_hour = random.choice([1, 2, 3, 4])
        tx["timestamp"] = now.replace(hour=unusual_hour, minute=random.randint(0, 59)).isoformat()
        tx["amount"] = round(random.uniform(18000.0, 35000.0), 2)
        tx["merchant_category"] = "Electronics"

    elif scenario == "Device Change":
        # New unfamiliar phone hardware
        tx["device_type"] = random.choice(other_devices)
        tx["device_changed"] = 1
        tx["amount"] = round(random.uniform(14000.0, 28000.0), 2)

    elif scenario == "Location Change":
        # Sudden geographical jump to a different state/city
        tx["location"] = random.choice(other_cities)
        tx["location_changed"] = 1
        tx["amount"] = round(random.uniform(15000.0, 32000.0), 2)

    elif scenario == "Spending Burst":
        # High value series with rapid velocity
        tx["amount"] = round(random.uniform(38000.0, 68000.0), 2)
        tx["transactions_last_hour"] = random.randint(4, 7)
        tx["time_since_last_transaction"] = round(random.uniform(2.0, 8.0), 1)

    elif scenario == "Multiple Signals":
        # Compound high-risk threat: Extreme amount + New device + New city + 3 AM + Burst
        unusual_hour = random.choice([1, 2, 3, 4])
        tx["timestamp"] = now.replace(hour=unusual_hour, minute=random.randint(0, 59)).isoformat()
        tx["amount"] = round(random.uniform(68000.0, 99000.0), 2)
        tx["device_type"] = random.choice(other_devices)
        tx["device_changed"] = 1
        tx["location"] = random.choice(other_cities)
        tx["location_changed"] = 1
        tx["transactions_last_hour"] = random.randint(8, 14)
        tx["transactions_last_24h"] = tx["transactions_last_hour"] + random.randint(3, 8)
        tx["time_since_last_transaction"] = 1.2
        tx["merchant_category"] = "Financial Services"

    return tx

if __name__ == "__main__":
    print("Normal transaction simulation:")
    print(generate_normal_transaction())
    print("\nSuspicious transaction simulation (Multiple Signals):")
    print(generate_suspicious_transaction("Multiple Signals"))
