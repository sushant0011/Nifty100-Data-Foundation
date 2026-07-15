"""
02_profile.py — Company Profile Screen for Nifty100 Dashboard.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src.dashboard.utils.db import (
    get_companies, get_ratios, get_pl, get_pros_cons, safe_val
)

st.set_page_config(page_title="Company Profile", layout="wide")
st.title("Company Profile")
st.markdown("---")

# Load companies for search
companies = get_companies()
ticker_list = sorted(companies["ticker"].tolist())
name_list = companies["company_name"].tolist()

# Search box
search = st.text_input("Search by Ticker or Company Name", placeholder="e.g. TCS or Tata")

# Filter matching companies
if search:
    mask = (
        companies["ticker"].str.upper().str.contains(search.upper(), na=False) |
        companies["company_name"].str.upper().str.contains(search.upper(), na=False)
    )
    filtered = companies[mask]
else:
    filtered = companies

if filtered.empty:
    st.warning("Ticker not found — please try another")
    st.stop()

# Dropdown for selection
selected_ticker = st.selectbox(
    "Select Company",
    options=filtered["ticker"].tolist(),
    format_func=lambda t: f"{t} — {companies[companies['ticker']==t]['company_name'].values[0]}"
)

if not selected_ticker:
    st.info("Please search and select a company above.")
    st.stop()

# Load company info
co = companies[companies["ticker"] == selected_ticker].iloc[0]
ratios = get_ratios(ticker=selected_ticker)
pl = get_pl(ticker=selected_ticker)

if ratios.empty:
    st.warning(f"Ticker not found — please try another")
    st.stop()

latest = ratios.sort_values("year").iloc[-1]

# ── Company Card ───────────────────────────────────────────────────────────
st.subheader(f"{co['company_name']} ({selected_ticker})")

card_col1, card_col2 = st.columns([2, 1])
with card_col1:
    st.markdown(f"**Sector:** {co.get('broad_sector', 'N/A')}")
    st.markdown(f"**Sub-sector:** {co.get('sub_sector', 'N/A')}")
    about = co.get("about_company", "")
    if about and str(about) != "nan":
        st.markdown(f"**About:** {about[:500]}...")

with card_col2:
    nse = co.get("nse_profile", "")
    bse = co.get("bse_profile", "")
    if nse and str(nse) != "nan":
        st.markdown(f"[NSE Profile]({nse})")
    if bse and str(bse) != "nan":
        st.markdown(f"[BSE Profile]({bse})")

st.markdown("---")

# ── 6 KPI Tiles ────────────────────────────────────────────────────────────
st.subheader("Key Metrics (Latest Year)")
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("ROE", safe_val(latest.get("return_on_equity_pct"), suffix="%"))
k2.metric("ROCE", safe_val(latest.get("return_on_capital_employed_pct"), suffix="%"))
k3.metric("Net Profit Margin", safe_val(latest.get("net_profit_margin_pct"), suffix="%"))
k4.metric("D/E", safe_val(latest.get("debt_to_equity")))
k5.metric("Revenue CAGR 5yr", safe_val(latest.get("revenue_cagr_5yr"), suffix="%"))
k6.metric("FCF (Cr)", safe_val(latest.get("free_cash_flow_cr")))

st.markdown("---")

# ── Revenue and Net Profit Bar Chart ──────────────────────────────────────
if not pl.empty:
    st.subheader("Revenue and Net Profit (10 Years)")
    pl_sorted = pl.sort_values("year").tail(10)

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=pl_sorted["year"],
        y=pl_sorted["sales"],
        name="Revenue",
        marker_color="#1f77b4"
    ))
    fig_bar.add_trace(go.Bar(
        x=pl_sorted["year"],
        y=pl_sorted["net_profit"],
        name="Net Profit",
        marker_color="#2ca02c"
    ))
    fig_bar.update_layout(
        barmode="group",
        xaxis_title="Year",
        yaxis_title="Crore (Rs)",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ── ROE and ROCE Dual Axis Line Chart ─────────────────────────────────────
if not ratios.empty:
    st.subheader("ROE and ROCE Trend (10 Years)")
    r_sorted = ratios.sort_values("year").tail(10)

    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=r_sorted["year"],
        y=r_sorted["return_on_equity_pct"],
        name="ROE %",
        mode="lines+markers",
        line=dict(color="#1f77b4", width=2)
    ))
    fig_line.add_trace(go.Scatter(
        x=r_sorted["year"],
        y=r_sorted["return_on_capital_employed_pct"],
        name="ROCE %",
        mode="lines+markers",
        line=dict(color="#ff7f0e", width=2)
    ))
    fig_line.update_layout(
        xaxis_title="Year",
        yaxis_title="Percentage (%)",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    st.plotly_chart(fig_line, use_container_width=True)

# ── Pros and Cons ──────────────────────────────────────────────────────────
pros_cons = get_pros_cons(selected_ticker)
if not pros_cons.empty:
    st.markdown("---")
    st.subheader("Pros and Cons")
    pc1, pc2 = st.columns(2)

    with pc1:
        st.markdown("**Strengths**")
        pros = pros_cons[pros_cons["type"].str.lower() == "pro"] if "type" in pros_cons.columns else pd.DataFrame()
        if not pros.empty:
            for _, row in pros.iterrows():
                point = row.get("point", row.get("description", ""))
                st.markdown(f"- {point}")
        else:
            st.info("No pros data available")

    with pc2:
        st.markdown("**Concerns**")
        cons = pros_cons[pros_cons["type"].str.lower() == "con"] if "type" in pros_cons.columns else pd.DataFrame()
        if not cons.empty:
            for _, row in cons.iterrows():
                point = row.get("point", row.get("description", ""))
                st.markdown(f"- {point}")
        else:
            st.info("No cons data available")