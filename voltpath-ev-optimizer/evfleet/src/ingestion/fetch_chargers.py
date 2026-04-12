"""
fetch_chargers.py
-----------------
Fetches EV charging station data from Open Charge Map API for India (Pune).
Falls back to a curated synthetic sample if API is unavailable or returns sparse results.
"""

import os
import json
import requests
import pandas as pd
import numpy as np

OCM_API_URL = "https://api.openchargemap.io/v3/poi/"

# Pune bounding box for spatial filter
PUNE_CENTER = {"lat": 18.520, "lon": 73.856}
PUNE_RADIUS_KM = 35


def fetch_ocm_chargers(
    api_key: str | None = None,
    city_lat: float = PUNE_CENTER["lat"],
    city_lon: float = PUNE_CENTER["lon"],
    radius_km: int = PUNE_RADIUS_KM,
    max_results: int = 200,
    output_path: str = "data/raw/chargers_raw.json",
) -> list[dict]:
    """
    Query Open Charge Map for charging stations near a city center.
    Returns a list of raw POI dicts.
    """
    key = api_key or os.getenv("OCM_API_KEY", "")
    params = {
        "output": "json",
        "countrycode": "IN",
        "latitude": city_lat,
        "longitude": city_lon,
        "distance": radius_km,
        "distanceunit": "KM",
        "maxresults": max_results,
        "verbose": False,
        "compact": True,
    }
    if key:
        params["key"] = key

    try:
        resp = requests.get(OCM_API_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(data, f)
        print(f"✅ OCM API returned {len(data)} charger records")
        return data
    except Exception as e:
        print(f"⚠️  OCM API unavailable ({e}). Using synthetic charger data.")
        return []


def parse_ocm_chargers(raw: list[dict]) -> pd.DataFrame:
    """Parse raw OCM response into a clean DataFrame."""
    rows = []
    for poi in raw:
        try:
            addr = poi.get("AddressInfo", {})
            conns = poi.get("Connections", [])
            power_kw = max(
                (c.get("PowerKW") or 0 for c in conns), default=0
            )
            rows.append({
                "charger_id": poi.get("ID"),
                "name": addr.get("Title", "Unknown"),
                "lat": addr.get("Latitude"),
                "lon": addr.get("Longitude"),
                "city": addr.get("Town", "Pune"),
                "operator": (poi.get("OperatorInfo") or {}).get("Title", "Unknown"),
                "num_points": poi.get("NumberOfPoints") or 1,
                "max_power_kw": power_kw,
                "status": (poi.get("StatusType") or {}).get("Title", "Unknown"),
                "data_source": "Open Charge Map",
            })
        except Exception:
            continue
    return pd.DataFrame(rows)


def synthetic_chargers(seed: int = 99) -> pd.DataFrame:
    """
    Curated synthetic charging/swap stations around Pune.
    Used as fallback when OCM API is sparse or unavailable.
    """
    rng = np.random.default_rng(seed)
    known_stations = [
        {"name": "Shivajinagar EV Hub",    "lat": 18.530, "lon": 73.848, "operator": "Tata Power",      "max_power_kw": 22},
        {"name": "Hinjawadi IT Park Charger","lat": 18.592, "lon": 73.741, "operator": "ChargeZone",     "max_power_kw": 50},
        {"name": "Kharadi Tech Zone",       "lat": 18.552, "lon": 73.942, "operator": "Ather Grid",     "max_power_kw": 15},
        {"name": "Kothrud Swap Point",      "lat": 18.508, "lon": 73.806, "operator": "Sun Mobility",   "max_power_kw": 7},
        {"name": "Wakad Interchange",       "lat": 18.600, "lon": 73.761, "operator": "Tata Power",     "max_power_kw": 22},
        {"name": "Hadapsar MIDC",           "lat": 18.507, "lon": 73.932, "operator": "MSEDCL",         "max_power_kw": 7},
        {"name": "Pimpri Municipal Depot",  "lat": 18.628, "lon": 73.801, "operator": "PMPML",          "max_power_kw": 22},
        {"name": "Yerwada Junction",        "lat": 18.552, "lon": 73.891, "operator": "ChargeZone",     "max_power_kw": 7},
    ]
    rows = []
    for i, s in enumerate(known_stations):
        rows.append({
            "charger_id": f"SYN-{100 + i}",
            "name": s["name"],
            "lat": s["lat"] + rng.normal(0, 0.002),
            "lon": s["lon"] + rng.normal(0, 0.002),
            "city": "Pune",
            "operator": s["operator"],
            "num_points": int(rng.integers(2, 8)),
            "max_power_kw": s["max_power_kw"],
            "status": "Operational",
            "data_source": "Synthetic (Illustrative)",
        })
    return pd.DataFrame(rows)


def get_chargers(
    api_key: str | None = None,
    output_path: str = "data/processed/chargers.csv",
    min_real_results: int = 5,
) -> pd.DataFrame:
    """
    Main entry point. Tries OCM API; falls back to synthetic if needed.
    """
    raw = fetch_ocm_chargers(api_key=api_key)
    if len(raw) >= min_real_results:
        df = parse_ocm_chargers(raw)
    else:
        print("ℹ️  Using synthetic charger dataset (labeled clearly in UI).")
        df = synthetic_chargers()

    df = df.dropna(subset=["lat", "lon"])
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"✅ Charger dataset saved: {len(df)} stations → {output_path}")
    return df


if __name__ == "__main__":
    get_chargers()
