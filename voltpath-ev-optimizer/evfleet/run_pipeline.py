"""
run_pipeline.py
---------------
Orchestrates the full data pipeline:
1. Generate synthetic fleet data
2. Fetch / fallback charger data
3. Compute scores and recommendations
4. Load everything into SQLite
5. Save processed CSVs

Run this once before launching the Streamlit app.
"""

import os
import sys

# Allow imports from src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.ingestion.generate_synthetic_data import generate_fleet_data, generate_zone_summary
from src.ingestion.fetch_chargers import get_chargers
from src.analysis.analysis import (
    compute_nearest_charger_distance,
    compute_accessibility_score,
    compute_downtime_risk_score,
    recommend_charging_hubs,
)
from src.utils.db_utils import init_db, load_csv_to_db

import pandas as pd


def run(api_key: str | None = None) -> None:
    print("\n🔋 EV Fleet Optimizer — Data Pipeline\n" + "=" * 45)

    # 1. Synthetic fleet
    print("\n[1/5] Generating fleet operations data...")
    fleet_df = generate_fleet_data(n_vehicles=60, days=60)

    # 2. Zone summary (pre-score)
    print("\n[2/5] Computing zone summaries...")
    zone_df = generate_zone_summary(fleet_df)

    # 3. Charger data
    print("\n[3/5] Fetching charger locations...")
    charger_df = get_chargers(api_key=api_key)

    # 4. Enrich zone summary with nearest charger distance + scores
    print("\n[4/5] Computing accessibility & risk scores...")
    zone_df = compute_nearest_charger_distance(zone_df, charger_df)
    zone_df = compute_accessibility_score(zone_df)
    zone_df = compute_downtime_risk_score(zone_df)
    zone_df.to_csv("data/processed/zone_summary.csv", index=False)
    print("✅ Zone summary enriched and saved")

    # 5. Hub recommendations
    hubs_df = recommend_charging_hubs(fleet_df, n_clusters=5)
    hubs_df.to_csv("data/processed/recommended_hubs.csv", index=False)
    print(f"✅ Recommended hubs: {len(hubs_df)}")

    # 6. Load to SQLite
    print("\n[5/5] Loading data into SQLite...")
    init_db()
    load_csv_to_db("data/processed/fleet_operations.csv", "fleet_operations")
    load_csv_to_db("data/processed/chargers.csv", "chargers")
    load_csv_to_db("data/processed/zone_summary.csv", "zone_summary")
    load_csv_to_db("data/processed/recommended_hubs.csv", "recommended_hubs")

    print("\n✅ Pipeline complete! Run: streamlit run app.py\n")


if __name__ == "__main__":
    api_key = os.getenv("OCM_API_KEY")
    run(api_key=api_key)
