"""
07_capital.py — Capital Allocation Map Screen for Nifty100 Dashboard.
"""

import streamlit as st
import plotly.express as px
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src.dashboard.utils.db import get_companies, get_capital_allocation

st.set_page_config(page_title="Capital Allocation", layout="wide")
st.title("Capital Allocation Map")
st.markdown("---")

companies = get_companies()
cap_df = get_capital_allocation()

if cap_df.empty:
    st.warning("Capital allocation data not found. Please run the ratio engine first.")
    st.stop()

# Get latest year per company
if "year" in cap_df.columns:
    cap_df = cap_df.sort_values("year").groupby("company_id").last().reset_index()

# Merge with company names
cap_df = cap_df.merge(
    companies[["ticker", "company_name", "broad_sector"]],
    left_on="company_id", right_on="ticker", how="left"
)

# ── Treemap ────────────────────────────────────────────────────────────────
st.subheader("Capital Allocation Treemap — 92 Companies")

if "pattern_label" not in cap_df.columns:
    st.warning("pattern_label column not found in capital allocation data.")
    st.stop()

cap_df["count"] = 1
cap_df["company_label"] = cap_df["company_id"].fillna("Unknown")

fig_tree = px.treemap(
    cap_df,
    path=["pattern_label", "broad_sector", "company_label"],
    values="count",
    color="pattern_label",
    hover_data={"company_name": True, "broad_sector": True},
    title="Capital Allocation Patterns — All 92 Companies",
    color_discrete_sequence=px.colors.qualitative.Set3,
    height=600,
)
fig_tree.update_traces(
    textinfo="label+value",
    hovertemplate="<b>%{label}</b><br>Company: %{customdata[0]}<br>Sector: %{customdata[1]}<extra></extra>"
)
fig_tree.update_layout(margin=dict(t=50, l=25, r=25, b=25))
st.plotly_chart(fig_tree, use_container_width=True)

st.markdown("---")

# ── Pattern Filter ─────────────────────────────────────────────────────────
st.subheader("Companies by Capital Allocation Pattern")

patterns = sorted(cap_df["pattern_label"].dropna().unique().tolist())
selected_pattern = st.selectbox("Select Pattern", ["All Patterns"] + patterns)

if selected_pattern != "All Patterns":
    filtered = cap_df[cap_df["pattern_label"] == selected_pattern].copy()
else:
    filtered = cap_df.copy()

st.markdown(f"**{len(filtered)} companies** in selected pattern")

# Pattern descriptions
pattern_desc = {
    "Reinvestor": "Earning cash, investing in growth, paying down debt",
    "Shareholder Returns": "High CFO/PAT ratio — returning value to shareholders",
    "Liquidating Assets": "Selling assets and repaying debt",
    "Distress Signal": "Burning cash, selling assets, borrowing — potential stress",
    "Growth Funded by Debt": "Investing aggressively, funded by borrowings",
    "Cash Accumulator": "Raising cash on all fronts",
    "Pre-Revenue": "Burning cash across all activities — early stage",
    "Mixed": "Mixed signals across cash flow activities",
    "Unknown": "Insufficient data to classify",
}

if selected_pattern != "All Patterns" and selected_pattern in pattern_desc:
    st.info(f"**{selected_pattern}:** {pattern_desc[selected_pattern]}")

# Display table
display_cols = {
    "company_id": "Ticker",
    "company_name": "Company",
    "broad_sector": "Sector",
    "pattern_label": "Pattern",
    "cfo_sign": "CFO",
    "cfi_sign": "CFI",
    "cff_sign": "CFF",
}

available = [c for c in display_cols if c in filtered.columns]
show_df = filtered[available].copy()
show_df = show_df.rename(columns=display_cols)
show_df = show_df.sort_values("Sector").reset_index(drop=True)
show_df.index += 1

st.dataframe(show_df, use_container_width=True)

st.markdown("---")

# ── Pattern Summary ────────────────────────────────────────────────────────
st.subheader("Pattern Distribution Summary")

summary = cap_df.groupby("pattern_label").size().reset_index(name="Count")
summary = summary.sort_values("Count", ascending=False).reset_index(drop=True)
summary.index += 1

col1, col2 = st.columns([1, 2])

with col1:
    st.dataframe(summary, use_container_width=True)

with col2:
    fig_bar = px.bar(
        summary,
        x="pattern_label",
        y="Count",
        color="pattern_label",
        title="Companies per Capital Allocation Pattern",
        height=350,
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    fig_bar.update_layout(showlegend=False, xaxis_tickangle=-30)
    st.plotly_chart(fig_bar, use_container_width=True)