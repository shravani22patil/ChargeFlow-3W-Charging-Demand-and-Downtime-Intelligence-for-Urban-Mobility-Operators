"""
analysis.py
-----------
Core analytics engine:
  - Nearest charger distance computation
  - Charging accessibility score
  - Downtime risk score
  - Cluster-based hub recommendation
  - ROI simulator for new charging points
"""

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

try:
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


# ── Distance utilities ────────────────────────────────────────────────────────

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in km between two lat/lon points."""
    R = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlam / 2) ** 2
    return R * 2 * np.arcsin(np.sqrt(a))


def compute_nearest_charger_distance(
    zones: pd.DataFrame,
    chargers: pd.DataFrame,
) -> pd.DataFrame:
    """
    For each zone centroid, find the distance to the nearest charger.
    zones must have columns: zone, lat, lon
    chargers must have columns: lat, lon
    """
    zone_coords = zones[["lat", "lon"]].values
    charger_coords = chargers[["lat", "lon"]].values

    if len(charger_coords) == 0:
        zones = zones.copy()
        zones["nearest_charger_km"] = np.nan
        return zones

    dists = cdist(zone_coords, charger_coords, metric=lambda u, v: haversine_km(u[0], u[1], v[0], v[1]))
    zones = zones.copy()
    zones["nearest_charger_km"] = dists.min(axis=1).round(2)
    return zones


# ── Scoring ───────────────────────────────────────────────────────────────────

def compute_accessibility_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Charging Accessibility Score ∈ [0,1]:
    Higher = better access.
    Penalizes long nearest_charger_km and high avg_downtime_wait.
    """
    df = df.copy()
    dist_norm = df["nearest_charger_km"] / df["nearest_charger_km"].max()
    wait_norm = df["avg_downtime_wait"] / df["avg_downtime_wait"].max()
    df["accessibility_score"] = (1 - 0.6 * dist_norm - 0.4 * wait_norm).clip(0, 1).round(3)
    return df


def compute_downtime_risk_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Downtime Risk Score ∈ [0,1]:
    Higher = more risk.
    Combines normalized downtime cost, wait, and distance.
    """
    df = df.copy()
    cost_norm = df["total_downtime_cost"] / df["total_downtime_cost"].max()
    wait_norm = df["avg_downtime_wait"] / df["avg_downtime_wait"].max()
    dist_norm = df["nearest_charger_km"] / df["nearest_charger_km"].max()
    df["downtime_risk_score"] = (0.4 * cost_norm + 0.35 * wait_norm + 0.25 * dist_norm).clip(0, 1).round(3)
    return df


# ── Hub clustering ────────────────────────────────────────────────────────────

def recommend_charging_hubs(
    fleet_df: pd.DataFrame,
    n_clusters: int = 5,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Cluster high-demand, high-downtime vehicle locations to recommend
    optimal new charging/swapping hub positions.

    Returns a DataFrame with recommended hub lat/lon + metadata.
    """
    # Focus on vehicles with high downtime and high demand
    candidates = fleet_df[
        (fleet_df["demand_score"] > 0.65) & (fleet_df["downtime_wait_minutes"] > 30)
    ][["zone_lat", "zone_lon", "zone", "downtime_cost"]].dropna()

    if len(candidates) < n_clusters:
        candidates = fleet_df[["zone_lat", "zone_lon", "zone", "downtime_cost"]].dropna()

    coords = candidates[["zone_lat", "zone_lon"]].values

    if SKLEARN_AVAILABLE and len(coords) >= n_clusters:
        km = KMeans(n_clusters=n_clusters, random_state=seed, n_init=10)
        labels = km.fit_predict(coords)
        centers = km.cluster_centers_
    else:
        # Simple quantile-based fallback
        labels = np.zeros(len(coords), dtype=int)
        centers = coords[:n_clusters]

    candidates = candidates.copy()
    candidates["cluster"] = labels
    cluster_costs = candidates.groupby("cluster")["downtime_cost"].sum()

    hubs = []
    for i, (lat, lon) in enumerate(centers):
        cost = cluster_costs.get(i, 0)
        nearby_zones = candidates[candidates["cluster"] == i]["zone"].value_counts()
        top_zone = nearby_zones.index[0] if len(nearby_zones) > 0 else "Unknown"
        hubs.append({
            "hub_id": i + 1,
            "lat": round(lat, 5),
            "lon": round(lon, 5),
            "cluster_label": i,
            "zone_proximity": top_zone,
            "estimated_annual_savings": round(cost * (365 / 60), 0),
            "priority_rank": i + 1,
        })

    hubs_df = pd.DataFrame(hubs).sort_values("estimated_annual_savings", ascending=False)
    hubs_df["priority_rank"] = range(1, len(hubs_df) + 1)
    return hubs_df


# ── ROI Simulator ─────────────────────────────────────────────────────────────

def simulate_roi(
    zone_summary: pd.DataFrame,
    fleet_df: pd.DataFrame,
    new_chargers: int = 3,
    cost_per_charger_lakh: float = 8.5,
    coverage_radius_km: float = 2.0,
    avg_revenue_per_trip: float = 90.0,  # ₹/hr equivalent (≈2 trips/hr × ₹45/trip)
) -> dict:
    """
    Estimate ROI of adding N new charging points in highest-risk zones.

    Assumptions (illustrative, not real operator data):
    - Each new charger covers vehicles within coverage_radius_km
    - Downtime reduction: ~40% of current wait time for covered vehicles
    - Revenue recovered = downtime_minutes_saved / 60 * avg_revenue_per_trip
    """
    high_risk = zone_summary.nlargest(new_chargers, "downtime_risk_score")

    total_downtime_saved_minutes = 0
    vehicles_benefited = 0

    for _, zone in high_risk.iterrows():
        zone_fleet = fleet_df[fleet_df["zone"] == zone["zone"]]
        n_v = zone_fleet["vehicle_id"].nunique()
        avg_wait = zone_fleet["downtime_wait_minutes"].mean()
        days = fleet_df["date"].nunique()
        saved = avg_wait * 0.40 * n_v * days
        total_downtime_saved_minutes += saved
        vehicles_benefited += n_v

    hours_saved = total_downtime_saved_minutes / 60
    days_in_period = fleet_df["date"].nunique() if hasattr(fleet_df["date"], "nunique") else 60
    # Annualize: scale from simulation window to full year
    annualization_factor = 365 / max(days_in_period, 1)
    revenue_recovered_annual = hours_saved * avg_revenue_per_trip * annualization_factor
    revenue_recovered = revenue_recovered_annual
    capex_total_lakh = new_chargers * cost_per_charger_lakh
    capex_inr = capex_total_lakh * 100_000
    payback_months = capex_inr / (revenue_recovered / 12) if revenue_recovered > 0 else float("inf")

    return {
        "new_chargers": new_chargers,
        "vehicles_benefited": int(vehicles_benefited),
        "downtime_hours_saved_per_period": round(hours_saved, 1),
        "revenue_recovered_inr": round(revenue_recovered, 0),
        "capex_lakh": round(capex_total_lakh, 1),
        "estimated_payback_months": round(payback_months, 1),
        "annual_roi_pct": round((revenue_recovered / capex_inr) * 100, 1) if capex_inr > 0 else 0,
    }
