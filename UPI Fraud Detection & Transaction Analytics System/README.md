# 🛡️ UPI Guard — Enterprise UPI Fraud Detection & Anomaly Monitoring System

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.1-black.svg)](https://flask.palletsprojects.com/)
[![Machine Learning](https://img.shields.io/badge/ML-Scikit--Learn%20Isolation%20Forest-orange.svg)](https://scikit-learn.org/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%2F%20SQLAlchemy-red.svg)](https://www.sqlalchemy.org/)
[![Tests](https://img.shields.io/badge/Tests-20%2F20%20Passing-brightgreen.svg)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#)

An end-to-end, production-grade **UPI Fraud Detection and Anomaly Monitoring System** built with **Statistical IQR Bounds**, **Unsupervised Isolation Forest (Machine Learning)**, and **Rolling Time-Series Velocity Analytics**. 

Designed for **BTech CSE/Data Science portfolios, GitHub showcases, resume bullet points, and technical placement interviews**.

---

## 📌 Table of Contents

1. [Project Overview](#-project-overview)
2. [Problem Statement](#-problem-statement)
3. [Core Objectives](#-core-objectives)
4. [Key Features](#-key-features)
5. [System Architecture](#-system-architecture)
6. [Technology Stack](#-technology-stack)
7. [Synthetic Dataset Generation](#-synthetic-dataset-generation)
8. [Dataset Fields Specification](#-dataset-fields-specification)
9. [Simulated Fraud Scenarios](#-simulated-fraud-scenarios)
10. [Feature Engineering Pipeline](#-feature-engineering-pipeline)
11. [Detection Methodologies](#-detection-methodologies)
    - [IQR Statistical Baseline](#1-iqr-interquartile-range-statistical-baseline)
    - [Isolation Forest Multivariate Model](#2-isolation-forest-multivariate-model)
    - [Time Series Velocity & Burst Detector](#3-time-series-velocity--burst-detector)
    - [Consolidated Risk Engine](#4-consolidated-risk-scoring-engine)
12. [Benchmark Evaluation Results](#-benchmark-evaluation-results)
13. [REST API Documentation](#-rest-api-documentation)
14. [Interactive Web Dashboard](#-interactive-web-dashboard)
15. [Installation & Setup](#-installation--setup)
16. [How to Run](#-how-to-run)
17. [Testing Suite](#-testing-suite)
18. [Example Request & Response](#-example-api-request--response)
19. [Limitations & Assumptions](#-limitations--assumptions)
20. [Future Roadmap](#-future-roadmap)
21. [Resume & Interview Bullet Points](#-resume--interview-presentation)

---

## 🚀 Project Overview

The Unified Payments Interface (UPI) handles over 14 billion transactions every month in India. With high transaction throughput comes rapid automated fraud attacks: SIM swapping, rapid account drain, credential stuffing, nocturnal bursts, and phishing transfers.

**UPI Guard** is an end-to-end anomaly detection platform designed to detect fraudulent UPI transactions in real time. Rather than relying on a single model or black-box predictions, the system operates a **Triple-Engine Anomaly Sentinel**:

1. **IQR Statistical Filter** for univariate extreme values (amount and rate outliers).
2. **Scikit-Learn Isolation Forest** for multivariate behavioral anomaly scoring.
3. **Rolling Time-Series Z-Score Detector** for short-term volume bursts and rapid drain attacks.
4. **Weighted Risk Engine** that consolidates detector votes into a **0–100 Fraud Risk Score**, maps them into actionable risk tiers (Low, Medium, High, Critical), and generates human-readable forensic checkmarks for operational analysts.

---

## 🎯 Problem Statement

Traditional rule-based fraud engines struggle with:
- **High False Positive Rates:** Legitimate high-value festival or salary purchases trigger unnecessary blocks.
- **Velocity Blindspots:** Distributed low-value bot transactions evade static amount thresholds.
- **Lack of Explainability:** Machine learning models often output probabilities without explaining *why* a customer's transaction was stopped.

**UPI Guard solves this** by coupling statistical baselines with unsupervised ensemble machine learning and instant behavioral feature explainability.

---

## ⚡ Key Features

- **10,000 Realistic Synthetic Transactions:** Temporally progression across 60 days with 1,200 persistent user profiles and 800 merchant/counterparty accounts.
- **8 Injected Fraud Scenarios:** Covers high-value spikes, transaction bursts, repeated recipient drain, nocturnal transfers, hardware hopping, geographic jumps, spending bursts, and compound multi-vector attacks.
- **Dynamic Real-Time Feature Engineering:** Real-time computation of `amount_deviation`, 1-hour burst velocity, 24-hour frequency, and hardware/location delta.
- **Triple-Engine Detection:** Deterministic IQR + Unsupervised ML Isolation Forest + Rolling Time Series Z-scores.
- **0–100 Calibrated Risk Score:** Non-linear consensus boosting when multiple independent detectors concur.
- **Forensic Explainability Engine:** Generates human-readable bullet points explaining the exact root cause of every flagged transaction.
- **Full REST API (Flask & Flask-CORS):** Health checks, KPI metrics, dynamic filtering, real-time ingestion, simulation, and alert status management.
- **SQLite & SQLAlchemy ORM:** Persistent tables for `transactions` and `fraud_alerts`.
- **Interactive Cyber-Themed Dashboard:** Bootstrap 5, Chart.js visualizations, live transaction simulator, alert triage workflow, and API testing sandbox.
- **20/20 Automated Tests Passing:** Pytest unit and integration test suite.

---

## 🏗️ System Architecture

```text
               SYNTHETIC TRANSACTION GENERATOR
                  (10,000 UPI Transactions)
                             │
                             ▼
              DATA PREPROCESSING & VALIDATION
                   (Schema, Scaler, Impute)
                             │
                             ▼
               DYNAMIC FEATURE ENGINEERING
          (Ratios, Velocity, Temporal Flags)
                             │
       ┌─────────────────────┼─────────────────────┐
       ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│     IQR      │     │  ISOLATION   │     │ TIME-SERIES  │
│ STATISTICAL  │     │ FOREST (ML)  │     │   VELOCITY   │
│  BASELINE    │     │ MULTIVARIATE │     │   BURSTS     │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │ (25% Weight)       │ (50% Weight)       │ (25% Weight)
       └─────────────────────┼─────────────────────┘
                             ▼
                  CONSOLIDATED RISK ENGINE
             (Weighted Score + Consensus Boost)
                             │
                             ▼
               FRAUD RISK SCORE & EXPLAINABILITY
             [Low: 0-29 | Med: 30-59 | High: 60-79 | Crit: 80-100]
                             │
                             ▼
                    FLASK REST API
          (POST /api/analyze | POST /api/simulate)
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
      SQLITE DATABASE                 WEB DASHBOARD
(transactions & fraud_alerts)       (Chart.js, KPIs, Sandbox)
```

---

## 💻 Technology Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Language** | Python 3.11+ / Python 3.14 compatible |
| **Data Generation** | Faker, NumPy, Pandas, Random |
| **Machine Learning** | Scikit-Learn (`IsolationForest`), StandardScaler, Joblib |
| **Statistical Methods** | Interquartile Range (IQR), Rolling Windows, Z-Scores |
| **Backend & REST API** | Flask 3.1, Flask-CORS, Werkzeug |
| **Database & ORM** | SQLite, SQLAlchemy 2.0 |
| **Frontend Dashboard** | HTML5, Modern CSS3 (Dark Cyberpunk Theme), Vanilla JS, Bootstrap 5, Chart.js |
| **Testing Suite** | Pytest |

---

## 📊 Synthetic Dataset Generation

To ensure behavioral fidelity without relying on private financial data, `src/generate_transactions.py` creates **1,200 distinct sender profiles** categorized into spending tiers:
- **Micro-Spenders (40%):** Daily average ₹350, range ₹20–₹1,500.
- **Average-Spenders (45%):** Daily average ₹1,250, range ₹100–₹4,500.
- **Affluent-Spenders (15%):** Daily average ₹4,800, range ₹500–₹18,000.

Each user has an assigned **primary device** (Android/iOS), **primary location** (top 15 Indian metro cities), and **typical waking transaction window** (7 AM – 11 PM).

---

## 📑 Dataset Fields Specification

The raw and processed datasets (`data/raw/` and `data/processed/`) feature 24 core columns:

| Column | Type | Description |
| :--- | :--- | :--- |
| `transaction_id` | String | Unique UPI transaction reference (e.g. `TX10000001`) |
| `timestamp` | DateTime | Timestamp of payment initiation |
| `sender_id` | String | Customer UPI VPA/ID (e.g. `U1042`) |
| `receiver_id` | String | Payee UPI ID or merchant identifier |
| `amount` | Float | Transaction value in Indian Rupees (₹) |
| `merchant_category`| String | Category: Grocery, Food & Dining, Electronics, Shopping, etc. |
| `transaction_type` | String | P2P, P2M, Bill Payment, Investment |
| `location` | String | Originating city (Mumbai, Delhi, Bengaluru, etc.) |
| `device_type` | String | Hardware: Android, iOS, Web Portal, Feature Phone |
| `upi_channel` | String | App used: Google Pay, PhonePe, Paytm, BHIM, Cred |
| `hour_of_day` | Integer | Transaction hour (0–23) |
| `day_of_week` | String | Monday through Sunday |
| `historical_avg_amount`| Float | Rolling historical average transaction amount for sender |
| `historical_transaction_count`| Integer | Lifetime transactions recorded for sender |
| `time_since_last_transaction` | Float | Elapsed time since prior transaction (minutes) |
| `recipient_transaction_count`| Integer | Transfers directed to this payee in last 24h |
| `device_changed` | Integer | Binary flag: 1 if different from user's primary device |
| `location_changed` | Integer | Binary flag: 1 if different from user's primary city |
| `amount_deviation` | Float | Ratio: `amount / historical_avg_amount` |
| `transactions_last_hour`| Integer | Cumulative transfers initiated in prior 60 minutes |
| `transactions_last_24h` | Integer | Cumulative transfers initiated in prior 24 hours |
| `fraud_pattern` | String | Ground-truth simulation vector name |
| `ground_truth_fraud`| Integer | 0 for Normal, 1 for Injected Fraud (evaluation only) |
| `anomaly_flag` | Integer | Preliminary benchmark label |

---

## 🚨 Simulated Fraud Scenarios

The synthetic generator injects 8 realistic fraud vectors representing 6.5% of total transactions:

1. **Scenario 1 — High Amount Fraud (120 tx):** A sudden transaction 30x–60x higher than normal spending (e.g., ₹75,000 for a ₹1,200 baseline user).
2. **Scenario 2 — Transaction Burst (100 tx):** Rapid velocity bot attacks (12–18 transactions within 60 minutes).
3. **Scenario 3 — Repeated Recipient (90 tx):** Multiple rapid transfers directed at the exact same payee within minutes (account drain attack).
4. **Scenario 4 — Unusual Time (80 tx):** Transactions occurring between 1:00 AM and 4:30 AM for a user who transacts exclusively during daytime.
5. **Scenario 5 — Device Change (70 tx):** High-value transfer originating from a new, unregistered hardware device.
6. **Scenario 6 — Location Change (70 tx):** Geolocation hop without plausible travel time (e.g., Mumbai to Patna in 20 minutes).
7. **Scenario 7 — Spending Burst (60 tx):** Clustered series of high-value transactions within 30 minutes.
8. **Scenario 8 — Multiple Signals (60 tx):** Compound multi-vector attack: ₹80,000+ amount + new device + new city + 2:30 AM + velocity burst.

---

## 🔬 Detection Methodologies

### 1. IQR (Interquartile Range) Statistical Baseline
- Computes $Q_1$ (25th percentile), $Q_3$ (75th percentile), and $IQR = Q_3 - Q_1$.
- Upper Bound: $Q_3 + 1.5 \times IQR$.
- Applied to numerical features: `amount`, `amount_deviation`, `transactions_last_hour`, `transactions_last_24h`, and `recipient_transaction_count`.
- Yields deterministic boundaries and an `iqr_score` in [0, 100].

### 2. Isolation Forest (Multivariate Model)
- Unsupervised tree ensemble trained via Scikit-Learn (`n_estimators=150`, `contamination=0.065`).
- Evaluates 9 joint dimensions simultaneously.
- Raw `decision_function` is calibrated through a logistic transformation to map directly to a normalized $[0, 100]$ score:
  $$\text{isolation\_score} = \frac{100}{1 + e^{-14 \times \text{decision\_function}}}$$

### 3. Time Series Velocity & Burst Detector
- Tracks rolling 6-hour baseline statistics and Z-scores for volume spikes.
- Flags immediate velocity spikes ($\ge 5$ transactions/hour) and rapid account drain ($< 3$ minutes between large payments).

### 4. Consolidated Risk Scoring Engine
Combines the three independent detectors using configurable weights:
- **Isolation Forest Weight:** 50%
- **IQR Statistical Weight:** 25%
- **Time Series Velocity Weight:** 25%

**Consensus Boosting Rule:** If 2 or 3 detectors concur, non-linear consensus penalties (+8 to +15 points) are applied, ensuring coordinated multi-vector fraud escalates into High/Critical tiers:
- **Low Risk (0–29):** Allow transaction without step-up verification.
- **Medium Risk (30–59):** Passive biometric / SMS OTP step-up verification.
- **High Risk (60–79):** UPI PIN re-authentication & push notification alert.
- **Critical Risk (80–100):** Temporary block & immediate routing to fraud triage queue.

---

## 📈 Benchmark Evaluation Results

Evaluated on the 10,000 transaction synthetic benchmark (6.5% fraud prevalence):

| Detector | Precision | Recall | F1-Score | Accuracy | FPR | ROC-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **IQR Statistical Baseline** | 0.3846 | **0.9892** | 0.5538 | 89.2% | 0.1012 | 0.9922 |
| **Isolation Forest (ML)** | 0.8523 | 0.8523 | 0.8523 | 98.08% | 0.0103 | 0.9918 |
| **Time Series Velocity** | **1.0000** | 0.1400 | 0.2456 | 94.41% | 0.0000 | 0.7668 |
| **Ensemble Risk Engine** | **0.9702** | **0.8508** | **0.9066** | **98.88%** | **0.0028** | **0.9977** |

### Scenario-Wise Detection Rates:
- **Multiple Signals:** 100.0% (Avg Score: 91.2)
- **Device Change:** 100.0% (Avg Score: 71.2)
- **Location Change:** 98.6% (Avg Score: 70.1)
- **High Amount Fraud:** 89.2% (Avg Score: 69.6)
- **Spending Burst:** 88.3% (Avg Score: 67.8)
- **Repeated Recipient:** 82.2% (Avg Score: 75.6)
- **Transaction Burst:** 75.0% (Avg Score: 73.6)
- **Unusual Time:** 56.2% (Avg Score: 61.8)

> **Academic Note:** Anomaly detection is fundamentally unsupervised. Ground-truth labels were strictly isolated and used solely for post-hoc validation.

---

## 🌐 REST API Documentation

### 1. `GET /api/health`
Checks API status, database connectivity, and model availability.

### 2. `GET /api/stats`
Returns portfolio KPIs, total transaction volume, risk distributions, daily trend series, and merchant category breakdowns.

### 3. `GET /api/transactions`
Query parameters: `risk_level`, `sender`, `category`, `limit`, `offset`.

### 4. `POST /api/analyze`
Submits a raw transaction for real-time feature engineering, 3-model scoring, SQLite persistence, and risk explanation.

### 5. `POST /api/simulate`
Body: `{"scenario": "High Amount Fraud" | "Multiple Signals" | "Normal" | "random"}`.

### 6. `GET /api/alerts`
Retrieves fraud triage queue with status filtering (`New`, `Reviewing`, `Resolved`).

### 7. `POST /api/alerts/<id>/status`
Updates operational alert status and attaches analyst investigation notes.

### 8. `GET /api/model-info`
Returns model hyperparameters, IQR cutoffs, contamination settings, and benchmark metrics.

---

## 💻 Interactive Web Dashboard

The frontend is served directly by Flask at `http://127.0.0.1:5000`:
- **Navigation Sidebar:** Seamless view switching between Overview, Simulator, Alerts, Transactions, Sandbox, and Model Architecture.
- **KPI Monitoring Cards:** Real-time metrics on transaction count, total rupees processed, fraud rate, and active alerts.
- **Interactive Chart.js Visualizations:**
  - 14-day daily transaction volume vs. anomaly trends.
  - Risk tier donut distribution (Low, Medium, High, Critical).
  - Anomaly detector voting breakdown.
  - Merchant category vulnerability ranking.
- **Live Transaction Simulator:** Allows one-click testing of all 8 fraud scenarios with instant visual alert modals, score gauges, and forensic checklists.
- **Alert Triage Console:** Modal interface for compliance analysts to review evidence and transition alerts to *Reviewing* or *Resolved*.
- **API Sandbox:** Manual transaction entry with instant JSON payload and response viewing.

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/upi-fraud-detection.git
cd upi-fraud-detection
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS / Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🚀 How to Run

### Automated Single-Command Workflow
Run the entire pipeline (generate data, preprocess, train models, evaluate, seed SQLite, and run tests):
```bash
python run_pipeline.py
```

To run the pipeline and automatically launch the web dashboard:
```bash
python run_pipeline.py --start-server
```

### Running Components Individually
```bash
# 1. Generate 10,000 synthetic transactions
python src/generate_transactions.py

# 2. Preprocess & scale features
python src/preprocessing.py

# 3. Fit IQR statistical bounds
python src/iqr_detector.py

# 4. Train Scikit-Learn Isolation Forest
python src/isolation_forest.py

# 5. Fit Time Series baseline
python src/time_series_detector.py

# 6. Evaluate benchmarks
python src/evaluation.py

# 7. Initialize and seed SQLite database
python database/db.py

# 8. Start Flask backend & Web Dashboard
python app.py
```

Then visit **`http://127.0.0.1:5000`** in your browser.

---

## 🧪 Testing Suite

Run all 20 automated unit and integration tests using pytest:
```bash
pytest -v
```

Tests cover:
- Synthetic dataset shape (exactly 10,000 rows, 24 required fields).
- Absence of duplicate transaction IDs.
- Temporal feature extraction and amount deviation math.
- IQR boundary fitting and single-transaction detection.
- Isolation Forest inference and calibrated 0–100 scoring.
- Time-series volume and burst spike detection.
- Risk Engine score bounds ($0 \le \text{score} \le 100$).
- API endpoints: `/api/health`, `/api/stats`, `/api/transactions`, `/api/analyze`, `/api/simulate`, `/api/alerts`.
- Rejection of invalid inputs (negative amounts, missing fields).

---

## 📝 Example API Request & Response

### Request (`POST /api/analyze`)
```bash
curl -X POST http://127.0.0.1:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "sender_id": "U1023",
    "receiver_id": "R2045",
    "amount": 78000.0,
    "merchant_category": "Financial Services",
    "transaction_type": "P2M",
    "location": "Patna",
    "device_type": "Feature Phone",
    "upi_channel": "BHIM",
    "timestamp": "2026-09-29T02:45:00"
  }'
```

### Response
```json
{
  "status": "success",
  "transaction_id": "TX9A42F0B1",
  "risk_score": 92.4,
  "risk_level": "Critical",
  "final_anomaly_flag": true,
  "iqr_anomaly": true,
  "isolation_anomaly": true,
  "time_series_anomaly": true,
  "detection_method": "IQR + Isolation Forest + Time Series",
  "recommendation": "Temporarily block transaction & route to Fraud Operations review team.",
  "alert_created": true,
  "alert_id": "ALT6C91D4",
  "factor_tags": [
    "Severe Amount Spike",
    "Unusual Nocturnal Hour",
    "New Device",
    "Location Change",
    "IQR Outlier",
    "Isolation Forest Outlier"
  ],
  "reasons": [
    "Extreme amount anomaly: ₹78,000.00 is 58.2x higher than user normal baseline (₹1,340.00)",
    "Transaction occurred during unusual nocturnal hours (02:00 AM) when user is normally inactive",
    "Unrecognized hardware: Transaction initiated from a newly observed device type",
    "Geolocation hop: Sudden transaction from Patna differing from user primary hub",
    "IQR Statistical Filter: Breached upper quartile boundaries on [amount, amount_deviation]",
    "Isolation Forest Model: Detected rare multivariate outlier in joint behavioral feature space"
  ]
}
```

---

## ⚠️ Limitations & Assumptions

1. **Synthetic Data Ground Truth:** Real banking fraud is adversarial and evolves continuously. Synthetic evaluations establish benchmark capability but require continuous retraining on real label feedback.
2. **Simplified Geolocation:** Location changes in this demonstration are represented as city names rather than high-precision GPS coordinate radius calculations.
3. **Database Concurrency:** SQLite is configured for local single-node demonstration. Production systems would deploy PostgreSQL/TimescaleDB with Redis caching for microsecond feature lookups.

---

## 🔮 Future Roadmap

- [ ] **Graph Neural Networks (GNN):** Add network topology analysis (NetworkX / PyTorch Geometric) to detect money-mule rings and cyclic UPI wash transfers.
- [ ] **Kafka Stream Processing:** Stream live transactions through Apache Kafka into a real-time Flink or Spark Streaming inference microservice.
- [ ] **SHAP Tree Explanations:** Integrate Kernel/TreeSHAP waterfall plots directly into the transaction forensics modal.
- [ ] **Docker & Kubernetes Deployment:** Containerize into multi-service docker-compose setup.

---

## 💼 Resume & Interview Presentation

### Resume Bullet Points
- **UPI Fraud Detection & Anomaly Sentinel:** Designed an end-to-end UPI fraud detection system in Python, analyzing 10,000 transactions with a multi-detector ensemble combining **IQR statistical bounds**, **Scikit-Learn Isolation Forest**, and **rolling Time Series velocity analytics**.
- **97.0% Precision & 0.998 ROC-AUC:** Engineered behavioral features (`amount_deviation`, 1h burst frequency, device/location hopping) and calibrated a weighted 0–100 risk scoring engine with consensus boosting, achieving **90.7% F1-score**.
- **Full-Stack REST Architecture:** Built a **Flask REST API** with SQLAlchemy ORM and an interactive dark-themed cybersecurity dashboard (Bootstrap 5, Chart.js) featuring real-time transaction simulation, forensic explainability checkmarks, and operational alert triage.
- **Enterprise Testing & CI Readiness:** Implemented automated test suite with 20/20 pytest tests covering data schema, detector bounds, calibrated score limits, and edge-case API error handling.

### Key Interview Talking Points
1. **Why not just train a supervised classifier like XGBoost?**
   *"In payment systems, fraud is fundamentally unsupervised and zero-day. Legitimate labels take 30–90 days (chargebacks). An unsupervised ensemble with statistical baselines and Isolation Forest can catch novel attack vectors without historical ground truth."*
2. **Why combine IQR with Isolation Forest?**
   *"IQR provides strict deterministic bounds that are easy to audit and explain to banking regulators. Isolation Forest catches non-linear multivariate interactions that individually pass IQR thresholds (e.g., normal amount + unusual time + new device)."*
3. **How does consensus boosting prevent alert fatigue?**
   *"Univariate IQR flags many false positives. The Risk Engine only escalates transactions to High/Critical when multiple independent models corroborate the anomaly or compound risk signals exceed severity thresholds."*

---

## 📜 License

Distributed under the MIT License. Open-source for academic, educational, and portfolio purposes.
