"""
Project Configuration for UPI Fraud Detection & Anomaly Monitoring System
"""
import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_PATH = DATA_DIR / "raw" / "upi_transactions_10000.csv"
PROCESSED_DATA_PATH = DATA_DIR / "processed" / "processed_transactions.csv"
MODELS_DIR = BASE_DIR / "models"
MODEL_PATH = MODELS_DIR / "isolation_forest.pkl"
SCALER_PATH = MODELS_DIR / "feature_scaler.pkl"
IQR_METADATA_PATH = MODELS_DIR / "iqr_bounds.json"
MODEL_METADATA_PATH = MODELS_DIR / "model_metadata.json"
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "fraud_detection.db"
SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH.as_posix()}"

# Synthetic Data Generation Settings
TOTAL_TRANSACTIONS = 10000
TARGET_FRAUD_RATIO = 0.065  # ~6.5% suspicious/fraud transactions
RANDOM_SEED = 42
NUM_USERS = 1200
NUM_RECEIVERS = 800

# Supported Categories & Channels
MERCHANT_CATEGORIES = [
    "Grocery", "Food & Dining", "Electronics", "Shopping", 
    "Utilities", "Entertainment", "Travel & Transit", "Healthcare", 
    "Financial Services", "Personal Transfer"
]

TRANSACTION_TYPES = ["P2P", "P2M", "Bill Payment", "Investment", "Refund"]

UPI_CHANNELS = ["Google Pay", "PhonePe", "Paytm", "BHIM", "Cred", "Amazon Pay", "Banking App"]

DEVICES = ["Android", "iOS", "Web Portal", "Feature Phone"]

INDIAN_CITIES = [
    "Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai",
    "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Indore",
    "Lucknow", "Chandigarh", "Kochi", "Patna", "Bhopal"
]

# IQR Detection Settings
IQR_MULTIPLIER = 1.5
IQR_FEATURES = [
    "amount",
    "amount_deviation",
    "transactions_last_hour",
    "transactions_last_24h",
    "recipient_transaction_count"
]

# Isolation Forest Settings
ISOLATION_CONTAMINATION = 0.065
ISOLATION_FEATURES = [
    "amount",
    "amount_deviation",
    "transactions_last_hour",
    "transactions_last_24h",
    "time_since_last_transaction",
    "recipient_transaction_count",
    "device_changed",
    "location_changed",
    "hour_of_day"
]

# Time Series Anomaly Settings
TIME_SERIES_ROLLING_WINDOW = 6  # 6-hour rolling window for baseline
Z_SCORE_THRESHOLD = 2.5         # standard deviations for volume/amount spikes

# Ensemble Risk Engine Weights
IQR_WEIGHT = 0.25
ISOLATION_WEIGHT = 0.50
TIME_SERIES_WEIGHT = 0.25

# Risk Score Thresholds (0-100 scale)
RISK_THRESHOLDS = {
    "Low": (0, 29.99),
    "Medium": (30, 59.99),
    "High": (60, 79.99),
    "Critical": (80, 100.0)
}

# Recommendation Rules
RECOMMENDATIONS = {
    "Low": "Allow transaction without step-up verification.",
    "Medium": "Perform passive biometric / SMS OTP step-up verification.",
    "High": "Flag for instant UPI PIN re-authentication & risk-alert notification.",
    "Critical": "Temporarily block transaction & route to Fraud Operations review team."
}

# API Configuration
API_HOST = "127.0.0.1"
API_PORT = 5000
DEBUG_MODE = True
