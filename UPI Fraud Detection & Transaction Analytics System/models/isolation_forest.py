"""
Model bridge for Isolation Forest Detector
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.isolation_forest import UPIIsolationForestDetector

__all__ = ["UPIIsolationForestDetector"]
