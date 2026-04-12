"""
db_utils.py
-----------
SQLite schema creation and data loading utilities.
Keeps SQL logic separate from analysis scripts.
"""

import os
import sqlite3
import pandas as pd

DB_PATH = os.getenv("DB_PATH", "data/sql/evfleet.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS fleet_operations (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id            TEXT NOT NULL,
    vehicle_type          TEXT,
    date                  TEXT NOT NULL,
    zone                  TEXT,
    zone_lat              REAL,
    zone_lon              REAL,
    demand_score          REAL,
    trip_count            INTEGER,
    battery_level_start   REAL,
    battery_level_end     REAL,
    charge_minutes        INTEGER,
    idle_minutes          INTEGER,
    downtime_wait_minutes INTEGER,
    charger_distance_km   REAL,
    revenue_per_trip      REAL,
    downtime_cost         REAL,
    total_revenue         REAL,
    net_revenue           REAL,
    is_weekend            INTEGER
);

CREATE TABLE IF NOT EXISTS chargers (
    charger_id    TEXT PRIMARY KEY,
    name          TEXT,
    lat           REAL,
    lon           REAL,
    city          TEXT,
    operator      TEXT,
    num_points    INTEGER,
    max_power_kw  REAL,
    status        TEXT,
    data_source   TEXT
);

CREATE TABLE IF NOT EXISTS zone_summary (
    zone                  TEXT PRIMARY KEY,
    lat                   REAL,
    lon                   REAL,
    avg_demand_score      REAL,
    total_trips           INTEGER,
    avg_downtime_wait     REAL,
    avg_charger_distance  REAL,
    total_downtime_cost   REAL,
    total_revenue         REAL,
    vehicle_count         INTEGER,
    downtime_risk_score   REAL,
    accessibility_score   REAL
);

CREATE TABLE IF NOT EXISTS recommended_hubs (
    hub_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    lat             REAL,
    lon             REAL,
    cluster_label   INTEGER,
    zone_proximity  TEXT,
    estimated_roi   REAL,
    priority_rank   INTEGER
);
"""


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return sqlite3.connect(db_path)


def init_db(db_path: str = DB_PATH) -> None:
    """Create all tables if they don't exist."""
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
    print(f"✅ Database initialized: {db_path}")


def load_csv_to_db(csv_path: str, table: str, db_path: str = DB_PATH, if_exists: str = "replace") -> None:
    """Load a CSV into a SQLite table."""
    df = pd.read_csv(csv_path)
    with get_connection(db_path) as conn:
        df.to_sql(table, conn, if_exists=if_exists, index=False)
    print(f"✅ Loaded {len(df):,} rows into '{table}'")


def query(sql: str, db_path: str = DB_PATH) -> pd.DataFrame:
    """Run a SELECT query and return a DataFrame."""
    with get_connection(db_path) as conn:
        return pd.read_sql_query(sql, conn)


if __name__ == "__main__":
    init_db()
    load_csv_to_db("data/processed/fleet_operations.csv", "fleet_operations")
    load_csv_to_db("data/processed/chargers.csv", "chargers")
    load_csv_to_db("data/processed/zone_summary.csv", "zone_summary")
