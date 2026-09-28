"""
Flask REST API and Application Entry Point for UPI Fraud Detection System
Provides endpoints for health checks, analytics statistics, transaction filtering,
real-time transaction analysis, simulation, and alert triage.
"""
import os
import sys
import json
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from sqlalchemy import func, desc

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import config
from database.db import SessionFactory, TransactionModel, FraudAlertModel, init_db
from src.preprocessing import validate_single_transaction_input
from src.feature_engineering import engineer_features_for_single_transaction
from src.iqr_detector import IQRAnomalyDetector
from src.isolation_forest import UPIIsolationForestDetector
from src.time_series_detector import TimeSeriesAnomalyDetector
from src.risk_engine import RiskEngine
from src.transaction_simulator import generate_normal_transaction, generate_suspicious_transaction

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Load Detectors at Application Startup
print("Loading trained anomaly detectors...")
try:
    iqr_detector = IQRAnomalyDetector().load(config.IQR_METADATA_PATH)
    isolation_detector = UPIIsolationForestDetector().load(
        model_path=config.MODEL_PATH,
        scaler_path=config.SCALER_PATH,
        metadata_path=config.MODEL_METADATA_PATH
    )
    time_series_detector = TimeSeriesAnomalyDetector().load(
        config.MODELS_DIR / "time_series_metadata.json"
    )
    risk_engine = RiskEngine()
    models_ready = True
    print("All detection models successfully loaded!")
except Exception as e:
    print(f"Warning: Failed to load models at startup: {e}")
    models_ready = False

@app.teardown_appcontext
def shutdown_session(exception=None):
    pass

# -------------------------------------------------------------
# Frontend Routes
# -------------------------------------------------------------
@app.route("/")
def dashboard_page():
    """Renders the single-page analytical dashboard."""
    return render_template("dashboard.html")

# -------------------------------------------------------------
# REST API Endpoints
# -------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health_check():
    """
    GET /api/health
    Health check returning system and model status.
    """
    db_ok = os.path.exists(config.DATABASE_PATH)
    return jsonify({
        "status": "healthy",
        "service": "UPI Fraud Detection & Anomaly Monitoring System",
        "timestamp": datetime.now().isoformat(),
        "database_connected": db_ok,
        "models_ready": models_ready
    }), 200

