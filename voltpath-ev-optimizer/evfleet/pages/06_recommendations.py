"""pages/06_recommendations.py — Business Recommendations Summary"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def render(fleet: pd.DataFrame, zones: pd.DataFrame, hubs: pd.DataFrame, chargers: pd.DataFrame) -> None:
    st.markdown("## 💡 Recommendations & Business Intelligence")
    st.markdown(
        "<p style='color:#94a3b8;margin-top:-12px;'>Prioritized actions for fleet operators, infrastructure planners, and EV startups</p>",
        unsafe_allow_html=True,
    )

    # ── Priority Hub Placement Cards ─────────────────────────────────────────
    st.markdown("### 🔋 Priority Charging Hub Placements")
    st.markdown("Locations ranked by estimated downtime cost savings (based on clustering of high-demand, high-wait zones).")

    hubs_sorted = hubs.sort_values("priority_rank")
    for _, row in hubs_sorted.iterrows():
        savings = row.get("estimated_annual_savings", 0)
        rank = int(row["priority_rank"])
        zone = row["zone_proximity"]
        color = "#fc8181" if rank == 1 else "#f6ad55" if rank == 2 else "#48bb78"
        badge = "🔴 CRITICAL" if rank == 1 else "🟠 HIGH" if rank == 2 else "🟢 MEDIUM"
        st.markdown(
            f"""<div style="background:rgba(15,23,42,0.7);border-left:4px solid {color};
            border-radius:10px;padding:16px 20px;margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <span style="color:{color};font-weight:700;font-size:16px;">Hub #{rank} — {zone}</span>
                    <span style="margin-left:12px;background:rgba(255,255,255,0.08);padding:2px 10px;border-radius:20px;font-size:12px;">{badge}</span>
                </div>
                <div style="text-align:right;">
                    <p style="color:#48bb78;font-size:18px;font-weight:700;margin:0;">₹{savings:,.0f}</p>
                    <p style="color:#94a3b8;font-size:11px;margin:0;">Est. Annual Savings</p>
                </div>
            </div>
            <p style="color:#94a3b8;font-size:12px;margin:8px 0 0;">
                📍 {row['lat']:.4f}, {row['lon']:.4f}
            </p>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Zone Action Matrix ────────────────────────────────────────────────────
    st.markdown("### 📊 Zone Action Priority Matrix")
    if "nearest_charger_km" in zones.columns and "avg_demand_score" in zones.columns:
        fig = px.scatter(
            zones,
            x="avg_demand_score",
            y="nearest_charger_km",
            size="total_downtime_cost",
            color="downtime_risk_score",
            color_continuous_scale=["#48bb78", "#f6ad55", "#fc8181"],
            text="zone",
            title="Demand vs Charger Distance — Action Quadrant",
            labels={
                "avg_demand_score": "Avg Demand Score →",
                "nearest_charger_km": "Distance to Nearest Charger (km) ↑",
                "downtime_risk_score": "Risk Score",
            },
        )
        fig.update_traces(textposition="top center", textfont=dict(size=10, color="#e2e8f0"))
        fig.add_hline(y=zones["nearest_charger_km"].median(), line_dash="dash", line_color="#94a3b8", annotation_text="Median Distance")
        fig.add_vline(x=zones["avg_demand_score"].median(), line_dash="dash", line_color="#94a3b8", annotation_text="Median Demand")
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0", height=420,
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Top-right quadrant = HIGH DEMAND + FAR from chargers = most urgent for new infrastructure.")

    # ── Strategic Recommendations ─────────────────────────────────────────────
    st.markdown("### 📋 Strategic Recommendations")

    recommendations = [
        {
            "icon": "⚡",
            "title": "Deploy Battery Swap Hubs at Top 3 Risk Zones",
            "detail": f"Zones like {zones.nlargest(3,'downtime_risk_score')['zone'].tolist()} show the highest charger-gap + demand combination. Battery swap stations can cut charging wait from 90+ minutes to under 5 minutes.",
            "impact": "HIGH",
            "timeline": "3–6 months",
        },
        {
            "icon": "🗺️",
            "title": "Align Charging Hours with Peak Trip Windows",
            "detail": "Fleet data shows weekday morning and evening peaks. Prioritizing charging access during off-peak windows (11am–2pm) reduces congestion at chargers and shortens vehicle idle time.",
            "impact": "MEDIUM",
            "timeline": "Immediate (Policy)",
        },
        {
            "icon": "📡",
            "title": "Install IoT Battery Monitors for Predictive Charging",
            "detail": "Vehicles ending day below 20% battery face next-morning delays. Simple telematics integration allows dispatchers to pre-route to chargers before batteries hit critical levels.",
            "impact": "HIGH",
            "timeline": "6–12 months",
        },
        {
            "icon": "🤝",
            "title": "Partner with MSEDCL / Tata Power for Grid Integration",
            "detail": "Coordinating charging schedules with local DISCOMs reduces peak grid load and can qualify for EV tariff incentives under India's National EV Policy 2023.",
            "impact": "MEDIUM",
            "timeline": "12–18 months",
        },
        {
            "icon": "💰",
            "title": "Apply for FAME-II / State EV Infrastructure Subsidies",
            "detail": "The FAME-II scheme and Maharashtra EV Policy offer capital subsidies for public charging infrastructure. Eligible operators can reduce effective CapEx by 20–40%.",
            "impact": "HIGH",
            "timeline": "Ongoing",
        },
    ]

    impact_color = {"HIGH": "#48bb78", "MEDIUM": "#f6ad55", "LOW": "#94a3b8"}
    for r in recommendations:
        color = impact_color.get(r["impact"], "#94a3b8")
        st.markdown(
            f"""<div style="background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.08);
            border-radius:10px;padding:16px 20px;margin-bottom:10px;">
            <div style="display:flex;gap:14px;align-items:flex-start;">
                <span style="font-size:24px;">{r['icon']}</span>
                <div style="flex:1;">
                    <p style="color:#e2e8f0;font-weight:600;font-size:15px;margin:0;">{r['title']}</p>
                    <p style="color:#94a3b8;font-size:13px;margin:6px 0 8px;">{r['detail']}</p>
                    <span style="background:rgba(255,255,255,0.06);color:{color};padding:2px 10px;border-radius:20px;font-size:12px;">Impact: {r['impact']}</span>
                    <span style="margin-left:8px;color:#64748b;font-size:12px;">⏱ {r['timeline']}</span>
                </div>
            </div></div>""",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown(
        "<p style='color:#64748b;font-size:12px;'>All recommendations are based on simulated synthetic data for portfolio/educational demonstration. "
        "No real operator, DISCOM, or government partnership is implied or claimed.</p>",
        unsafe_allow_html=True,
    )
