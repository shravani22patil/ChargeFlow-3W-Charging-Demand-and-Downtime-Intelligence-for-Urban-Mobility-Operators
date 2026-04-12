"""
data_loader.py
--------------
Cached data loading functions for the Streamlit app.
Auto-runs pipeline if processed data doesn't exist.
"""

import os
import sys
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

FLEET_PATH = "data/processed/fleet_operations.csv"
ZONE_PATH = "data/processed/zone_summary.csv"
CHARGER_PATH = "data/processed/chargers.csv"
HUB_PATH = "data/processed/recommended_hubs.csv"


def _ensure_data() -> None:
    """Run pipeline if processed data is missing."""
    if not os.path.exists(FLEET_PATH):
        with st.spinner("⚡ First run — generating data pipeline..."):
            from run_pipeline import run
            run()


@st.cache_data(ttl=3600)
def load_fleet() -> pd.DataFrame:
    _ensure_data()
    df = pd.read_csv(FLEET_PATH, parse_dates=["date"])
    return df


@st.cache_data(ttl=3600)
def load_zones() -> pd.DataFrame:
    _ensure_data()
    return pd.read_csv(ZONE_PATH)


@st.cache_data(ttl=3600)
def load_chargers() -> pd.DataFrame:
    _ensure_data()
    return pd.read_csv(CHARGER_PATH)


@st.cache_data(ttl=3600)
def load_hubs() -> pd.DataFrame:
    _ensure_data()
    return pd.read_csv(HUB_PATH)
