# UPI Fraud Detection System

## 📌 Project Overview
An end-to-end UPI fraud detection system that identifies
suspicious transactions using multiple anomaly detection techniques.

## 🚀 Features
- 10,000+ synthetic UPI transactions
- Data preprocessing and cleaning
- IQR-based outlier detection
- Isolation Forest anomaly detection
- Time-Series anomaly detection
- Fraud/anomaly visualization
- Interactive dashboard

## 🛠️ Technologies Used
- Python
- Pandas
- NumPy
- Matplotlib
- Scikit-learn
- SQL
- Power BI / Streamlit

## 🔍 Detection Techniques
### 1. IQR
Detects transactions with unusually high/low values.

### 2. Isolation Forest
Identifies unusual transaction patterns.

### 3. Time-Series Anomaly Detection
Detects unusual changes in transaction behavior over time.

## 📊 Dataset
10,000 synthetic UPI transactions containing:
- Transaction ID
- Timestamp
- Sender ID
- Receiver ID
- Amount
- Merchant Category
- Transaction Location
- etc.

## ⚙️ Installation

```bash
git clone <your-repository-url>
cd UPI-Fraud-Detection
pip install -r requirements.txt
