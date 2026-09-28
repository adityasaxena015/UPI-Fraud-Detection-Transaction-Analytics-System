"""
Model bridge for Time Series Anomaly Detector
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.time_series_detector import TimeSeriesAnomalyDetector

__all__ = ["TimeSeriesAnomalyDetector"]
