"""
08_reports.py — Annual Reports Screen for Nifty100 Dashboard.
"""

import streamlit as st
import pandas as pd
import requests
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src.dashboard.utils.db import get_companies

st.set_page_config(page_title="Annual Reports", layout="wide")
st.title("Annual Reports")
st.markdown("---")

companies = get_companies()

# ── Company Search ─────────────────────────────────────────────────────────
search = st.text_input("Search by Ticker or Company Name", placeholder="e.g. RELIANCE")

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

co = companies[companies["ticker"] == selected_ticker].iloc[0]

st.markdown("---")

# ── Company Info ───────────────────────────────────────────────────────────
st.subheader(f"{co['company_name']} ({selected_ticker})")
st.markdown(f"**Sector:** {co.get('broad_sector', 'N/A')}")

col1, col2 = st.columns(2)
with col1:
    nse = co.get("nse_profile", "")
    if nse and str(nse) != "nan":
        st.markdown(f"[NSE Profile]({nse})")
    else:
        st.markdown("NSE Profile: N/A")

with col2:
    bse = co.get("bse_profile", "")
    if bse and str(bse) != "nan":
        st.markdown(f"[BSE Profile]({bse})")
    else:
        st.markdown("BSE Profile: N/A")

st.markdown("---")

# ── Annual Report Links ────────────────────────────────────────────────────
st.subheader("Annual Reports")

import sqlite3
conn = sqlite3.connect("db/nifty100.db")
try:
    docs_df = pd.read_sql_query(
        "SELECT * FROM documents WHERE company_id = ? ORDER BY year DESC",
        conn, params=[selected_ticker]
    )
except Exception:
    docs_df = pd.DataFrame()
conn.close()

if docs_df.empty:
    st.info(f"No annual report links found for {selected_ticker}.")
else:
    st.markdown(f"**{len(docs_df)} reports found**")

    for _, row in docs_df.iterrows():
        year = row.get("year", "N/A")
        url = row.get("annual_report_url", row.get("url", row.get("link", "")))
        doc_type = row.get("doc_type", row.get("type", "Annual Report"))

        col_year, col_link, col_status = st.columns([1, 3, 1])

        with col_year:
            st.markdown(f"**{year}**")

        with col_link:
            if url and str(url) != "nan":
                st.markdown(f"[{doc_type}]({url})")
            else:
                st.markdown("URL not available")

        with col_status:
            if url and str(url) != "nan":
                try:
                    resp = requests.head(str(url), timeout=3, allow_redirects=True)
                    if resp.status_code == 404:
                        st.markdown(
                            '<span style="color:red; font-weight:bold;">Report unavailable</span>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            '<span style="color:green;">Available</span>',
                            unsafe_allow_html=True
                        )
                except Exception:
                    st.markdown(
                        '<span style="color:orange;">Check manually</span>',
                        unsafe_allow_html=True
                    )
            else:
                st.markdown(
                    '<span style="color:gray;">No URL</span>',
                    unsafe_allow_html=True
                )

st.markdown("---")
st.caption("Annual report links sourced from BSE/NSE filings. Click to open PDF in browser.")