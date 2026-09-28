"""
Synthetic UPI Transaction Dataset Generator
Generates exactly 10,000 realistic UPI transactions with user profiles,
temporal consistency, and 8 realistic injected fraud scenarios.
"""
import os
import sys
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from faker import Faker

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

def set_seed(seed=config.RANDOM_SEED):
    random.seed(seed)
    np.random.seed(seed)
    Faker.seed(seed)

def create_user_profiles(num_users=config.NUM_USERS):
    """
    Creates persistent user profiles to model realistic human UPI behavior.
    """
    profiles = {}
    spending_tiers = [
        {"name": "Micro-spender", "mean": 350, "std": 120, "min": 20, "max": 1500, "weight": 0.40},
        {"name": "Average-spender", "mean": 1250, "std": 450, "min": 100, "max": 4500, "weight": 0.45},
        {"name": "Affluent-spender", "mean": 4800, "std": 1600, "min": 500, "max": 18000, "weight": 0.15}
    ]
    tier_choices = [t["name"] for t in spending_tiers]
    tier_weights = [t["weight"] for t in spending_tiers]

    for i in range(1, num_users + 1):
        user_id = f"U{1000 + i}"
        chosen_tier_name = random.choices(tier_choices, weights=tier_weights, k=1)[0]
        tier = next(t for t in spending_tiers if t["name"] == chosen_tier_name)
        
        primary_device = random.choices(
            config.DEVICES, weights=[0.75, 0.20, 0.04, 0.01], k=1
        )[0]
        primary_location = random.choice(config.INDIAN_CITIES)
        primary_channel = random.choices(
            config.UPI_CHANNELS, weights=[0.35, 0.30, 0.15, 0.08, 0.05, 0.04, 0.03], k=1
        )[0]

        profiles[user_id] = {
            "tier": tier,
            "primary_device": primary_device,
            "primary_location": primary_location,
            "primary_channel": primary_channel,
            "normal_hours_start": random.choice([7, 8, 9]),
            "normal_hours_end": random.choice([21, 22, 23]),
            "baseline_avg": max(50.0, float(np.random.normal(tier["mean"], tier["std"] * 0.2)))
        }
    return profiles

