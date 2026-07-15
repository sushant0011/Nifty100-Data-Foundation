"""
06_sectors.py — Sector Analysis Screen for Nifty100 Dashboard.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src.dashboard.utils.db import get_companies, get_latest_ratios, get_sectors

st.set_page_config(page_title="Sector Analysis", layout="wide")
st.title("Sector Analysis")
st.markdown("---")

# Load data
companies = get_companies()
ratios = get_latest_ratios()
sectors = get_sectors()

# Merge
df = ratios.merge(
    companies[["ticker", "company_name", "broad_sector", "sub_sector"]],
    left_on="company_id", right_on="ticker", how="left"
)

# ── Sector Selector ────────────────────────────────────────────────────────
sector_list = sorted(df["broad_sector"].dropna().unique().tolist())
selected_sector = st.selectbox("Select Sector", ["All Sectors"] + sector_list)

if selected_sector != "All Sectors":
    sector_df = df[df["broad_sector"] == selected_sector].copy()
else:
    sector_df = df.copy()

st.markdown(f"**{len(sector_df)} companies** in selected view")
st.markdown("---")

# ── Bubble Chart ───────────────────────────────────────────────────────────
st.subheader("Revenue vs ROE — Bubble Chart (size = Market Cap proxy)")

bubble_df = sector_df.dropna(subset=["return_on_equity_pct", "cash_from_operations_cr"]).copy()

if not bubble_df.empty:
    bubble_df["bubble_size"] = bubble_df["total_debt_cr"].fillna(100).abs().clip(lower=10) + 10

    fig_bubble = px.scatter(
        bubble_df,
        x="cash_from_operations_cr",
        y="return_on_equity_pct",
        size="bubble_size",
        color="broad_sector" if selected_sector == "All Sectors" else "sub_sector",
        hover_name="company_id",
        hover_data={
            "company_name": True,
            "return_on_equity_pct": ":.2f",
            "cash_from_operations_cr": ":.2f",
            "bubble_size": False,
        },
        labels={
            "cash_from_operations_cr": "Cash from Operations (Cr)",
            "return_on_equity_pct": "ROE %",
        },
        title=f"Sector Bubble Chart — {selected_sector}",
        height=500,
    )
    fig_bubble.update_layout(showlegend=True)
    st.plotly_chart(fig_bubble, use_container_width=True)
else:
    st.warning("Not enough data to render bubble chart.")

st.markdown("---")

# ── Sector Median KPI Bar Chart ────────────────────────────────────────────
st.subheader("Sector Median KPIs")

KPI_COLS = {
    "return_on_equity_pct": "ROE %",
    "net_profit_margin_pct": "NPM %",
    "debt_to_equity": "D/E",
    "revenue_cagr_5yr": "Rev CAGR 5yr %",
    "composite_quality_score": "Quality Score",
}

selected_kpi_label = st.selectbox(
    "Select KPI for Sector Comparison",
    list(KPI_COLS.values())
)
selected_kpi_col = {v: k for k, v in KPI_COLS.items()}[selected_kpi_label]

if selected_kpi_col in df.columns:
    sector_median = (
        df.groupby("broad_sector")[selected_kpi_col]
        .median()
        .dropna()
        .sort_values(ascending=False)
        .reset_index()
    )
    sector_median.columns = ["Sector", selected_kpi_label]

    fig_bar = px.bar(
        sector_median,
        x="Sector",
        y=selected_kpi_label,
        color="Sector",
        title=f"Sector Median — {selected_kpi_label}",
        height=400,
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    fig_bar.update_layout(showlegend=False, xaxis_tickangle=-30)
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# ── Sector Summary Table ───────────────────────────────────────────────────
st.subheader("Sector Summary Table")

summary = df.groupby("broad_sector").agg(
    Companies=("company_id", "count"),
    Avg_ROE=("return_on_equity_pct", "mean"),
    Median_DE=("debt_to_equity", "median"),
    Median_NPM=("net_profit_margin_pct", "median"),
    Median_RevCAGR=("revenue_cagr_5yr", "median"),
    Avg_QualityScore=("composite_quality_score", "mean"),
).round(2).reset_index()

summary.columns = [
    "Sector", "Companies", "Avg ROE %",
    "Median D/E", "Median NPM %",
    "Median Rev CAGR 5yr %", "Avg Quality Score"
]

st.dataframe(summary.sort_values("Avg Quality Score", ascending=False),
             use_container_width=True)