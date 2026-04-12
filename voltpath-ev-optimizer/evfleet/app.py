"""
app.py — VoltPath: Electric Rickshaw Fleet Optimizer
=====================================================
Main Streamlit application entry point.
Run: streamlit run app.py
"""

import os
import sys
import streamlit as st

# Allow relative imports
sys.path.insert(0, os.path.dirname(__file__))

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="VoltPath — EV Fleet Optimizer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        background-color: #060d1a;
        color: #e2e8f0;
    }

    /* Dark background for entire app */
    .stApp { background-color: #060d1a; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a1628 0%, #0d1f38 100%);
        border-right: 1px solid rgba(99,179,237,0.12);
    }

    /* Headings */
    h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: rgba(15,23,42,0.7);
        border: 1px solid rgba(99,179,237,0.15);
        border-radius: 12px;
        padding: 12px;
    }

    /* Remove default padding */
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1280px; }

    /* Tabs */
    .stTabs [data-baseweb="tab"] {
        font-family: 'Syne', sans-serif;
        font-weight: 600;
        color: #64748b;
    }
    .stTabs [aria-selected="true"] { color: #63b3ed; border-bottom-color: #63b3ed; }

    /* Dataframe */
    .stDataFrame { border-radius: 10px; overflow: hidden; }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #1a56db, #1a96db);
        color: white;
        border: none;
        border-radius: 8px;
        font-family: 'Syne', sans-serif;
        font-weight: 600;
        padding: 8px 20px;
    }

    /* Info boxes */
    .stAlert { border-radius: 10px; }

    /* Remove hamburger/footer */
    #MainMenu, footer { visibility: hidden; }

    /* Select boxes */
    .stSelectbox > div > div { background: rgba(15,23,42,0.8); border-color: rgba(99,179,237,0.2); }

    /* Slider */
    .stSlider { padding-top: 4px; }
    </style>
    """,
    unsafe_allow_html=True,
)

from src.utils.data_loader import load_fleet, load_zones, load_chargers, load_hubs

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 8px 0 24px; border-bottom: 1px solid rgba(99,179,237,0.15); margin-bottom: 20px;">
            <p style="font-family:'Syne',sans-serif;font-size:22px;font-weight:800;
               color:#e2e8f0;margin:0;letter-spacing:-0.5px;">
               ⚡ VoltPath
            </p>
            <p style="color:#64748b;font-size:12px;margin:2px 0 0;">
                EV Fleet Optimizer · Pune, MH
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        [
            "📊 Overview",
            "🗺️ City Map",
            "🚗 Fleet Performance",
            "⏱️ Downtime Analysis",
            "🧮 Scenario Simulator",
            "💡 Recommendations",
        ],
        label_visibility="collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        """<div style="background:rgba(99,179,237,0.06);border:1px solid rgba(99,179,237,0.15);
        border-radius:10px;padding:14px;font-size:12px;color:#94a3b8;">
        <b style="color:#63b3ed;">⚠ Data Notice</b><br>
        All fleet data is <b>synthetic</b> and labeled for educational/portfolio use.
        Charger locations may use OCM API or curated illustrative data.
        No real operator deployments claimed.
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """<div style="margin-top:20px;font-size:11px;color:#475569;">
        Built with Python · GeoPandas · Streamlit · Folium · Plotly<br>
        Open Charge Map API · SQLite · scikit-learn
        </div>""",
        unsafe_allow_html=True,
    )

# ── Load data ─────────────────────────────────────────────────────────────────
fleet = load_fleet()
zones = load_zones()
chargers = load_chargers()
hubs = load_hubs()

# ── Route pages ───────────────────────────────────────────────────────────────
if page == "📊 Overview":
    from pages.p01_overview import render
    render(fleet, zones, chargers)

elif page == "🗺️ City Map":
    from pages.p02_city_map import render
    render(fleet, zones, chargers, hubs)

elif page == "🚗 Fleet Performance":
    from pages.p03_fleet_performance import render
    render(fleet)

elif page == "⏱️ Downtime Analysis":
    from pages.p04_downtime_analysis import render
    render(fleet, zones)

elif page == "🧮 Scenario Simulator":
    from pages.p05_scenario_simulator import render
    render(fleet, zones, hubs)

elif page == "💡 Recommendations":
    from pages.p06_recommendations import render
    render(fleet, zones, hubs, chargers)
