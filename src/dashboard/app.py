"""
app.py — Main Streamlit entry point for Nifty100 Dashboard.

Run: streamlit run src/dashboard/app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="N",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.title("Nifty 100 Analytics")
st.sidebar.markdown("---")
st.sidebar.caption("N100 Financial Intelligence Platform v1.0")

st.title("Nifty 100 Financial Intelligence Platform")
st.markdown("> Production-grade analytics for all 92 Nifty 100 companies")
st.markdown("---")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Companies", "92")
col2.metric("Financial KPIs", "30+")
col3.metric("Screener Filters", "15")
col4.metric("Peer Groups", "11")
col5.metric("Radar Charts", "92")

st.markdown("---")
st.markdown("""
### Use the sidebar to navigate between screens.

| Screen | Description |
|--------|-------------|
| Home | Market overview, KPI tiles, sector breakdown |
| Company Profile | Deep-dive into any of the 92 companies |
| Screener | Filter companies by 15 metrics with 6 presets |
| Peer Comparison | Radar charts and percentile rankings by peer group |
| Trend Analysis | 10-year metric trends with YoY annotations |
| Sector Analysis | Bubble charts, sector median KPIs |
| Capital Allocation | Treemap of 92 companies by capital pattern |
| Annual Reports | BSE annual report links for all companies |
""")