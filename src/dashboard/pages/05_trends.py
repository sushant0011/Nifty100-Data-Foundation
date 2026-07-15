"""
05_trends.py — Trend Analysis Screen for Nifty100 Dashboard.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src.dashboard.utils.db import get_companies, get_ratios

st.set_page_config(page_title="Trend Analysis", layout="wide")
st.title("Trend Analysis")
st.markdown("---")

companies = get_companies()

# ── Company Search ─────────────────────────────────────────────────────────
search = st.text_input("Search by Ticker or Company Name", placeholder="e.g. INFY")

if search:
    mask = (
        companies["ticker"].str.upper().str.contains(search.upper(), na=False) |
        companies["company_name"].str.upper().str.contains(search.upper(), na=False)
    )
    filtered = companies[mask]
else:
    filtered = companies

if filtered.empty:
    st.warning("No company found. Please try another search.")
    st.stop()

selected_ticker = st.selectbox(
    "Select Company",
    options=filtered["ticker"].tolist(),
    format_func=lambda t: f"{t} — {companies[companies['ticker']==t]['company_name'].values[0]}"
)

# ── Metric Selector ────────────────────────────────────────────────────────
AVAILABLE_METRICS = {
    "ROE %": "return_on_equity_pct",
    "ROCE %": "return_on_capital_employed_pct",
    "Net Profit Margin %": "net_profit_margin_pct",
    "D/E Ratio": "debt_to_equity",
    "Revenue CAGR 5yr %": "revenue_cagr_5yr",
    "PAT CAGR 5yr %": "pat_cagr_5yr",
    "EPS CAGR 5yr %": "eps_cagr_5yr",
    "FCF (Cr)": "free_cash_flow_cr",
    "Asset Turnover": "asset_turnover",
    "Interest Coverage": "interest_coverage",
    "OPM %": "operating_profit_margin_pct",
    "Composite Quality Score": "composite_quality_score",
}

selected_metrics = st.multiselect(
    "Select up to 3 Metrics to Compare",
    options=list(AVAILABLE_METRICS.keys()),
    default=["ROE %", "ROCE %"],
    max_selections=3,
)

if not selected_metrics:
    st.info("Please select at least one metric.")
    st.stop()

# ── Load Data ──────────────────────────────────────────────────────────────
ratios = get_ratios(ticker=selected_ticker)

if ratios.empty:
    st.warning("No data available for this company.")
    st.stop()

ratios = ratios.sort_values("year")

# Check data availability
available_years = len(ratios)
if available_years < 10:
    st.info(f"Data available for {available_years} years (fewer than 10 years of history).")

st.markdown("---")

# ── Trend Chart ────────────────────────────────────────────────────────────
st.subheader(f"10-Year Trend — {selected_ticker}")

fig = go.Figure()

colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

for i, metric_label in enumerate(selected_metrics):
    col = AVAILABLE_METRICS[metric_label]
    if col not in ratios.columns:
        st.warning(f"Metric {metric_label} not available in data.")
        continue

    series = ratios[["year", col]].dropna(subset=[col])

    if series.empty:
        st.warning(f"No data for {metric_label}.")
        continue

    # YoY % change annotation
    series = series.copy()
    series["yoy_change"] = series[col].pct_change() * 100

    annotations = []
    for _, row in series.iterrows():
        if pd.notna(row["yoy_change"]):
            sign = "+" if row["yoy_change"] >= 0 else ""
            annotations.append(f"{sign}{row['yoy_change']:.1f}%")
        else:
            annotations.append("")

    fig.add_trace(go.Scatter(
        x=series["year"],
        y=series[col],
        name=metric_label,
        mode="lines+markers+text",
        text=annotations,
        textposition="top center",
        textfont=dict(size=9),
        line=dict(color=colors[i % len(colors)], width=2),
        marker=dict(size=6),
    ))

fig.update_layout(
    xaxis_title="Year",
    yaxis_title="Value",
    height=500,
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
)

st.plotly_chart(fig, use_container_width=True)

# ── Raw Data Table ─────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Raw Data")

cols_to_show = ["year"] + [
    AVAILABLE_METRICS[m] for m in selected_metrics
    if AVAILABLE_METRICS[m] in ratios.columns
]
raw = ratios[cols_to_show].copy()
raw = raw.rename(columns={v: k for k, v in AVAILABLE_METRICS.items()})

for col in raw.select_dtypes(include="float").columns:
    raw[col] = raw[col].apply(lambda x: round(x, 2) if pd.notna(x) else "N/A")

st.dataframe(raw.sort_values("year", ascending=False).reset_index(drop=True),
             use_container_width=True)