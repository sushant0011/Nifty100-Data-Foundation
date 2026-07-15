"""
03_screener.py — Screener Screen for Nifty100 Dashboard.
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src.dashboard.utils.db import get_companies, get_latest_ratios, safe_val

st.set_page_config(page_title="Screener", layout="wide")
st.title("Investment Screener")
st.markdown("---")

# Load data
companies = get_companies()
ratios = get_latest_ratios()
df = ratios.merge(companies[["ticker", "company_name", "broad_sector"]],
                  left_on="company_id", right_on="ticker", how="left")

# ── Preset Buttons ─────────────────────────────────────────────────────────
st.subheader("Presets")
col1, col2, col3, col4, col5, col6 = st.columns(6)

presets = {
    "Quality": {"roe_min": 15.0, "de_max": 1.0, "fcf_min": 0.0, "rev_cagr_min": 10.0},
    "Value": {"de_max": 2.0},
    "Growth": {"pat_cagr_min": 20.0, "rev_cagr_min": 15.0, "de_max": 2.0},
    "Dividend": {"fcf_min": 0.0},
    "Debt-Free": {"de_max": 0.1, "roe_min": 12.0},
    "Turnaround": {"rev_cagr_min": 10.0, "fcf_min": 0.0},
}

if "filters" not in st.session_state:
    st.session_state.filters = {}

with col1:
    if st.button("Quality Compounder"):
        st.session_state.filters = presets["Quality"]
with col2:
    if st.button("Value Pick"):
        st.session_state.filters = presets["Value"]
with col3:
    if st.button("Growth Accelerator"):
        st.session_state.filters = presets["Growth"]
with col4:
    if st.button("Dividend Champion"):
        st.session_state.filters = presets["Dividend"]
with col5:
    if st.button("Debt Free Blue Chip"):
        st.session_state.filters = presets["Debt-Free"]
with col6:
    if st.button("Turnaround Watch"):
        st.session_state.filters = presets["Turnaround"]

st.markdown("---")

# ── Sidebar Sliders ────────────────────────────────────────────────────────
st.sidebar.header("Filter Metrics")

f = st.session_state.filters

roe_min = st.sidebar.slider(
    "ROE Min (%)", -50.0, 100.0,
    float(f.get("roe_min", 0.0)), step=0.5
)
de_max = st.sidebar.slider(
    "D/E Max", 0.0, 10.0,
    float(f.get("de_max", 10.0)), step=0.1
)
fcf_min = st.sidebar.slider(
    "FCF Min (Cr)", -5000.0, 10000.0,
    float(f.get("fcf_min", -5000.0)), step=100.0
)
rev_cagr_min = st.sidebar.slider(
    "Revenue CAGR 5yr Min (%)", -20.0, 50.0,
    float(f.get("rev_cagr_min", -20.0)), step=0.5
)
pat_cagr_min = st.sidebar.slider(
    "PAT CAGR 5yr Min (%)", -20.0, 50.0,
    float(f.get("pat_cagr_min", -20.0)), step=0.5
)
opm_min = st.sidebar.slider(
    "OPM Min (%)", -20.0, 60.0,
    float(f.get("opm_min", -20.0)), step=0.5
)
icr_min = st.sidebar.slider(
    "ICR Min", 0.0, 20.0,
    float(f.get("icr_min", 0.0)), step=0.5
)
asset_turnover_min = st.sidebar.slider(
    "Asset Turnover Min", 0.0, 3.0,
    float(f.get("asset_turnover_min", 0.0)), step=0.1
)

# ── Apply Filters ──────────────────────────────────────────────────────────
filtered = df.copy()

if "return_on_equity_pct" in filtered.columns:
    filtered = filtered[filtered["return_on_equity_pct"].fillna(-999) >= roe_min]

if "debt_to_equity" in filtered.columns:
    non_fin = filtered[filtered["broad_sector"].str.lower().fillna("") != "financials"]
    fin = filtered[filtered["broad_sector"].str.lower().fillna("") == "financials"]
    non_fin = non_fin[non_fin["debt_to_equity"].fillna(999) <= de_max]
    filtered = pd.concat([non_fin, fin], ignore_index=True)

if "free_cash_flow_cr" in filtered.columns:
    filtered = filtered[filtered["free_cash_flow_cr"].fillna(-999999) >= fcf_min]

if "revenue_cagr_5yr" in filtered.columns:
    filtered = filtered[filtered["revenue_cagr_5yr"].fillna(-999) >= rev_cagr_min]

if "pat_cagr_5yr" in filtered.columns:
    filtered = filtered[filtered["pat_cagr_5yr"].fillna(-999) >= pat_cagr_min]

if "operating_profit_margin_pct" in filtered.columns:
    filtered = filtered[filtered["operating_profit_margin_pct"].fillna(-999) >= opm_min]

if "interest_coverage" in filtered.columns:
    debt_free_mask = filtered["icr_label"] == "Debt Free"
    icr_mask = filtered["interest_coverage"].fillna(-999) >= icr_min
    filtered = filtered[debt_free_mask | icr_mask]

if "asset_turnover" in filtered.columns:
    filtered = filtered[filtered["asset_turnover"].fillna(-999) >= asset_turnover_min]

# ── Results ────────────────────────────────────────────────────────────────
st.subheader(f"{len(filtered)} companies match your filters")

display_cols = {
    "company_id": "Ticker",
    "company_name": "Company",
    "broad_sector": "Sector",
    "composite_quality_score": "Quality Score",
    "return_on_equity_pct": "ROE %",
    "debt_to_equity": "D/E",
    "free_cash_flow_cr": "FCF (Cr)",
    "revenue_cagr_5yr": "Rev CAGR 5yr %",
    "pat_cagr_5yr": "PAT CAGR 5yr %",
    "operating_profit_margin_pct": "OPM %",
    "interest_coverage": "ICR",
    "asset_turnover": "Asset Turnover",
}

available = [c for c in display_cols if c in filtered.columns]
show_df = filtered[available].copy()
show_df = show_df.rename(columns=display_cols)
show_df = show_df.sort_values("Quality Score", ascending=False).reset_index(drop=True)
show_df.index += 1

for col in show_df.select_dtypes(include="float").columns:
    show_df[col] = show_df[col].apply(lambda x: round(x, 2) if pd.notna(x) else "N/A")

st.dataframe(show_df, use_container_width=True, height=500)

# ── CSV Download ───────────────────────────────────────────────────────────
csv = show_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download CSV",
    data=csv,
    file_name="screener_results.csv",
    mime="text/csv",
)