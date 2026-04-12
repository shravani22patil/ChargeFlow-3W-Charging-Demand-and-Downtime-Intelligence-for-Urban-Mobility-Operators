"""pages/01_overview.py — Fleet KPI Overview Dashboard"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.utils.data_loader import load_fleet, load_zones, load_chargers


def render(fleet: pd.DataFrame, zones: pd.DataFrame, chargers: pd.DataFrame) -> None:
    st.markdown("## 📊 Fleet Operations Overview")
    st.markdown(
        "<p style='color:#94a3b8;margin-top:-12px;'>Synthetic operational data · Pune, Maharashtra · 60-day window</p>",
        unsafe_allow_html=True,
    )

    # ── Top KPIs ────────────────────────────────────────────────────────────
    total_revenue = fleet["total_revenue"].sum()
    total_downtime_cost = fleet["downtime_cost"].sum()
    total_trips = fleet["trip_count"].sum()
    avg_demand = fleet["demand_score"].mean()
    n_vehicles = fleet["vehicle_id"].nunique()
    avg_downtime_wait = fleet["downtime_wait_minutes"].mean()

    col1, col2, col3, col4, col5 = st.columns(5)
    kpi_style = """
        background: rgba(15,23,42,0.7);
        border: 1px solid rgba(99,179,237,0.2);
        border-radius: 12px;
        padding: 20px 16px;
        text-align: center;
    """

    def kpi_card(col, label, value, delta=None, delta_label="", color="#63b3ed"):
        with col:
            delta_html = f"<p style='color:{'#48bb78' if delta and delta > 0 else '#fc8181'};font-size:12px;margin:4px 0 0 0;'>{delta_label}</p>" if delta_label else ""
            st.markdown(
                f"""<div style="{kpi_style}">
                    <p style='color:#94a3b8;font-size:12px;margin:0;letter-spacing:0.05em;text-transform:uppercase;'>{label}</p>
                    <p style='color:{color};font-size:26px;font-weight:700;margin:6px 0 0 0;'>{value}</p>
                    {delta_html}
                </div>""",
                unsafe_allow_html=True,
            )

    kpi_card(col1, "Total Trips", f"{total_trips:,}", color="#63b3ed")
    kpi_card(col2, "Gross Revenue", f"₹{total_revenue/1e5:.1f}L", color="#48bb78")
    kpi_card(col3, "Downtime Loss", f"₹{total_downtime_cost/1e5:.1f}L", color="#fc8181")
    kpi_card(col4, "Fleet Size", f"{n_vehicles} Vehicles", color="#f6ad55")
    kpi_card(col5, "Avg Wait (Charging)", f"{avg_downtime_wait:.0f} min", color="#b794f4")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Revenue vs Downtime Cost by Zone ────────────────────────────────────
    col_a, col_b = st.columns([3, 2])

    with col_a:
        zone_agg = (
            fleet.groupby("zone")
            .agg(revenue=("total_revenue", "sum"), loss=("downtime_cost", "sum"))
            .reset_index()
            .sort_values("revenue", ascending=True)
        )
        fig = go.Figure()
        fig.add_bar(
            y=zone_agg["zone"], x=zone_agg["revenue"],
            name="Revenue", marker_color="#48bb78", orientation="h",
        )
        fig.add_bar(
            y=zone_agg["zone"], x=-zone_agg["loss"],
            name="Downtime Loss", marker_color="#fc8181", orientation="h",
        )
        fig.update_layout(
            title="Revenue vs Downtime Loss by Zone",
            barmode="overlay",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0", height=340,
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="INR"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        # Trip distribution by vehicle type
        type_agg = fleet.groupby("vehicle_type")["trip_count"].sum().reset_index()
        fig2 = px.pie(
            type_agg, names="vehicle_type", values="trip_count",
            color_discrete_sequence=["#63b3ed", "#48bb78", "#f6ad55"],
            hole=0.55,
        )
        fig2.update_layout(
            title="Trips by Vehicle Type",
            paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0", height=340,
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        fig2.update_traces(textfont_color="#e2e8f0")
        st.plotly_chart(fig2, use_container_width=True)

    # ── Daily trend ──────────────────────────────────────────────────────────
    daily = (
        fleet.groupby("date")
        .agg(revenue=("total_revenue", "sum"), trips=("trip_count", "sum"))
        .reset_index()
    )
    fig3 = go.Figure()
    fig3.add_scatter(
        x=daily["date"], y=daily["revenue"], name="Daily Revenue",
        line=dict(color="#48bb78", width=2), fill="tozeroy",
        fillcolor="rgba(72,187,120,0.08)",
    )
    fig3.update_layout(
        title="Daily Revenue Trend",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e2e8f0", height=260,
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="INR"),
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Executive summary ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📋 Executive Summary")
    loss_pct = total_downtime_cost / total_revenue * 100
    worst_zone = zones.nlargest(1, "downtime_risk_score")["zone"].values[0]
    st.info(
        f"**Fleet of {n_vehicles} e-rickshaws** completed **{total_trips:,} trips** generating "
        f"**₹{total_revenue/1e5:.1f} lakh** gross revenue over a 60-day simulation window. "
        f"**Charging downtime losses** account for **{loss_pct:.1f}%** of gross revenue "
        f"(₹{total_downtime_cost/1e5:.1f}L). Zone **{worst_zone}** shows the highest downtime risk "
        f"due to poor charger proximity. Deploying 3–5 new charging hubs in high-risk zones is "
        f"estimated to recover **15–25%** of current downtime losses. See the Scenario Simulator for ROI."
    )
