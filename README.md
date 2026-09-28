# 💳 UPI Fraud Detection & Transaction Analytics System

An end-to-end **UPI Fraud Detection and Transaction Analytics System** that analyzes 10,000+ synthetic UPI transactions to identify fraudulent patterns, spending anomalies, and suspicious transaction behavior.

The system combines **data analytics, anomaly detection, machine learning, and an interactive web dashboard** to provide insights into transaction trends and potential fraud risks.

---

## 📌 Project Overview

Digital payment platforms process a large number of transactions every day, making automated fraud detection important for identifying suspicious activity.

This project analyzes UPI transaction data using **Python, Pandas, Scikit-learn, SQL, Flask, and Chart.js** to:

* Detect potentially fraudulent transaction patterns
* Identify unusual spending behavior
* Analyze transaction trends
* Generate risk scores
* Visualize fraud alerts and payment activity
* Provide an interactive analytics dashboard

---

## 🎯 Key Features

* 📊 Analysis of **10,000+ UPI transactions**
* 🧹 Data cleaning and preprocessing
* ⚙️ Feature engineering
* 🔍 Anomaly detection
* 🚨 Fraud pattern identification
* 📈 Transaction trend analysis
* 🎯 Transaction risk scoring
* 📊 Interactive analytics dashboard
* 🔔 Fraud alert visualization
* 🗄️ SQL-based data analysis
* 🌐 Flask-based web application

---

## 🔍 Fraud & Anomaly Detection

The project uses multiple techniques to identify suspicious transactions.

### 1. IQR-Based Outlier Detection

The **Interquartile Range (IQR)** method identifies unusually high or low transaction amounts.

```text
IQR = Q3 - Q1

Lower Bound = Q1 - 1.5 × IQR
Upper Bound = Q3 + 1.5 × IQR
```

Transactions outside these boundaries can be flagged as potential anomalies.

---

### 2. Isolation Forest

**Isolation Forest** is an unsupervised machine learning algorithm used to identify unusual transaction behavior.

It analyzes transaction features and isolates observations that differ significantly from normal transaction patterns.

---

### 3. Time-Series Anomaly Detection

Transaction activity is analyzed over time to identify unusual patterns such as:

* Sudden transaction spikes
* Abnormal transaction frequency
* Unusual spending periods
* Unexpected changes in transaction volume

---

## 📊 Transaction Analytics

The dashboard provides insights into:

* Total transactions
* Total transaction amount
* Fraud/anomaly alerts
* Transaction trends
* Spending patterns
* Risk scores
* Transaction categories
* Suspicious transactions

---

## 🛠️ Technologies Used

### Programming & Data Analysis

* **Python**
* **Pandas**
* **NumPy**

### Machine Learning

* **Scikit-learn**
* Isolation Forest
* Anomaly Detection

### Database

* **SQL**

### Backend

* **Flask**

### Frontend & Visualization

* **HTML**
* **CSS**
* **JavaScript**
* **Chart.js**

---

## 🏗️ System Workflow

```text
             UPI Transaction Data
                      │
                      ▼
             Data Cleaning
                      │
                      ▼
            Feature Engineering
                      │
                      ▼
            Exploratory Analysis
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
        IQR      Isolation     Time-Series
                   Forest       Detection
          └───────────┼───────────┘
                      ▼
              Risk Score / Alerts
                      │
                      ▼
              Flask Backend
                      │
                      ▼
           Interactive Dashboard
                      │
                      ▼
        Transaction Analytics
```

---

## 📁 Project Structure

```text
UPI-Fraud-Detection/
│
├── data/
│   └── transactions.csv
│
├── notebooks/
│   └── fraud_analysis.ipynb
│
├── src/
│   ├── data_cleaning.py
│   ├── feature_engineering.py
│   ├── fraud_detection.py
│   └── anomaly_detection.py
│
├── templates/
│   └── index.html
│
├── static/
│   ├── css/
│   └── js/
│
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```

> Adjust the folder structure above to match your actual project files.

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/UPI-Fraud-Detection.git
```

### 2. Navigate to the project

```bash
cd UPI-Fraud-Detection
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the environment

**Windows:**

```bash
venv\Scripts\activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Application

Start the Flask application:

```bash
python app.py
```

Then open the local URL displayed by Flask in your browser.

---

## 📦 Requirements

Example `requirements.txt`:

```text
pandas
numpy
scikit-learn
flask
matplotlib
seaborn
```

Add any other libraries that your actual project imports.

---

## 📈 Example Insights

The system can be used to identify:

```text
✔ Unusually high-value transactions
✔ Abnormal transaction frequency
✔ Suspicious spending patterns
✔ Potential fraudulent transactions
✔ Changes in transaction activity over time
✔ High-risk transactions
```

---

## 📊 Dashboard

The interactive dashboard provides visual representations of:

* Payment trends
* Transaction volume
* Transaction amounts
* Risk scores
* Fraud alerts
* Anomaly patterns

### Dashboard Preview

Add screenshots of your dashboard here:

```markdown
![Dashboard](screenshots/dashboard.png)
```

---

## 🔐 Data Privacy

The project uses **synthetic transaction data** for development and demonstration.

No real customer banking information or UPI transaction data is used.

---

## 🚀 Future Improvements

* Real-time transaction monitoring
* Real-time fraud alerts
* Advanced machine learning models
* Deep learning-based fraud detection
* User behavioral profiling
* REST API integration
* Cloud deployment
* Authentication and role-based access
* Model performance monitoring
* Explainable AI for fraud detection

---

## 👨‍💻 Author

**Aditya**

B.Tech Computer Science & Engineering

**Interests:** Data Science, Data Analytics, Machine Learning & AI

---

## ⭐ Project Highlights

```text
10,000+ Transactions
        ↓
Data Cleaning
        ↓
Feature Engineering
        ↓
Anomaly Detection
        ↓
Risk Scoring
        ↓
Fraud Alerts
        ↓
Interactive Dashboard
```

---

## ⚠️ Disclaimer

This project is intended for **educational and demonstration purposes**. The dataset is synthetic and the detected anomalies should not be interpreted as confirmed real-world financial fraud.