def generate_synthetic_transactions(total_count=config.TOTAL_TRANSACTIONS, fraud_ratio=config.TARGET_FRAUD_RATIO):
    """
    Generates 10,000 synthetic transactions adhering to user profiles
    and injecting 8 distinct fraud scenarios.
    """
    set_seed(config.RANDOM_SEED)
    fake = Faker("en_IN")

    user_profiles = create_user_profiles(config.NUM_USERS)
    user_ids = list(user_profiles.keys())
    receiver_ids = [f"R{2000 + i}" for i in range(1, config.NUM_RECEIVERS + 1)]

    # Time span: last 60 days ending at 2026-09-28
    end_date = datetime(2026, 9, 28, 23, 59, 0)
    start_date = end_date - timedelta(days=60)
    total_seconds = int((end_date - start_date).total_seconds())

    fraud_target_count = int(total_count * fraud_ratio)
    normal_target_count = total_count - fraud_target_count

    print(f"Generating {normal_target_count} normal transactions and {fraud_target_count} suspicious/fraud transactions...")

    records = []

    # 1. Generate Normal Transactions
    for i in range(normal_target_count):
        user_id = random.choice(user_ids)
        profile = user_profiles[user_id]
        tier = profile["tier"]

        # Temporal sampling within normal waking hours with occasional light night use
        random_second = random.randint(0, total_seconds)
        dt = start_date + timedelta(seconds=random_second)
        
        # 96% within normal active hours
        if random.random() < 0.96:
            hour = random.randint(profile["normal_hours_start"], profile["normal_hours_end"])
            dt = dt.replace(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59))
        else:
            hour = dt.hour

        # Amount normally distributed around tier mean
        amt = float(np.random.normal(tier["mean"], tier["std"]))
        amt = round(max(tier["min"], min(tier["max"], amt)), 2)

        # 98% stick to primary device, 96% to primary location
        device = profile["primary_device"] if random.random() < 0.98 else random.choice(config.DEVICES)
        location = profile["primary_location"] if random.random() < 0.96 else random.choice(config.INDIAN_CITIES)
        channel = profile["primary_channel"] if random.random() < 0.90 else random.choice(config.UPI_CHANNELS)
        
        receiver = random.choice(receiver_ids)
        category = random.choices(
            config.MERCHANT_CATEGORIES, 
            weights=[0.24, 0.22, 0.08, 0.14, 0.10, 0.08, 0.07, 0.04, 0.02, 0.01], 
            k=1
        )[0]
        tx_type = "P2M" if category != "Personal Transfer" else "P2P"

        records.append({
            "timestamp": dt,
            "sender_id": user_id,
            "receiver_id": receiver,
            "amount": amt,
            "merchant_category": category,
            "transaction_type": tx_type,
            "location": location,
            "device_type": device,
            "upi_channel": channel,
            "fraud_pattern": "Normal",
            "ground_truth_fraud": 0,
            "anomaly_flag": 0
        })

    # 2. Generate Fraud Scenarios (~650 transactions)
    # Distribute among the 8 required scenarios
    scenarios = [
        ("High Amount Fraud", 120),
        ("Transaction Burst", 100),
        ("Repeated Recipient", 90),
        ("Unusual Time", 80),
        ("Device Change", 70),
        ("Location Change", 70),
        ("Spending Burst", 60),
        ("Multiple Signals", 60)
    ]
    # Adjust total to exactly fraud_target_count
    current_scenario_total = sum(s[1] for s in scenarios)
    if current_scenario_total != fraud_target_count:
        scenarios[0] = ("High Amount Fraud", scenarios[0][1] + (fraud_target_count - current_scenario_total))

    for scenario_name, count in scenarios:
        if scenario_name == "High Amount Fraud":
            for _ in range(count):
                user_id = random.choice(user_ids)
                profile = user_profiles[user_id]
                random_second = random.randint(0, total_seconds)
                dt = start_date + timedelta(seconds=random_second)
                
                # Normal spending is 350-5000, high fraud jumps to 40,000 - 98,000
                amount = round(random.uniform(42000.0, 98500.0), 2)
                receiver = random.choice(receiver_ids)
                category = random.choice(["Electronics", "Financial Services", "Shopping", "Personal Transfer"])
                tx_type = "P2M" if category != "Personal Transfer" else "P2P"

                records.append({
                    "timestamp": dt,
                    "sender_id": user_id,
                    "receiver_id": receiver,
                    "amount": amount,
                    "merchant_category": category,
                    "transaction_type": tx_type,
                    "location": profile["primary_location"],
                    "device_type": profile["primary_device"],
                    "upi_channel": profile["primary_channel"],
                    "fraud_pattern": scenario_name,
                    "ground_truth_fraud": 1,
                    "anomaly_flag": 1
                })

        elif scenario_name == "Transaction Burst":
            # Clusters of rapid transactions from same user within one hour
            batches = count // 10
            remainder = count % 10
            for b in range(batches + (1 if remainder else 0)):
                batch_size = 10 if (b < batches) else remainder
                user_id = random.choice(user_ids)
                profile = user_profiles[user_id]
                burst_start = start_date + timedelta(seconds=random.randint(0, total_seconds - 3600))
                
                for k in range(batch_size):
                    dt = burst_start + timedelta(minutes=k * random.randint(2, 5), seconds=random.randint(5, 50))
                    amt = round(random.uniform(1500.0, 8500.0), 2)
                    records.append({
                        "timestamp": dt,
                        "sender_id": user_id,
                        "receiver_id": random.choice(receiver_ids),
                        "amount": amt,
                        "merchant_category": random.choice(["Shopping", "Food & Dining", "Entertainment"]),
                        "transaction_type": "P2M",
                        "location": profile["primary_location"],
                        "device_type": profile["primary_device"],
                        "upi_channel": profile["primary_channel"],
                        "fraud_pattern": scenario_name,
                        "ground_truth_fraud": 1,
                        "anomaly_flag": 1
                    })

        elif scenario_name == "Repeated Recipient":
            # Repeated high/medium transactions to the exact same suspicious recipient within minutes
            batches = count // 5
            remainder = count % 5
            for b in range(batches + (1 if remainder else 0)):
                batch_size = 5 if (b < batches) else remainder
                user_id = random.choice(user_ids)
                profile = user_profiles[user_id]
                fixed_receiver = random.choice(receiver_ids)
                start_dt = start_date + timedelta(seconds=random.randint(0, total_seconds - 7200))
                
                for k in range(batch_size):
                    dt = start_dt + timedelta(minutes=k * random.randint(3, 8), seconds=random.randint(10, 45))
                    amt = round(random.uniform(9000.0, 28000.0), 2)
                    records.append({
                        "timestamp": dt,
                        "sender_id": user_id,
                        "receiver_id": fixed_receiver,
                        "amount": amt,
                        "merchant_category": "Personal Transfer",
                        "transaction_type": "P2P",
                        "location": profile["primary_location"],
                        "device_type": profile["primary_device"],
                        "upi_channel": profile["primary_channel"],
                        "fraud_pattern": scenario_name,
                        "ground_truth_fraud": 1,
                        "anomaly_flag": 1
                    })

        elif scenario_name == "Unusual Time":
            for _ in range(count):
                user_id = random.choice(user_ids)
                profile = user_profiles[user_id]
                random_second = random.randint(0, total_seconds)
                dt = start_date + timedelta(seconds=random_second)
                # Force time into 1:00 AM to 4:30 AM
                unusual_hour = random.choice([1, 2, 3, 4])
                dt = dt.replace(hour=unusual_hour, minute=random.randint(0, 59), second=random.randint(0, 59))
                amt = round(random.uniform(12000.0, 38000.0), 2)

                records.append({
                    "timestamp": dt,
                    "sender_id": user_id,
                    "receiver_id": random.choice(receiver_ids),
                    "amount": amt,
                    "merchant_category": random.choice(["Financial Services", "Electronics", "Entertainment"]),
                    "transaction_type": "P2M",
                    "location": profile["primary_location"],
                    "device_type": profile["primary_device"],
                    "upi_channel": profile["primary_channel"],
                    "fraud_pattern": scenario_name,
                    "ground_truth_fraud": 1,
                    "anomaly_flag": 1
                })

        elif scenario_name == "Device Change":
            for _ in range(count):
                user_id = random.choice(user_ids)
                profile = user_profiles[user_id]
                random_second = random.randint(0, total_seconds)
                dt = start_date + timedelta(seconds=random_second)
                
                # Different device from primary
                other_devices = [d for d in config.DEVICES if d != profile["primary_device"]]
                new_device = random.choice(other_devices)
                amt = round(random.uniform(8500.0, 24000.0), 2)

                records.append({
                    "timestamp": dt,
                    "sender_id": user_id,
                    "receiver_id": random.choice(receiver_ids),
                    "amount": amt,
                    "merchant_category": random.choice(["Electronics", "Shopping", "Personal Transfer"]),
                    "transaction_type": "P2M",
                    "location": profile["primary_location"],
                    "device_type": new_device,
                    "upi_channel": profile["primary_channel"],
                    "fraud_pattern": scenario_name,
                    "ground_truth_fraud": 1,
                    "anomaly_flag": 1
                })

        elif scenario_name == "Location Change":
            for _ in range(count):
                user_id = random.choice(user_ids)
                profile = user_profiles[user_id]
                random_second = random.randint(0, total_seconds)
                dt = start_date + timedelta(seconds=random_second)
                
                # Different city
                other_cities = [c for c in config.INDIAN_CITIES if c != profile["primary_location"]]
                new_location = random.choice(other_cities)
                amt = round(random.uniform(9500.0, 29000.0), 2)

                records.append({
                    "timestamp": dt,
                    "sender_id": user_id,
                    "receiver_id": random.choice(receiver_ids),
                    "amount": amt,
                    "merchant_category": random.choice(["Travel & Transit", "Shopping", "Food & Dining"]),
                    "transaction_type": "P2M",
                    "location": new_location,
                    "device_type": profile["primary_device"],
                    "upi_channel": profile["primary_channel"],
                    "fraud_pattern": scenario_name,
                    "ground_truth_fraud": 1,
                    "anomaly_flag": 1
                })

        elif scenario_name == "Spending Burst":
            # Several high-value transactions within 30-60 mins
            batches = count // 4
            remainder = count % 4
            for b in range(batches + (1 if remainder else 0)):
                batch_size = 4 if (b < batches) else remainder
                user_id = random.choice(user_ids)
                profile = user_profiles[user_id]
                burst_start = start_date + timedelta(seconds=random.randint(0, total_seconds - 3600))
                
                for k in range(batch_size):
                    dt = burst_start + timedelta(minutes=k * random.randint(5, 12), seconds=random.randint(10, 40))
                    amt = round(random.uniform(25000.0, 55000.0), 2)
                    records.append({
                        "timestamp": dt,
                        "sender_id": user_id,
                        "receiver_id": random.choice(receiver_ids),
                        "amount": amt,
                        "merchant_category": random.choice(["Shopping", "Electronics", "Financial Services"]),
                        "transaction_type": "P2M",
                        "location": profile["primary_location"],
                        "device_type": profile["primary_device"],
                        "upi_channel": profile["primary_channel"],
                        "fraud_pattern": scenario_name,
                        "ground_truth_fraud": 1,
                        "anomaly_flag": 1
                    })

        elif scenario_name == "Multiple Signals":
            # Compound extreme fraud: high amount + device changed + location changed + unusual hour (1-4 AM)
            for _ in range(count):
                user_id = random.choice(user_ids)
                profile = user_profiles[user_id]
                random_second = random.randint(0, total_seconds)
                dt = start_date + timedelta(seconds=random_second)
                unusual_hour = random.choice([1, 2, 3, 4])
                dt = dt.replace(hour=unusual_hour, minute=random.randint(0, 59), second=random.randint(0, 59))
                
                other_devices = [d for d in config.DEVICES if d != profile["primary_device"]]
                other_cities = [c for c in config.INDIAN_CITIES if c != profile["primary_location"]]
                
                amount = round(random.uniform(55000.0, 99500.0), 2)
                records.append({
                    "timestamp": dt,
                    "sender_id": user_id,
                    "receiver_id": random.choice(receiver_ids),
                    "amount": amount,
                    "merchant_category": random.choice(["Financial Services", "Electronics", "Personal Transfer"]),
                    "transaction_type": "P2M",
                    "location": random.choice(other_cities),
                    "device_type": random.choice(other_devices),
                    "upi_channel": random.choice(config.UPI_CHANNELS),
                    "fraud_pattern": scenario_name,
                    "ground_truth_fraud": 1,
                    "anomaly_flag": 1
                })

    df = pd.DataFrame(records)
    
    # Sort chronologically
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by="timestamp").reset_index(drop=True)
    
    # Assign sequential transaction IDs
    df.insert(0, "transaction_id", [f"TX{10000000 + i}" for i in range(1, len(df) + 1)])
    
    # Calculate time-based calendar features
    df["hour_of_day"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.day_name()
    
    # Now compute accurate chronological user-specific behavioral features
    print("Computing behavioral history and temporal window features...")
    df = compute_chronological_features(df, user_profiles)
    
    print(f"Generated {len(df)} transactions successfully.")
    print(f"Fraud distribution:\n{df['fraud_pattern'].value_counts()}")
    
    return df

def compute_chronological_features(df, user_profiles):
    """
    Computes rolling transaction metrics per user across the chronological sequence:
    - historical_avg_amount
    - historical_transaction_count
    - time_since_last_transaction (in minutes)
    - recipient_transaction_count (to this receiver in last 24h)
    - device_changed
    - location_changed
    - amount_deviation
    - transactions_last_hour
    - transactions_last_24h
    """
    df["historical_avg_amount"] = 0.0
    df["historical_transaction_count"] = 0
    df["time_since_last_transaction"] = 0.0
    df["recipient_transaction_count"] = 1
    df["device_changed"] = 0
    df["location_changed"] = 0
    df["amount_deviation"] = 1.0
    df["transactions_last_hour"] = 1
    df["transactions_last_24h"] = 1

    sender_history = {}  # sender_id -> list of (timestamp, amount, device, location, receiver_id)
    receiver_history = {} # (sender_id, receiver_id) -> list of timestamps

    n = len(df)
    
    hist_avg_arr = np.zeros(n, dtype=float)
    hist_cnt_arr = np.zeros(n, dtype=int)
    time_diff_arr = np.zeros(n, dtype=float)
    recip_cnt_arr = np.zeros(n, dtype=int)
    dev_chg_arr = np.zeros(n, dtype=int)
    loc_chg_arr = np.zeros(n, dtype=int)
    amt_dev_arr = np.zeros(n, dtype=float)
    tx_1h_arr = np.zeros(n, dtype=int)
    tx_24h_arr = np.zeros(n, dtype=int)

    for idx in range(n):
        ts = df.at[idx, "timestamp"]
        sender = df.at[idx, "sender_id"]
        receiver = df.at[idx, "receiver_id"]
        amt = df.at[idx, "amount"]
        device = df.at[idx, "device_type"]
        location = df.at[idx, "location"]
        
        profile = user_profiles.get(sender, None)
        primary_dev = profile["primary_device"] if profile else device
        primary_loc = profile["primary_location"] if profile else location
        baseline_avg = profile["baseline_avg"] if profile else 1000.0

        dev_chg_arr[idx] = 1 if device != primary_dev else 0
        loc_chg_arr[idx] = 1 if location != primary_loc else 0

        if sender in sender_history:
            prev_txs = sender_history[sender]
            hist_cnt_arr[idx] = len(prev_txs)
            
            # Historical average amount of past transactions
            past_amounts = [t[1] for t in prev_txs]
            avg_amt = float(np.mean(past_amounts))
            hist_avg_arr[idx] = round(avg_amt, 2)
            
            # Time since last transaction in minutes
            last_ts = prev_txs[-1][0]
            time_diff_min = max(0.1, (ts - last_ts).total_seconds() / 60.0)
            time_diff_arr[idx] = round(time_diff_min, 2)

            # Transactions in last 1 hour (60 mins) & 24 hours (1440 mins)
            cutoff_1h = ts - timedelta(hours=1)
            cutoff_24h = ts - timedelta(hours=24)
            tx_1h = sum(1 for t in prev_txs if t[0] >= cutoff_1h) + 1  # including current
            tx_24h = sum(1 for t in prev_txs if t[0] >= cutoff_24h) + 1 # including current
            tx_1h_arr[idx] = tx_1h
            tx_24h_arr[idx] = tx_24h
        else:
            hist_cnt_arr[idx] = 0
            hist_avg_arr[idx] = round(baseline_avg, 2)
            time_diff_arr[idx] = 1440.0  # default 24h for first transaction
            tx_1h_arr[idx] = 1
            tx_24h_arr[idx] = 1

        # Amount deviation = amount / historical_avg_amount
        eff_avg = hist_avg_arr[idx] if hist_avg_arr[idx] > 0 else 100.0
        amt_dev_arr[idx] = round(amt / eff_avg, 3)

        # Recipient transaction count in last 24 hours
        rec_key = (sender, receiver)
        if rec_key in receiver_history:
            cutoff_rec = ts - timedelta(hours=24)
            recip_cnt = sum(1 for t_time in receiver_history[rec_key] if t_time >= cutoff_rec) + 1
            recip_cnt_arr[idx] = recip_cnt
            receiver_history[rec_key].append(ts)
        else:
            recip_cnt_arr[idx] = 1
            receiver_history[rec_key] = [ts]

        # Append to sender history
        if sender not in sender_history:
            sender_history[sender] = []
        sender_history[sender].append((ts, amt, device, location, receiver))

    df["historical_avg_amount"] = hist_avg_arr
    df["historical_transaction_count"] = hist_cnt_arr
    df["time_since_last_transaction"] = time_diff_arr
    df["recipient_transaction_count"] = recip_cnt_arr
    df["device_changed"] = dev_chg_arr
    df["location_changed"] = loc_chg_arr
    df["amount_deviation"] = amt_dev_arr
    df["transactions_last_hour"] = tx_1h_arr
    df["transactions_last_24h"] = tx_24h_arr

    return df

def save_raw_dataset(df, filepath=config.RAW_DATA_PATH):
    """
    Saves generated dataset to raw CSV file.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    print(f"Saved {len(df)} transactions to {filepath}")

if __name__ == "__main__":
    df = generate_synthetic_transactions()
    save_raw_dataset(df)
