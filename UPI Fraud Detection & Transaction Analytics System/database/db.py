"""
Database Models and ORM Setup using SQLAlchemy
Defines transactions and fraud_alerts tables, plus seeding utilities.
"""
import os
import sys
import json
from datetime import datetime
import pandas as pd
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

Base = declarative_base()

class TransactionModel(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(32), unique=True, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    sender_id = Column(String(32), nullable=False, index=True)
    receiver_id = Column(String(32), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    merchant_category = Column(String(64), nullable=False, index=True)
    transaction_type = Column(String(32), nullable=False)
    location = Column(String(64), nullable=False)
    device_type = Column(String(32), nullable=False)
    upi_channel = Column(String(32), nullable=False)
    
    hour_of_day = Column(Integer, nullable=False)
    day_of_week = Column(String(16), nullable=False)
    
    historical_avg_amount = Column(Float, default=1000.0)
    amount_deviation = Column(Float, default=1.0)
    transactions_last_hour = Column(Integer, default=1)
    transactions_last_24h = Column(Integer, default=1)
    device_changed = Column(Integer, default=0)
    location_changed = Column(Integer, default=0)
    
    iqr_anomaly = Column(Integer, default=0)
    iqr_score = Column(Float, default=0.0)
    isolation_prediction = Column(Integer, default=0)
    isolation_score = Column(Float, default=0.0)
    time_series_anomaly = Column(Integer, default=0)
    time_series_score = Column(Float, default=0.0)
    
    fraud_risk_score = Column(Float, nullable=False, index=True)
    risk_level = Column(String(16), nullable=False, index=True)
    final_anomaly_flag = Column(Integer, default=0, index=True)
    detectors_flagged_count = Column(Integer, default=0, index=True)
    detection_method = Column(String(64), default="None")
    fraud_pattern = Column(String(64), default="Normal")
    ground_truth_fraud = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "transaction_id": self.transaction_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "amount": self.amount,
            "merchant_category": self.merchant_category,
            "transaction_type": self.transaction_type,
            "location": self.location,
            "device_type": self.device_type,
            "upi_channel": self.upi_channel,
            "hour_of_day": self.hour_of_day,
            "day_of_week": self.day_of_week,
            "historical_avg_amount": self.historical_avg_amount,
            "amount_deviation": self.amount_deviation,
            "transactions_last_hour": self.transactions_last_hour,
            "transactions_last_24h": self.transactions_last_24h,
            "device_changed": self.device_changed,
            "location_changed": self.location_changed,
            "iqr_anomaly": self.iqr_anomaly,
            "iqr_score": self.iqr_score,
            "isolation_prediction": self.isolation_prediction,
            "isolation_score": self.isolation_score,
            "time_series_anomaly": self.time_series_anomaly,
            "time_series_score": self.time_series_score,
            "fraud_risk_score": self.fraud_risk_score,
            "risk_level": self.risk_level,
            "final_anomaly_flag": self.final_anomaly_flag,
            "detectors_flagged_count": self.detectors_flagged_count,
            "detection_method": self.detection_method,
            "fraud_pattern": self.fraud_pattern,
            "ground_truth_fraud": self.ground_truth_fraud,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class FraudAlertModel(Base):
    __tablename__ = "fraud_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(32), unique=True, nullable=False, index=True)
    transaction_id = Column(String(32), ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    sender_id = Column(String(32), nullable=False)
    receiver_id = Column(String(32), nullable=False)
    amount = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(16), nullable=False, index=True)
    detection_method = Column(String(64), nullable=False)
    reasons = Column(Text, nullable=False)  # JSON-serialized list of explanation strings
    status = Column(String(16), default="New", index=True)  # New, Reviewing, Resolved
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)

    def to_dict(self):
        try:
            reasons_list = json.loads(self.reasons)
        except Exception:
            reasons_list = [self.reasons]
            
        return {
            "alert_id": self.alert_id,
            "transaction_id": self.transaction_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "amount": self.amount,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "detection_method": self.detection_method,
            "reasons": reasons_list,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

# Database Engine & Session Factory
engine = create_engine(config.SQLALCHEMY_DATABASE_URI, echo=False)
SessionFactory = sessionmaker(bind=engine)
db_session = scoped_session(SessionFactory)

def init_db(drop_existing=False):
    """
    Initializes SQLite database and tables.
    """
    os.makedirs(os.path.dirname(config.DATABASE_PATH), exist_ok=True)
    if drop_existing:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print(f"Database initialized at {config.DATABASE_PATH}")

def seed_database_from_processed_csv(csv_path=config.PROCESSED_DATA_PATH):
    """
    Seeds SQLite database from processed transactions CSV.
    Populates both transactions and fraud_alerts tables.
    """
    init_db(drop_existing=True)
    session = SessionFactory()

    print(f"Seeding database from {csv_path}...")
    df = pd.read_csv(csv_path)

    tx_objects = []
    alert_objects = []
    alert_counter = 1

    for _, row in df.iterrows():
        ts_val = pd.to_datetime(row["timestamp"])
        
        tx = TransactionModel(
            transaction_id=str(row["transaction_id"]),
            timestamp=ts_val.to_pydatetime(),
            sender_id=str(row["sender_id"]),
            receiver_id=str(row["receiver_id"]),
            amount=float(row["amount"]),
            merchant_category=str(row["merchant_category"]),
            transaction_type=str(row["transaction_type"]),
            location=str(row["location"]),
            device_type=str(row["device_type"]),
            upi_channel=str(row["upi_channel"]),
            hour_of_day=int(row["hour_of_day"]),
            day_of_week=str(row["day_of_week"]),
            historical_avg_amount=float(row.get("historical_avg_amount", 1000.0)),
            amount_deviation=float(row.get("amount_deviation", 1.0)),
            transactions_last_hour=int(row.get("transactions_last_hour", 1)),
            transactions_last_24h=int(row.get("transactions_last_24h", 1)),
            device_changed=int(row.get("device_changed", 0)),
            location_changed=int(row.get("location_changed", 0)),
            iqr_anomaly=int(row.get("iqr_anomaly", 0)),
            iqr_score=float(row.get("iqr_score", 0.0)),
            isolation_prediction=int(row.get("isolation_prediction", 0)),
            isolation_score=float(row.get("isolation_score", 0.0)),
            time_series_anomaly=int(row.get("time_series_anomaly", 0)),
            time_series_score=float(row.get("time_series_score", 0.0)),
            fraud_risk_score=float(row.get("fraud_risk_score", 0.0)),
            risk_level=str(row.get("risk_level", "Low")),
            final_anomaly_flag=int(row.get("final_anomaly_flag", 0)),
            detectors_flagged_count=int(row.get("detectors_flagged_count", 0)),
            detection_method=str(row.get("detection_method", "None")),
            fraud_pattern=str(row.get("fraud_pattern", "Normal")),
            ground_truth_fraud=int(row.get("ground_truth_fraud", 0)),
            created_at=ts_val.to_pydatetime()
        )
        tx_objects.append(tx)

        # Flag for fraud_alerts table if High, Critical, or flagged anomaly
        if tx.risk_level in ["High", "Critical"] or tx.final_anomaly_flag == 1:
            reasons_sample = [
                f"Risk score: {tx.fraud_risk_score:.1f} ({tx.risk_level} Risk tier)",
                f"Detection methods triggered: {tx.detection_method}",
                f"Pattern: {tx.fraud_pattern}"
            ]
            if tx.amount_deviation > 3.0:
                reasons_sample.append(f"Amount ₹{tx.amount:,.2f} is {tx.amount_deviation:.1f}x normal average")
            if tx.device_changed:
                reasons_sample.append("Initiated from an unrecognized device")
            if tx.location_changed:
                reasons_sample.append(f"Geographic jump to {tx.location}")
            if tx.hour_of_day <= 5:
                reasons_sample.append(f"Suspicious early morning timestamp ({tx.hour_of_day:02d}:00)")

            alert = FraudAlertModel(
                alert_id=f"ALT{10000 + alert_counter}",
                transaction_id=tx.transaction_id,
                sender_id=tx.sender_id,
                receiver_id=tx.receiver_id,
                amount=tx.amount,
                risk_score=tx.fraud_risk_score,
                risk_level=tx.risk_level,
                detection_method=tx.detection_method,
                reasons=json.dumps(reasons_sample),
                status="New" if alert_counter % 3 != 0 else "Reviewing",
                created_at=tx.timestamp
            )
            alert_objects.append(alert)
            alert_counter += 1

    session.bulk_save_objects(tx_objects)
    session.bulk_save_objects(alert_objects)
    session.commit()
    session.close()

    print(f"Successfully seeded {len(tx_objects)} transactions and {len(alert_objects)} fraud alerts into SQLite database.")

if __name__ == "__main__":
    seed_database_from_processed_csv()
