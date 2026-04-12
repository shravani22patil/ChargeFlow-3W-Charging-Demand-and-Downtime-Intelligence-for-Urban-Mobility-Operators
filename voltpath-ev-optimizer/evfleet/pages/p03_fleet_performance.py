"""pages/03_fleet_performance.py — Vehicle-level Fleet Analytics"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def render(fleet: pd.DataFrame) -> None:
    st.markdown("## 🚗 Fleet Performance Analytics")
    st.markdown(
        "<p style='color:#94a3b8;margin-top:-12px;'>Vehicle-level utilization, battery patterns, and trip efficiency</p>",
        unsafe_allow_html=True,
    )

    # ── Filters ──────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        zones = ["All"] + sorted(fleet["zone"].unique().tolist())
        selected_zone = st.selectbox("Filter by Zone", zones)
    with col2:
        vtypes = ["All"] + sorted(fleet["vehicle_type"].unique().tolist())
        selected_type = st.selectbox("Vehicle Type", vtypes)
    with col3:
        date_range = st.date_input(
            "Date Range",
            value=[fleet["date"].min(), fleet["date"].max()],
        )

    df = fleet.copy()
    if selected_zone != "All":
        df = df[df["zone"] == selected_zone]
    if selected_type != "All":
        df = df[df["vehicle_type"] == selected_type]
    if len(date_range) == 2:
        df = df[(df["date"] >= pd.Timestamp(date_range[0])) & (df["date"] <= pd.Timestamp(date_range[1]))]

    if df.empty:
        st.warning("No data matches selected filters.")
        return

    # ── KPIs ─────────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    card = "background:rgba(15,23,42,0.7);border:1px solid rgba(99,179,237,0.15);border-radius:10px;padding:16px;text-align:center;"
    for col, label, val, color in [
        (c1, "Avg Trips/Day/Vehicle", f"{df.groupby(['vehicle_id','date'])['trip_count'].sum().mean():.1f}", "#63b3ed"),
        (c2, "Avg Battery End Level", f"{df['battery_level_end'].mean():.1f}%", "#f6ad55"),
        (c3, "Avg Charge Time", f"{df['charge_minutes'].mean():.0f} min", "#b794f4"),
        (c4, "Avg Revenue/Vehicle/Day", f"₹{df.groupby(['vehicle_id','date'])['total_revenue'].sum().mean():.0f}", "#48bb78"),
    ]:
        with col:
            st.markdown(f"<div style='{card}'><p style='color:#94a3b8;font-size:11px;margin:0;text-transform:uppercase;letter-spacing:0.05em;'>{label}</p><p style='color:{color};font-size:22px;font-weight:700;margin:6px 0 0;'>{val}</p></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    # Battery distribution
    with col_a:
        fig = px.histogram(
            df, x="battery_level_end", nbins=25,
            color_discrete_sequence=["#f6ad55"],
            title="Battery Level at End of Day Distribution",
            labels={"battery_level_end": "Battery Level (%)"},
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0", height=300,
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Count"),
        )
        fig.add_vline(x=20, line_dash="dash", line_color="#fc8181", annotation_text="Critical <20%")
        st.plotly_chart(fig, use_container_width=True)

    # Charge time vs trips
    with col_b:
        fig2 = px.scatter(
            df.sample(min(500, len(df)), random_state=42),
            x="trip_count", y="charge_minutes",
            color="vehicle_type",
            color_discrete_sequence=["#63b3ed", "#48bb78", "#f6ad55"],
            opacity=0.65,
            title="Charge Time vs Daily Trip Count",
            labels={"trip_count": "Trips/Day", "charge_minutes": "Charging Minutes"},
        )
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0", height=300,
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Top performers table
    st.markdown("### Top 10 Vehicles by Net Revenue")
    top_vehicles = (
        df.groupby("vehicle_id")
        .agg(
            net_revenue=("net_revenue", "sum"),
            total_trips=("trip_count", "sum"),
            avg_battery=("battery_level_end", "mean"),
            avg_downtime=("downtime_wait_minutes", "mean"),
            vehicle_type=("vehicle_type", "first"),
        )
        .reset_index()
        .nlargest(10, "net_revenue")
    )
    top_vehicles["net_revenue"] = top_vehicles["net_revenue"].apply(lambda x: f"₹{x:,.0f}")
    top_vehicles["avg_battery"] = top_vehicles["avg_battery"].apply(lambda x: f"{x:.1f}%")
    top_vehicles["avg_downtime"] = top_vehicles["avg_downtime"].apply(lambda x: f"{x:.0f} min")
    top_vehicles.columns = ["Vehicle ID", "Net Revenue", "Total Trips", "Avg Battery", "Avg Wait", "Type"]
    st.dataframe(top_vehicles, use_container_width=True, hide_index=True)

    # Demand heatmap by zone and weekday
    st.markdown("### Demand Heatmap — Zone × Day of Week")
    fleet["dow"] = pd.to_datetime(fleet["date"]).dt.day_name()
    heatmap_data = fleet.groupby(["zone", "dow"])["demand_score"].mean().reset_index()
    day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    heatmap_pivot = heatmap_data.pivot(index="zone", columns="dow", values="demand_score").reindex(columns=day_order)
    fig3 = px.imshow(
        heatmap_pivot,
        color_continuous_scale="Blues",
        title="Avg Demand Score by Zone & Weekday",
        aspect="auto",
    )
    fig3.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0", height=320,
        coloraxis_colorbar=dict(title="Score"),
    )
    st.plotly_chart(fig3, use_container_width=True)
