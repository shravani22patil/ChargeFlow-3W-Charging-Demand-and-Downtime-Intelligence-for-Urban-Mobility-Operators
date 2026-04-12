"""
generate_synthetic_data.py
--------------------------
Generates a realistic synthetic electric rickshaw fleet dataset.
Labeled as synthetic — no real operator partnerships claimed.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# ── Pune demand zones (lat/lon centroids + zone names) ───────────────────────
PUNE_ZONES = [
    {"zone": "Shivajinagar",   "lat": 18.530,  "lon": 73.847, "base_demand": 0.88},
    {"zone": "Kothrud",        "lat": 18.507,  "lon": 73.807, "base_demand": 0.72},
    {"zone": "Hadapsar",       "lat": 18.506,  "lon": 73.930, "base_demand": 0.65},
    {"zone": "Wakad",          "lat": 18.601,  "lon": 73.760, "base_demand": 0.70},
    {"zone": "Hinjawadi",      "lat": 18.593,  "lon": 73.739, "base_demand": 0.82},
    {"zone": "Kharadi",        "lat": 18.551,  "lon": 73.942, "base_demand": 0.75},
    {"zone": "Yerawada",       "lat": 18.551,  "lon": 73.893, "base_demand": 0.55},
    {"zone": "Bibwewadi",      "lat": 18.468,  "lon": 73.850, "base_demand": 0.60},
    {"zone": "Pimpri",         "lat": 18.629,  "lon": 73.800, "base_demand": 0.68},
    {"zone": "Katraj",         "lat": 18.449,  "lon": 73.862, "base_demand": 0.50},
]

VEHICLE_TYPES = ["Standard E-Rick", "Cargo E-Rick", "Premium E-Rick"]


def generate_fleet_data(
    n_vehicles: int = 60,
    days: int = 60,
    start_date: str = "2024-01-01",
    seed: int = 42,
    output_path: str = "data/processed/fleet_operations.csv",
) -> pd.DataFrame:
    """
    Generate synthetic daily fleet operations data.

    Returns a DataFrame with one row per vehicle per day.
    """
    np.random.seed(seed)
    rng = np.random.default_rng(seed)

    dates = [
        datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=i)
        for i in range(days)
    ]
    vehicle_ids = [f"ER-{1000 + i}" for i in range(n_vehicles)]
    vehicle_types = rng.choice(VEHICLE_TYPES, size=n_vehicles)
    vehicle_zone_idx = rng.integers(0, len(PUNE_ZONES), size=n_vehicles)

    records = []
    for v_idx, vid in enumerate(vehicle_ids):
        zone_info = PUNE_ZONES[vehicle_zone_idx[v_idx]]
        v_type = vehicle_types[v_idx]
        base_capacity = 6 if "Cargo" in v_type else 8 if "Premium" in v_type else 7

        for date in dates:
            weekday = date.weekday()
            is_weekend = weekday >= 5
            demand_mult = zone_info["base_demand"] * (0.85 if is_weekend else 1.0)
            demand_score = float(np.clip(rng.normal(demand_mult, 0.08), 0.1, 1.0))

            trip_count = int(np.clip(rng.normal(base_capacity * demand_score * 2.5, 2), 1, 22))
            battery_start = float(rng.uniform(60, 100))
            battery_end = float(np.clip(battery_start - trip_count * rng.uniform(3.5, 6.5), 5, 95))

            # Charging time: more trips → more charging needed
            charge_minutes = int(np.clip(rng.normal((100 - battery_end) * 1.2, 15), 0, 180))
            idle_minutes = int(rng.uniform(20, 90))

            # Downtime = time waiting for a charger (modeled as a function of distance to nearest charger)
            charger_distance_km = float(rng.uniform(0.3, 8.0))  # filled by analysis later
            downtime_wait = int(np.clip(charger_distance_km * 8 + rng.normal(0, 5), 0, 90))

            revenue_per_trip = float(rng.uniform(28, 75) * (1.15 if "Premium" in v_type else 1.0))
            downtime_cost = float(downtime_wait / 60 * revenue_per_trip * 1.5)

            # Jitter vehicle lat/lon around zone centroid
            lat_jitter = float(rng.normal(zone_info["lat"], 0.015))
            lon_jitter = float(rng.normal(zone_info["lon"], 0.015))

            records.append({
                "vehicle_id": vid,
                "vehicle_type": v_type,
                "date": date.strftime("%Y-%m-%d"),
                "zone": zone_info["zone"],
                "zone_lat": round(lat_jitter, 5),
                "zone_lon": round(lon_jitter, 5),
                "demand_score": round(demand_score, 3),
                "trip_count": trip_count,
                "battery_level_start": round(battery_start, 1),
                "battery_level_end": round(battery_end, 1),
                "charge_minutes": charge_minutes,
                "idle_minutes": idle_minutes,
                "downtime_wait_minutes": downtime_wait,
                "charger_distance_km": round(charger_distance_km, 2),
                "revenue_per_trip": round(revenue_per_trip, 2),
                "downtime_cost": round(downtime_cost, 2),
                "is_weekend": int(is_weekend),
            })

    df = pd.DataFrame(records)
    df["total_revenue"] = df["revenue_per_trip"] * df["trip_count"]
    df["net_revenue"] = df["total_revenue"] - df["downtime_cost"]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"✅ Fleet data generated: {len(df):,} rows → {output_path}")
    return df


def generate_zone_summary(df: pd.DataFrame, output_path: str = "data/processed/zone_summary.csv") -> pd.DataFrame:
    """Aggregate fleet data to zone-level summaries."""
    zone_meta = pd.DataFrame(PUNE_ZONES)

    summary = (
        df.groupby("zone")
        .agg(
            avg_demand_score=("demand_score", "mean"),
            total_trips=("trip_count", "sum"),
            avg_downtime_wait=("downtime_wait_minutes", "mean"),
            avg_charger_distance=("charger_distance_km", "mean"),
            total_downtime_cost=("downtime_cost", "sum"),
            total_revenue=("total_revenue", "sum"),
            vehicle_count=("vehicle_id", "nunique"),
        )
        .reset_index()
    )
    summary = summary.merge(zone_meta[["zone", "lat", "lon"]], on="zone", how="left")
    summary["downtime_risk_score"] = (
        summary["avg_downtime_wait"] / summary["avg_downtime_wait"].max() * 0.5
        + summary["avg_charger_distance"] / summary["avg_charger_distance"].max() * 0.5
    ).round(3)
    summary["accessibility_score"] = (1 - summary["downtime_risk_score"]).round(3)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    summary.to_csv(output_path, index=False)
    print(f"✅ Zone summary generated → {output_path}")
    return summary


if __name__ == "__main__":
    df = generate_fleet_data()
    generate_zone_summary(df)