@app.route("/api/stats", methods=["GET"])
def get_stats():
    """
    GET /api/stats
    Returns consolidated portfolio KPIs, risk distributions, and temporal trends.
    """
    session = SessionFactory()
    try:
        total_tx = session.query(func.count(TransactionModel.id)).scalar() or 0
        total_amt = session.query(func.sum(TransactionModel.amount)).scalar() or 0.0
        
        high_risk_tx = session.query(func.count(TransactionModel.id)).filter(TransactionModel.risk_level == "High").scalar() or 0
        critical_risk_tx = session.query(func.count(TransactionModel.id)).filter(TransactionModel.risk_level == "Critical").scalar() or 0
        medium_risk_tx = session.query(func.count(TransactionModel.id)).filter(TransactionModel.risk_level == "Medium").scalar() or 0
        low_risk_tx = session.query(func.count(TransactionModel.id)).filter(TransactionModel.risk_level == "Low").scalar() or 0
        
        suspicious_tx = session.query(func.count(TransactionModel.id)).filter(TransactionModel.final_anomaly_flag == 1).scalar() or 0
        active_alerts_count = session.query(func.count(FraudAlertModel.id)).filter(FraudAlertModel.status != "Resolved").scalar() or 0

        fraud_pct = round((suspicious_tx / total_tx * 100), 2) if total_tx > 0 else 0.0

        # Method breakdown
        iqr_only = session.query(func.count(TransactionModel.id)).filter(
            TransactionModel.iqr_anomaly == 1,
            TransactionModel.isolation_prediction == 0,
            TransactionModel.time_series_anomaly == 0
        ).scalar() or 0

        iso_only = session.query(func.count(TransactionModel.id)).filter(
            TransactionModel.iqr_anomaly == 0,
            TransactionModel.isolation_prediction == 1,
            TransactionModel.time_series_anomaly == 0
        ).scalar() or 0

        ts_only = session.query(func.count(TransactionModel.id)).filter(
            TransactionModel.iqr_anomaly == 0,
            TransactionModel.isolation_prediction == 0,
            TransactionModel.time_series_anomaly == 1
        ).scalar() or 0

        multi_methods = session.query(func.count(TransactionModel.id)).filter(
            TransactionModel.detectors_flagged_count >= 2
        ).scalar() or 0

        # Daily trends (last 14 days)
        trends_query = session.query(
            func.date(TransactionModel.timestamp).label("tx_date"),
            func.count(TransactionModel.id).label("count"),
            func.sum(TransactionModel.amount).label("volume"),
            func.sum(TransactionModel.final_anomaly_flag).label("anomalies")
        ).group_by(func.date(TransactionModel.timestamp)).order_by(desc("tx_date")).limit(14).all()

        daily_trends = [
            {
                "date": str(r.tx_date),
                "count": int(r.count),
                "volume": round(float(r.volume or 0), 2),
                "anomalies": int(r.anomalies or 0)
            }
            for r in reversed(trends_query)
        ]

        # Top merchant categories by fraud
        category_query = session.query(
            TransactionModel.merchant_category,
            func.count(TransactionModel.id).label("total_tx"),
            func.sum(TransactionModel.final_anomaly_flag).label("fraud_tx")
        ).group_by(TransactionModel.merchant_category).all()

        category_stats = [
            {
                "category": r.merchant_category,
                "total": int(r.total_tx),
                "fraud": int(r.fraud_tx or 0),
                "rate": round(int(r.fraud_tx or 0) / int(r.total_tx) * 100, 1) if int(r.total_tx) > 0 else 0
            }
            for r in category_query
        ]

        return jsonify({
            "status": "success",
            "kpis": {
                "total_transactions": total_tx,
                "total_amount": round(total_amt, 2),
                "suspicious_transactions": suspicious_tx,
                "high_risk_transactions": high_risk_tx,
                "critical_transactions": critical_risk_tx,
                "medium_risk_transactions": medium_risk_tx,
                "low_risk_transactions": low_risk_tx,
                "fraud_percentage": fraud_pct,
                "active_alerts_count": active_alerts_count
            },
            "risk_distribution": {
                "Low": low_risk_tx,
                "Medium": medium_risk_tx,
                "High": high_risk_tx,
                "Critical": critical_risk_tx
            },
            "detector_distribution": {
                "IQR_Only": iqr_only,
                "Isolation_Forest_Only": iso_only,
                "Time_Series_Only": ts_only,
                "Multiple_Detectors": multi_methods,
                "No_Anomaly": max(0, total_tx - (iqr_only + iso_only + ts_only + multi_methods))
            },
            "daily_trends": daily_trends,
            "category_stats": category_stats
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    """
    GET /api/transactions
    Query parameters:
    - risk_level (Low, Medium, High, Critical)
    - sender (search sender_id)
    - category (merchant category)
    - anomaly_only (true/false)
    - limit (int, default 50)
    - offset (int, default 0)
    """
    session = SessionFactory()
    try:
        risk_level = request.args.get("risk_level")
        sender = request.args.get("sender")
        category = request.args.get("category")
        anomaly_only = request.args.get("anomaly_only")
        limit = min(int(request.args.get("limit", 50)), 500)
        offset = int(request.args.get("offset", 0))

        query = session.query(TransactionModel)

        if risk_level:
            query = query.filter(TransactionModel.risk_level == risk_level)
        if sender:
            query = query.filter(TransactionModel.sender_id.ilike(f"%{sender}%"))
        if category:
            query = query.filter(TransactionModel.merchant_category == category)
        if anomaly_only and anomaly_only.lower() in ["true", "1"]:
            query = query.filter(TransactionModel.final_anomaly_flag == 1)

        total_matching = query.count()
        transactions = query.order_by(TransactionModel.id.desc()).offset(offset).limit(limit).all()

        return jsonify({
            "status": "success",
            "total_matching": total_matching,
            "limit": limit,
            "offset": offset,
            "transactions": [tx.to_dict() for tx in transactions]
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/transactions/<string:tx_id>", methods=["GET"])
def get_single_transaction(tx_id):
    """
    GET /api/transactions/<tx_id>
    Fetches full metadata and operational reasons for a specific transaction ID.
    """
    session = SessionFactory()
    try:
        tx = session.query(TransactionModel).filter(TransactionModel.transaction_id == tx_id).first()
        if not tx:
            return jsonify({"status": "error", "message": f"Transaction '{tx_id}' not found."}), 404

        tx_dict = tx.to_dict()
        
        # Check if an alert exists for it
        alert = session.query(FraudAlertModel).filter(FraudAlertModel.transaction_id == tx_id).first()
        tx_dict["alert"] = alert.to_dict() if alert else None

        return jsonify({"status": "success", "transaction": tx_dict}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/analyze", methods=["POST"])
def analyze_transaction():
    """
    POST /api/analyze
    Analyzes an incoming transaction payload in real time.
    Generates behavioral features, runs all 3 anomaly detection models,
    calculates consolidated risk score, persists transaction & alert,
    and returns full explainability breakdown.
    """
    payload = request.get_json(force=True, silent=True)
    if not payload:
        return jsonify({"status": "error", "message": "Invalid JSON body provided."}), 400

    is_valid, err_msg, cleaned_tx = validate_single_transaction_input(payload)
    if not is_valid:
        return jsonify({"status": "error", "message": err_msg}), 422

    session = SessionFactory()
    try:
        sender_id = cleaned_tx["sender_id"]
        
        # Look up sender's prior profile from database for realistic dynamic context
        recent_txs = session.query(TransactionModel).filter(
            TransactionModel.sender_id == sender_id
        ).order_by(TransactionModel.timestamp.desc()).limit(20).all()

        user_history = None
        if recent_txs:
            amounts = [t.amount for t in recent_txs]
            avg_amt = float(sum(amounts) / len(amounts))
            latest_tx = recent_txs[0]
            
            # Count recent in last 1h and 24h
            tx_dt = cleaned_tx.get("timestamp")
            if isinstance(tx_dt, str):
                try:
                    ref_ts = datetime.fromisoformat(tx_dt.replace("Z", "+00:00"))
                except Exception:
                    ref_ts = datetime.now()
            else:
                ref_ts = datetime.now()

            cutoff_1h = ref_ts - timedelta(hours=1)
            cutoff_24h = ref_ts - timedelta(hours=24)
            tx_1h = sum(1 for t in recent_txs if t.timestamp >= cutoff_1h) + 1
            tx_24h = sum(1 for t in recent_txs if t.timestamp >= cutoff_24h) + 1
            
            rec_id = cleaned_tx["receiver_id"]
            rec_count = sum(1 for t in recent_txs if t.receiver_id == rec_id and t.timestamp >= cutoff_24h) + 1

            user_history = {
                "historical_avg_amount": avg_amt,
                "historical_transaction_count": len(recent_txs),
                "last_timestamp": latest_tx.timestamp,
                "primary_device": latest_tx.device_type,
                "primary_location": latest_tx.location,
                "transactions_last_hour": tx_1h,
                "transactions_last_24h": tx_24h,
                "recipient_transaction_count": rec_count
            }

        # 1. Feature Engineering
        enriched_tx = engineer_features_for_single_transaction(cleaned_tx, user_history=user_history)

        # 2. Run IQR Anomaly Detection
        iqr_anomaly, iqr_score, iqr_breaches = iqr_detector.detect_single(enriched_tx)

        # 3. Run Isolation Forest ML Anomaly Detection
        isolation_pred, isolation_score, iso_raw_decision = isolation_detector.predict_single(enriched_tx)

        # 4. Run Time Series Anomaly Detection
        ts_anomaly, ts_score, ts_details = time_series_detector.detect_single(enriched_tx)

        # 5. Evaluate Consolidated Risk Engine
        evaluation = risk_engine.evaluate_single_transaction(
            tx_dict=enriched_tx,
            iqr_anomaly=iqr_anomaly,
            iqr_score=iqr_score,
            iqr_breaches=iqr_breaches,
            isolation_pred=isolation_pred,
            isolation_score=isolation_score,
            time_series_anomaly=ts_anomaly,
            time_series_score=ts_score,
            ts_details=ts_details
        )

        # 6. Generate Transaction ID
        tx_id = cleaned_tx.get("transaction_id") or f"TX{uuid.uuid4().hex[:8].upper()}"

        # 7. Persist to Database
        ts_object = enriched_tx["timestamp"]
        new_tx = TransactionModel(
            transaction_id=tx_id,
            timestamp=ts_object,
            sender_id=enriched_tx["sender_id"],
            receiver_id=enriched_tx["receiver_id"],
            amount=enriched_tx["amount"],
            merchant_category=enriched_tx["merchant_category"],
            transaction_type=enriched_tx["transaction_type"],
            location=enriched_tx["location"],
            device_type=enriched_tx["device_type"],
            upi_channel=enriched_tx["upi_channel"],
            hour_of_day=enriched_tx["hour_of_day"],
            day_of_week=enriched_tx["day_of_week"],
            historical_avg_amount=enriched_tx["historical_avg_amount"],
            amount_deviation=enriched_tx["amount_deviation"],
            transactions_last_hour=enriched_tx["transactions_last_hour"],
            transactions_last_24h=enriched_tx["transactions_last_24h"],
            device_changed=enriched_tx["device_changed"],
            location_changed=enriched_tx["location_changed"],
            iqr_anomaly=iqr_anomaly,
            iqr_score=iqr_score,
            isolation_prediction=isolation_pred,
            isolation_score=isolation_score,
            time_series_anomaly=ts_anomaly,
            time_series_score=ts_score,
            fraud_risk_score=evaluation["fraud_risk_score"],
            risk_level=evaluation["risk_level"],
            final_anomaly_flag=evaluation["final_anomaly_flag"],
            detectors_flagged_count=evaluation["detectors_flagged_count"],
            detection_method=evaluation["detection_method"],
            fraud_pattern=cleaned_tx.get("simulated_scenario", "Real-Time Ingestion"),
            ground_truth_fraud=1 if evaluation["final_anomaly_flag"] == 1 else 0
        )
        session.add(new_tx)

        # 8. Create Fraud Alert if High/Critical or Anomaly
        alert_id = None
        if evaluation["risk_level"] in ["High", "Critical"] or evaluation["final_anomaly_flag"] == 1:
            alert_id = f"ALT{uuid.uuid4().hex[:6].upper()}"
            alert = FraudAlertModel(
                alert_id=alert_id,
                transaction_id=tx_id,
                sender_id=new_tx.sender_id,
                receiver_id=new_tx.receiver_id,
                amount=new_tx.amount,
                risk_score=evaluation["fraud_risk_score"],
                risk_level=evaluation["risk_level"],
                detection_method=evaluation["detection_method"],
                reasons=json.dumps(evaluation["reasons"]),
                status="New"
            )
            session.add(alert)

        session.commit()

        # Build response adhering strictly to user requirements
        response = {
            "status": "success",
            "transaction_id": tx_id,
            "risk_score": evaluation["fraud_risk_score"],
            "risk_level": evaluation["risk_level"],
            "final_anomaly_flag": bool(evaluation["final_anomaly_flag"]),
            "iqr_anomaly": bool(iqr_anomaly),
            "isolation_anomaly": bool(isolation_pred),
            "time_series_anomaly": bool(ts_anomaly),
            "detection_method": evaluation["detection_method"],
            "recommendation": evaluation["recommendation"],
            "reasons": evaluation["reasons"],
            "factor_tags": evaluation["factor_tags"],
            "alert_created": alert_id is not None,
            "alert_id": alert_id,
            "engineered_features": {
                "amount": enriched_tx["amount"],
                "historical_avg_amount": enriched_tx["historical_avg_amount"],
                "amount_deviation": enriched_tx["amount_deviation"],
                "transactions_last_hour": enriched_tx["transactions_last_hour"],
                "transactions_last_24h": enriched_tx["transactions_last_24h"],
                "time_since_last_transaction": enriched_tx["time_since_last_transaction"],
                "recipient_transaction_count": enriched_tx["recipient_transaction_count"],
                "device_changed": enriched_tx["device_changed"],
                "location_changed": enriched_tx["location_changed"],
                "hour_of_day": enriched_tx["hour_of_day"]
            },
            "detector_scores": evaluation["detector_scores"]
        }
        return jsonify(response), 200

    except Exception as e:
        session.rollback()
        return jsonify({"status": "error", "message": f"Analysis failed: {str(e)}"}), 500
    finally:
        session.close()

@app.route("/api/simulate", methods=["POST"])
def simulate_transaction_endpoint():
    """
    POST /api/simulate
    Body parameters:
    - scenario: "Normal", "High Amount Fraud", "Transaction Burst", "Repeated Recipient",
                "Unusual Time", "Device Change", "Location Change", "Spending Burst",
                "Multiple Signals", or "random"
    """
    data = request.get_json(silent=True) or {}
    scenario = data.get("scenario", "random")

    if scenario == "Normal":
        payload = generate_normal_transaction()
    elif scenario == "random":
        scenarios_pool = [
            "Normal", "High Amount Fraud", "Transaction Burst", "Repeated Recipient",
            "Unusual Time", "Device Change", "Location Change", "Spending Burst", "Multiple Signals"
        ]
        chosen = random.choice(scenarios_pool)
        payload = generate_normal_transaction() if chosen == "Normal" else generate_suspicious_transaction(chosen)
    else:
        payload = generate_suspicious_transaction(scenario)

    # Re-use analyze logic via internal test client or direct call
    with app.test_request_context(
        "/api/analyze", method="POST", json=payload, headers={"Content-Type": "application/json"}
    ):
        analyze_res, status_code = analyze_transaction()
        response_data = analyze_res.get_json()

    return jsonify({
        "status": "success",
        "simulated_scenario": payload.get("simulated_scenario", "Normal"),
        "transaction_payload": payload,
        "analysis": response_data
    }), status_code

@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    """
    GET /api/alerts
    Query parameters:
    - status: New, Reviewing, Resolved
    - risk_level: High, Critical, etc.
    - limit: int
    - offset: int
    """
    session = SessionFactory()
    try:
        status = request.args.get("status")
        risk_level = request.args.get("risk_level")
        limit = min(int(request.args.get("limit", 50)), 200)
        offset = int(request.args.get("offset", 0))

        query = session.query(FraudAlertModel)
        if status:
            query = query.filter(FraudAlertModel.status == status)
        if risk_level:
            query = query.filter(FraudAlertModel.risk_level == risk_level)

        total_alerts = query.count()
        alerts = query.order_by(FraudAlertModel.id.desc()).offset(offset).limit(limit).all()

        return jsonify({
            "status": "success",
            "total_matching": total_alerts,
            "alerts": [a.to_dict() for a in alerts]
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/alerts/<string:alert_id>/status", methods=["POST"])
def update_alert_status(alert_id):
    """
    POST /api/alerts/<alert_id>/status
    Body:
    - status: "New" | "Reviewing" | "Resolved"
    - notes: optional string
    """
    data = request.get_json(force=True, silent=True) or {}
    new_status = data.get("status")
    notes = data.get("notes")

    if new_status not in ["New", "Reviewing", "Resolved"]:
        return jsonify({"status": "error", "message": "Status must be 'New', 'Reviewing', or 'Resolved'."}), 400

    session = SessionFactory()
    try:
        alert = session.query(FraudAlertModel).filter(FraudAlertModel.alert_id == alert_id).first()
        if not alert:
            return jsonify({"status": "error", "message": f"Alert '{alert_id}' not found."}), 404

        alert.status = new_status
        if notes is not None:
            alert.notes = notes

        session.commit()
        return jsonify({
            "status": "success",
            "message": f"Alert {alert_id} updated to '{new_status}'",
            "alert": alert.to_dict()
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/model-info", methods=["GET"])
def get_model_info():
    """
    GET /api/model-info
    Returns trained models' metadata, configurations, feature weights,
    and synthetic benchmark evaluation results.
    """
    eval_path = config.MODELS_DIR / "evaluation_results.json"
    eval_data = {}
    if os.path.exists(eval_path):
        with open(eval_path, "r") as f:
            eval_data = json.load(f)

    iso_meta_path = config.MODEL_METADATA_PATH
    iso_meta = {}
    if os.path.exists(iso_meta_path):
        with open(iso_meta_path, "r") as f:
            iso_meta = json.load(f)

    iqr_meta_path = config.IQR_METADATA_PATH
    iqr_meta = {}
    if os.path.exists(iqr_meta_path):
        with open(iqr_meta_path, "r") as f:
            iqr_meta = json.load(f)

    return jsonify({
        "status": "success",
        "ensemble_weights": {
            "IQR": config.IQR_WEIGHT,
            "Isolation_Forest": config.ISOLATION_WEIGHT,
            "Time_Series": config.TIME_SERIES_WEIGHT
        },
        "risk_thresholds": config.RISK_THRESHOLDS,
        "recommendations": config.RECOMMENDATIONS,
        "isolation_forest_meta": iso_meta,
        "iqr_bounds": iqr_meta.get("bounds", {}),
        "evaluation_benchmarks": eval_data
    }), 200

if __name__ == "__main__":
    app.run(host=config.API_HOST, port=config.API_PORT, debug=config.DEBUG_MODE)
