"""
01_home.py — Home Screen for Nifty100 Dashboard.

Shows: 6 KPI tiles, sector donut chart, top-5 companies by composite score.
"""

import streamlit as st
import plotly.express as px
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src.dashboard.utils.db import (
    get_companies, get_latest_ratios, get_sectors, safe_val
)

st.set_page_config(page_title="Home", layout="wide")
st.title("Market Overview")
st.markdown("---")

# Year selector in sidebar
year = st.sidebar.selectbox("Select Year", list(range(2024, 2018, -1)), index=0)

# Load data
companies = get_companies()
ratios = get_latest_ratios(year=year)

if ratios.empty:
    st.warning(f"No data available for year {year}. Showing latest available.")
    ratios = get_latest_ratios()

# Merge with company names
df = ratios.merge(companies[["ticker", "company_name", "broad_sector"]], 
                  left_on="company_id", right_on="ticker", how="left")

# ── 6 KPI Tiles ────────────────────────────────────────────────────────────
st.subheader("Key Metrics")
col1, col2, col3, col4, col5, col6 = st.columns(6)

avg_roe = df["return_on_equity_pct"].mean()
median_de = df["debt_to_equity"].median()
median_rev_cagr = df["revenue_cagr_5yr"].median()
total_companies = len(df["company_id"].unique())
debt_free = len(df[df["debt_to_equity"] <= 0.1])
median_npm = df["net_profit_margin_pct"].median()

col1.metric("Average ROE", safe_val(avg_roe, suffix="%"))
col2.metric("Median Net Profit Margin", safe_val(median_npm, suffix="%"))
col3.metric("Median D/E", safe_val(median_de))
col4.metric("Total Companies", str(total_companies))
col5.metric("Median Revenue CAGR 5yr", safe_val(median_rev_cagr, suffix="%"))
col6.metric("Debt-Free Companies", str(debt_free))

st.markdown("---")

# ── Two Column Layout ──────────────────────────────────────────────────────
left, right = st.columns([1, 1])

# Sector Donut Chart
with left:
    st.subheader("Sector Breakdown")
    sectors = get_sectors()
    if not sectors.empty:
        fig = px.pie(
            sectors,
            names="broad_sector",
            values="company_count",
            hole=0.4,
            title="Companies by Sector",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

# Top 5 by Composite Score
with right:
    st.subheader("Top 5 Companies by Quality Score")
    if "composite_quality_score" in df.columns:
        top5 = (
            df[["company_id", "company_name", "broad_sector",
                "composite_quality_score", "return_on_equity_pct",
                "debt_to_equity", "revenue_cagr_5yr"]]
            .dropna(subset=["composite_quality_score"])
            .sort_values("composite_quality_score", ascending=False)
            .head(5)
            .reset_index(drop=True)
        )
        top5.index += 1
        top5.columns = ["Ticker", "Company", "Sector",
                        "Quality Score", "ROE %", "D/E", "Rev CAGR 5yr %"]
        st.dataframe(top5, use_container_width=True)

st.markdown("---")

# ── All Companies Table ────────────────────────────────────────────────────
st.subheader("All Companies Overview")

display_cols = {
    "company_id": "Ticker",
    "company_name": "Company",
    "broad_sector": "Sector",
    "return_on_equity_pct": "ROE %",
    "debt_to_equity": "D/E",
    "net_profit_margin_pct": "NPM %",
    "revenue_cagr_5yr": "Rev CAGR 5yr %",
    "composite_quality_score": "Quality Score",
}

available = [c for c in display_cols if c in df.columns]
show_df = df[available].copy()
show_df = show_df.rename(columns=display_cols)
show_df = show_df.sort_values("Quality Score", ascending=False).reset_index(drop=True)
show_df.index += 1

for col in ["ROE %", "D/E", "NPM %", "Rev CAGR 5yr %", "Quality Score"]:
    if col in show_df.columns:
        show_df[col] = show_df[col].apply(lambda x: round(x, 2) if pd.notna(x) else "N/A")

st.dataframe(show_df, use_container_width=True, height=400)