"""
End-to-End Pipeline Orchestrator for UPI Fraud Detection System
Executes data generation, cleaning, feature engineering, model training,
anomaly detection, benchmark evaluation, database seeding, and testing.

Usage:
    python run_pipeline.py                # Run full ML & Data pipeline
    python run_pipeline.py --start-server # Run pipeline and launch web dashboard
"""
import os
import sys
import argparse
import time

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import config

def print_step(step_num, title):
    print("\n" + "=" * 75)
    print(f"STEP {step_num}: {title.upper()}")
    print("=" * 75)

def main():
    parser = argparse.ArgumentParser(description="UPI Fraud Detection Pipeline Runner")
    parser.add_argument("--start-server", action="store_true", help="Launch the Flask web server after pipeline completion")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running pytest suite")
    args = parser.parse_args()

    start_time = time.time()
    print("*" * 75)
    print("UPI ENTERPRISE FRAUD DETECTION & ANOMALY MONITORING SYSTEM")
    print("End-to-End Automated Pipeline Execution")
    print("*" * 75)

    # 1. Data Generation
    print_step(1, "Generating 10,000 Synthetic UPI Transactions")
    from src.generate_transactions import generate_synthetic_transactions, save_raw_dataset
    df_raw = generate_synthetic_transactions(
        total_count=config.TOTAL_TRANSACTIONS,
        fraud_ratio=config.TARGET_FRAUD_RATIO
    )
    save_raw_dataset(df_raw, config.RAW_DATA_PATH)

    # 2. Data Cleaning & Feature Engineering Pipeline
    print_step(2, "Data Cleaning, Preprocessing & Feature Engineering")
    from src.preprocessing import preprocess_and_save
    df_processed = preprocess_and_save(config.RAW_DATA_PATH, config.PROCESSED_DATA_PATH)

    # 3. IQR Detector Training
    print_step(3, "Training & Fitting Statistical IQR Detector")
    from src.iqr_detector import IQRAnomalyDetector
    iqr_det = IQRAnomalyDetector(multiplier=config.IQR_MULTIPLIER, features=config.IQR_FEATURES)
    iqr_det.fit(df_processed)
    iqr_det.save(config.IQR_METADATA_PATH)

    # 4. Isolation Forest Training
    print_step(4, "Training Unsupervised Isolation Forest Model (Scikit-Learn)")
    from src.isolation_forest import UPIIsolationForestDetector
    iso_det = UPIIsolationForestDetector(contamination=config.ISOLATION_CONTAMINATION, features=config.ISOLATION_FEATURES)
    iso_det.fit(df_processed)
    iso_det.save(
        model_path=config.MODEL_PATH,
        scaler_path=config.SCALER_PATH,
        metadata_path=config.MODEL_METADATA_PATH
    )

    # 5. Time Series Anomaly Baseline
    print_step(5, "Fitting Rolling Time Series Anomaly & Velocity Detector")
    from src.time_series_detector import TimeSeriesAnomalyDetector
    ts_det = TimeSeriesAnomalyDetector(rolling_window=config.TIME_SERIES_ROLLING_WINDOW, z_threshold=config.Z_SCORE_THRESHOLD)
    ts_det.fit_and_analyze_timeline(df_processed)
    ts_det.save()

    # 6. Ensemble Risk Engine & Model Evaluation
    print_step(6, "Evaluating Benchmark Metrics & Building Evaluation Report")
    from src.evaluation import evaluate_and_save
    evaluate_and_save(config.PROCESSED_DATA_PATH, config.MODELS_DIR / "evaluation_results.json")

    # 7. Database Initialization & Seeding
    print_step(7, "Initializing & Seeding SQLite Database with SQLAlchemy")
    from database.db import seed_database_from_processed_csv
    seed_database_from_processed_csv(config.PROCESSED_DATA_PATH)

    # 8. Run Automated Tests
    if not args.skip_tests:
        print_step(8, "Executing Test Suite with Pytest")
        import pytest
        exit_code = pytest.main(["-v", "tests"])
        if exit_code != 0:
            print("WARNING: Some tests did not pass. Check test logs above.")
        else:
            print("All 20 unit and integration tests passed successfully!")

    elapsed = round(time.time() - start_time, 2)
    print("\n" + "*" * 75)
    print(f"PIPELINE COMPLETED SUCCESSFULLY IN {elapsed}s!")
    print("*" * 75)
    print(f"• Raw Dataset:        {config.RAW_DATA_PATH}")
    print(f"• Processed Dataset:  {config.PROCESSED_DATA_PATH}")
    print(f"• Isolation Model:    {config.MODEL_PATH}")
    print(f"• IQR Metadata:       {config.IQR_METADATA_PATH}")
    print(f"• Evaluation Report:  {config.MODELS_DIR / 'evaluation_results.json'}")
    print(f"• SQLite Database:    {config.DATABASE_PATH}")
    print("*" * 75)

    if args.start_server:
        print("\nStarting Flask Web Server on http://127.0.0.1:5000 ...")
        from app import app
        app.run(host=config.API_HOST, port=config.API_PORT, debug=False)
    else:
        print("\nTo start the web application and interactive dashboard, run:")
        print("    python app.py")
        print("Then open your browser at: http://127.0.0.1:5000\n")

if __name__ == "__main__":
    main()
