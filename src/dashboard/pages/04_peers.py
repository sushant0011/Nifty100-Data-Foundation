"""
04_peers.py — Peer Comparison Screen for Nifty100 Dashboard.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src.dashboard.utils.db import (
    get_companies, get_peers, get_peer_groups, safe_val
)

st.set_page_config(page_title="Peer Comparison", layout="wide")
st.title("Peer Comparison")
st.markdown("---")

companies = get_companies()
peer_groups = get_peer_groups()

if not peer_groups:
    st.warning("No peer groups found in database.")
    st.stop()

# ── Selections ─────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    selected_group = st.selectbox("Select Peer Group", peer_groups)

peers_df = get_peers(selected_group)

if peers_df.empty:
    st.warning(f"No data found for peer group: {selected_group}")
    st.stop()

with col2:
    selected_ticker = st.selectbox(
        "Select Company",
        peers_df["company_id"].tolist(),
        format_func=lambda t: f"{t} — {peers_df[peers_df['company_id']==t]['company_name'].values[0] if not peers_df[peers_df['company_id']==t].empty else t}"
    )

st.markdown("---")

# ── Radar Chart ────────────────────────────────────────────────────────────
st.subheader(f"Radar Chart — {selected_ticker} vs {selected_group} Average")

RADAR_METRICS = [
    ("return_on_equity_pct", "ROE %"),
    ("return_on_capital_employed_pct", "ROCE %"),
    ("net_profit_margin_pct", "NPM %"),
    ("debt_to_equity", "D/E"),
    ("free_cash_flow_cr", "FCF"),
    ("pat_cagr_5yr", "PAT CAGR 5yr"),
    ("revenue_cagr_5yr", "Rev CAGR 5yr"),
    ("composite_quality_score", "Quality Score"),
]

def winsorise_scale(series):
    import numpy as np
    low = np.nanpercentile(series.dropna(), 10)
    high = np.nanpercentile(series.dropna(), 90)
    clipped = series.clip(lower=low, upper=high)
    mn, mx = clipped.min(), clipped.max()
    if mx == mn:
        return pd.Series([50.0] * len(series), index=series.index)
    return (clipped - mn) / (mx - mn) * 100

scaled = peers_df.copy()
for col, _ in RADAR_METRICS:
    if col in scaled.columns:
        scaled[col + "_s"] = winsorise_scale(scaled[col].fillna(scaled[col].median()))

labels = [label for _, label in RADAR_METRICS]
company_row = scaled[scaled["company_id"] == selected_ticker]
peer_avg = scaled[[col + "_s" for col, _ in RADAR_METRICS if col + "_s" in scaled.columns]].mean()

if not company_row.empty:
    company_vals = [
        float(company_row[col + "_s"].values[0])
        if col + "_s" in company_row.columns and pd.notna(company_row[col + "_s"].values[0])
        else 50.0
        for col, _ in RADAR_METRICS
    ]
    peer_vals = [
        float(peer_avg.get(col + "_s", 50.0))
        for col, _ in RADAR_METRICS
    ]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=company_vals + [company_vals[0]],
        theta=labels + [labels[0]],
        fill="toself",
        name=selected_ticker,
        line=dict(color="#1f77b4", width=2),
        fillcolor="rgba(31, 119, 180, 0.2)"
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=peer_vals + [peer_vals[0]],
        theta=labels + [labels[0]],
        fill="toself",
        name=f"{selected_group} Avg",
        line=dict(color="#ff7f0e", width=2, dash="dash"),
        fillcolor="rgba(255, 127, 14, 0.1)"
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        height=500,
    )
    st.plotly_chart(fig_radar, use_container_width=True)

st.markdown("---")

# ── KPI Comparison Table ───────────────────────────────────────────────────
st.subheader(f"KPI Comparison — {selected_group}")

display_cols = {
    "company_id": "Ticker",
    "company_name": "Company",
    "return_on_equity_pct": "ROE %",
    "return_on_capital_employed_pct": "ROCE %",
    "net_profit_margin_pct": "NPM %",
    "debt_to_equity": "D/E",
    "free_cash_flow_cr": "FCF (Cr)",
    "pat_cagr_5yr": "PAT CAGR 5yr %",
    "revenue_cagr_5yr": "Rev CAGR 5yr %",
    "composite_quality_score": "Quality Score",
}

available = [c for c in display_cols if c in peers_df.columns]
show_df = peers_df[available].copy()
show_df = show_df.rename(columns=display_cols)
show_df = show_df.sort_values("Quality Score", ascending=False).reset_index(drop=True)
show_df.index += 1

for col in show_df.select_dtypes(include="float").columns:
    show_df[col] = show_df[col].apply(lambda x: round(x, 2) if pd.notna(x) else "N/A")

def highlight_selected(row):
    if row.get("Ticker") == selected_ticker:
        return ["background-color: #fff3cd"] * len(row)
    return [""] * len(row)

st.dataframe(
    show_df.style.apply(highlight_selected, axis=1),
    use_container_width=True
)