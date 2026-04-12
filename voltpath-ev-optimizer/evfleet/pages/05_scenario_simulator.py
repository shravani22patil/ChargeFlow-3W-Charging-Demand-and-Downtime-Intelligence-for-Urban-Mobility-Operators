"""pages/05_scenario_simulator.py — ROI Scenario Simulator"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.analysis.analysis import simulate_roi


def render(fleet: pd.DataFrame, zones: pd.DataFrame, hubs: pd.DataFrame) -> None:
    st.markdown("## 🧮 Scenario Simulator")
    st.markdown(
        "<p style='color:#94a3b8;margin-top:-12px;'>Model the financial impact of deploying new charging or swapping infrastructure</p>",
        unsafe_allow_html=True,
    )

    st.markdown("### Configure Your Scenario")

    col1, col2, col3 = st.columns(3)
    with col1:
        n_chargers = st.slider("New Charging Points", min_value=1, max_value=10, value=3)
    with col2:
        cost_per = st.slider("Cost per Charger (₹ Lakh)", min_value=3.0, max_value=20.0, value=8.5, step=0.5)
    with col3:
        coverage = st.slider("Coverage Radius (km)", min_value=0.5, max_value=5.0, value=2.0, step=0.25)

    col4, col5 = st.columns(2)
    with col4:
        avg_rev = st.slider("Avg Revenue per Trip (₹)", min_value=25, max_value=100, value=45)
    with col5:
        downtime_reduction = st.slider("Downtime Reduction Assumption (%)", min_value=10, max_value=70, value=40)

    # ── Run simulation ────────────────────────────────────────────────────────
    result = simulate_roi(
        zone_summary=zones,
        fleet_df=fleet,
        new_chargers=n_chargers,
        cost_per_charger_lakh=cost_per,
        coverage_radius_km=coverage,
        avg_revenue_per_trip=avg_rev,
    )
    # Adjust for custom downtime reduction assumption
    scale = downtime_reduction / 40.0
    result["downtime_hours_saved_per_period"] = round(result["downtime_hours_saved_per_period"] * scale, 1)
    result["revenue_recovered_inr"] = round(result["revenue_recovered_inr"] * scale, 0)
    rev_rec = result["revenue_recovered_inr"]
    capex_inr = result["capex_lakh"] * 1e5
    result["annual_roi_pct"] = round((rev_rec / capex_inr) * 100, 1) if capex_inr > 0 else 0
    result["estimated_payback_months"] = round(capex_inr / (rev_rec / 2), 1) if rev_rec > 0 else float("inf")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Simulation Results")

    card = "background:rgba(15,23,42,0.8);border:1px solid rgba(72,187,120,0.25);border-radius:12px;padding:22px;text-align:center;"
    c1,c2,c3,c4,c5 = st.columns(5)
    for col, label, val, color in [
        (c1, "CapEx", f"₹{result['capex_lakh']:.1f}L", "#fc8181"),
        (c2, "Vehicles Benefited", f"{result['vehicles_benefited']}", "#63b3ed"),
        (c3, "Downtime Hours Saved", f"{result['downtime_hours_saved_per_period']:,.0f}", "#f6ad55"),
        (c4, "Revenue Recovered", f"₹{result['revenue_recovered_inr']/1e5:.2f}L", "#48bb78"),
        (c5, "Est. Payback", f"{result['estimated_payback_months']:.1f} mo", "#b794f4"),
    ]:
        with col:
            st.markdown(f"<div style='{card}'><p style='color:#94a3b8;font-size:11px;margin:0;text-transform:uppercase;'>{label}</p><p style='color:{color};font-size:20px;font-weight:700;margin:6px 0 0;'>{val}</p></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Comparison: 1, 3, 5, 10 chargers ────────────────────────────────────
    scenarios = []
    for n in [1, 2, 3, 5, 7, 10]:
        r = simulate_roi(zones, fleet, n, cost_per, coverage, avg_rev)
        scale_n = downtime_reduction / 40.0
        rev = r["revenue_recovered_inr"] * scale_n
        cap = r["capex_lakh"] * 1e5
        roi = round((rev / cap) * 100, 1) if cap > 0 else 0
        payback = round(cap / (rev / 2), 1) if rev > 0 else 999
        scenarios.append({
            "Chargers": n,
            "CapEx (L)": r["capex_lakh"],
            "Revenue Recovered (L)": round(rev / 1e5, 2),
            "ROI (%)": roi,
            "Payback (months)": payback,
        })
    scen_df = pd.DataFrame(scenarios)

    col_a, col_b = st.columns(2)
    with col_a:
        fig = go.Figure()
        fig.add_bar(x=scen_df["Chargers"].astype(str), y=scen_df["CapEx (L)"], name="CapEx (L)", marker_color="#fc8181")
        fig.add_bar(x=scen_df["Chargers"].astype(str), y=scen_df["Revenue Recovered (L)"], name="Revenue Recovered (L)", marker_color="#48bb78")
        fig.update_layout(
            title="CapEx vs Revenue Recovered by # Chargers",
            barmode="group",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0", height=320,
            xaxis=dict(title="New Chargers", gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(title="₹ Lakh", gridcolor="rgba(255,255,255,0.05)"),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig2 = go.Figure()
        fig2.add_scatter(
            x=scen_df["Chargers"].astype(str), y=scen_df["ROI (%)"],
            mode="lines+markers", name="ROI %",
            line=dict(color="#63b3ed", width=2), marker=dict(size=8),
        )
        fig2.add_scatter(
            x=scen_df["Chargers"].astype(str), y=scen_df["Payback (months)"],
            mode="lines+markers", name="Payback (months)",
            line=dict(color="#f6ad55", width=2, dash="dash"), marker=dict(size=8),
            yaxis="y2",
        )
        fig2.update_layout(
            title="ROI % & Payback Period",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0", height=320,
            xaxis=dict(title="New Chargers", gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(title="ROI (%)", gridcolor="rgba(255,255,255,0.05)"),
            yaxis2=dict(title="Payback (months)", overlaying="y", side="right"),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(scen_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("""
    **⚠️ Simulation Assumptions**
    All financial projections are illustrative estimates based on synthetic fleet data.
    - Downtime reduction assumes charging access within the coverage radius.
    - Revenue recovery = downtime hours saved × avg revenue per hour.
    - Payback = CapEx ÷ (Annual Revenue Recovered ÷ 2) [conservative].
    - No real operator, partnership, or deployment is implied.
    """)
