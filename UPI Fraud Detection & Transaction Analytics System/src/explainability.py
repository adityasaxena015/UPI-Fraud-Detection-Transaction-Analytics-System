"""
Explainability Module for UPI Fraud Detection
Generates transparent, human-readable rationales and contributing factor
breakdowns for flagged transactions to assist human fraud analysts.
"""

def generate_transaction_explanation(tx_dict, iqr_breaches=None, ts_details=None, isolation_pred=0):
    """
    Generates structured, human-readable explanations detailing why a transaction
    was categorized as Low, Medium, High, or Critical risk.
    
    Returns:
        reasons (list of str): Human-readable bullet points
        factor_tags (list of str): Short keyword tags (e.g., ["High Amount", "New Device"])
    """
    reasons = []
    factor_tags = []

    amount = float(tx_dict.get("amount", 0.0))
    hist_avg = float(tx_dict.get("historical_avg_amount", 1000.0))
    amt_dev = float(tx_dict.get("amount_deviation", 1.0))
    tx_1h = int(tx_dict.get("transactions_last_hour", 1))
    tx_24h = int(tx_dict.get("transactions_last_24h", 1))
    recip_cnt = int(tx_dict.get("recipient_transaction_count", 1))
    dev_changed = int(tx_dict.get("device_changed", 0))
    loc_changed = int(tx_dict.get("location_changed", 0))
    hour = int(tx_dict.get("hour_of_day", 12))
    time_diff = float(tx_dict.get("time_since_last_transaction", 120.0))

    # 1. Amount deviation checks
    if amt_dev >= 8.0:
        reasons.append(f"Extreme amount anomaly: ₹{amount:,.2f} is {amt_dev:.1f}x higher than user's normal baseline (₹{hist_avg:,.2f})")
        factor_tags.append("Severe Amount Spike")
    elif amt_dev >= 3.5:
        reasons.append(f"Transaction amount ₹{amount:,.2f} is significantly above historical average ({amt_dev:.1f}x deviation)")
        factor_tags.append("High Amount Deviation")
    elif amount >= 50000:
        reasons.append(f"High absolute transaction amount: ₹{amount:,.2f} exceeds high-value threshold")
        factor_tags.append("High Value")

    # 2. Timing and nocturnal activity
    if 1 <= hour <= 5:
        reasons.append(f"Transaction occurred during unusual nocturnal hours ({hour:02d}:00 AM) when user is normally inactive")
        factor_tags.append("Unusual Nocturnal Hour")

    # 3. Device and Location security signals
    if dev_changed == 1:
        reasons.append("Unrecognized hardware: Transaction initiated from a newly observed device type")
        factor_tags.append("New Device")

    if loc_changed == 1:
        reasons.append(f"Geolocation hop: Sudden transaction from {tx_dict.get('location', 'Unknown')} differing from user's primary hub")
        factor_tags.append("Location Change")

    # 4. Burst and frequency patterns
    if tx_1h >= 10:
        reasons.append(f"Severe transaction burst: {tx_1h} transactions initiated within a single 60-minute window")
        factor_tags.append("Transaction Burst")
    elif tx_1h >= 5:
        reasons.append(f"High velocity frequency: {tx_1h} transactions performed in the past hour")
        factor_tags.append("High Hourly Velocity")

    if recip_cnt >= 4:
        reasons.append(f"Repeated recipient targeting: {recip_cnt} rapid transfers directed to recipient {tx_dict.get('receiver_id', '')}")
        factor_tags.append("Targeted Recipient")

    if time_diff < 4.0:
        reasons.append(f"Micro-interval velocity: Rapid succession just {time_diff:.1f} minutes after preceding transaction")
        factor_tags.append("Rapid Velocity")

    # 5. Detector-specific confirmations
    if iqr_breaches and len(iqr_breaches) > 0:
        breached_fields = ", ".join(iqr_breaches.keys())
        reasons.append(f"IQR Statistical Filter: Breached upper quartile boundaries on [{breached_fields}]")
        factor_tags.append("IQR Outlier")

    if isolation_pred == 1:
        reasons.append("Isolation Forest Model: Detected rare multivariate outlier in joint behavioral feature space")
        factor_tags.append("Isolation Forest Outlier")

    if ts_details and (ts_details.get("transaction_volume_spike") == 1 or ts_details.get("amount_volume_spike") == 1):
        reasons.append("Time Series Trend: Rolling baseline detected abnormal transaction volume or aggregate velocity spike")
        factor_tags.append("Time Series Spike")

    if not reasons:
        reasons.append("Normal behavioral pattern consistent with user historical baseline.")
        factor_tags.append("Normal Activity")

    return reasons, factor_tags
