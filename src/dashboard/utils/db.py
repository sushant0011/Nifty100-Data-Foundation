"""
db.py — Shared cached data loader for Nifty100 Streamlit Dashboard.

All functions use @st.cache_data(ttl=600) for 10-minute caching.
"""

import sqlite3
import pandas as pd
import streamlit as st
from pathlib import Path

DB_PATH = Path("db/nifty100.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    """Load all 92 companies with sector info."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT c.id as ticker, c.company_name, c.about_company,
               c.website, c.nse_profile, c.bse_profile,
               s.broad_sector, s.sub_sector
        FROM companies c
        LEFT JOIN sectors s ON s.company_id = c.id
    """, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_ratios(ticker: str = None, year: int = None) -> pd.DataFrame:
    """Load financial ratios, optionally filtered by ticker and year."""
    conn = get_connection()
    query = "SELECT * FROM financial_ratios WHERE 1=1"
    params = []
    if ticker:
        query += " AND company_id = ?"
        params.append(ticker)
    if year:
        query += " AND year = ?"
        params.append(year)
    query += " ORDER BY year"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_latest_ratios(year: int = None) -> pd.DataFrame:
    """Load latest year ratios for all companies."""
    conn = get_connection()
    if year:
        query = f"SELECT * FROM financial_ratios WHERE year = {year}"
    else:
        query = """
            SELECT fr.*
            FROM financial_ratios fr
            INNER JOIN (
                SELECT company_id, MAX(year) as max_year
                FROM financial_ratios GROUP BY company_id
            ) latest ON fr.company_id = latest.company_id
            AND fr.year = latest.max_year
        """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pl(ticker: str) -> pd.DataFrame:
    """Load P&L data for a ticker."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year",
        conn, params=[ticker]
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_bs(ticker: str) -> pd.DataFrame:
    """Load Balance Sheet data for a ticker."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year",
        conn, params=[ticker]
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_cf(ticker: str) -> pd.DataFrame:
    """Load Cash Flow data for a ticker."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM cashflow WHERE company_id = ? ORDER BY year",
        conn, params=[ticker]
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    """Load sector summary with company counts."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT broad_sector, COUNT(*) as company_count
        FROM sectors
        GROUP BY broad_sector
        ORDER BY company_count DESC
    """, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peers(group_name: str) -> pd.DataFrame:
    """Load peer group companies with their ratios."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT pg.company_id, pg.peer_group_name,
               c.company_name, s.broad_sector,
               fr.return_on_equity_pct, fr.return_on_capital_employed_pct,
               fr.net_profit_margin_pct, fr.debt_to_equity,
               fr.free_cash_flow_cr, fr.pat_cagr_5yr,
               fr.revenue_cagr_5yr, fr.composite_quality_score
        FROM peer_groups pg
        LEFT JOIN companies c ON c.id = pg.company_id
        LEFT JOIN sectors s ON s.company_id = pg.company_id
        LEFT JOIN financial_ratios fr ON fr.company_id = pg.company_id
        WHERE pg.peer_group_name = ?
        AND fr.year = (
            SELECT MAX(year) FROM financial_ratios
            WHERE company_id = pg.company_id
        )
    """, conn, params=[group_name])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peer_groups() -> list:
    """Get list of all peer group names."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT DISTINCT peer_group_name FROM peer_groups ORDER BY peer_group_name",
        conn
    )
    conn.close()
    return df["peer_group_name"].tolist()


@st.cache_data(ttl=600)
def get_peer_percentiles(group_name: str) -> pd.DataFrame:
    """Load peer percentile rankings for a group."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT * FROM peer_percentiles
        WHERE peer_group_name = ?
    """, conn, params=[group_name])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pros_cons(ticker: str) -> pd.DataFrame:
    """Load pros and cons for a company."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM prosandcons WHERE company_id = ?",
        conn, params=[ticker]
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_capital_allocation() -> pd.DataFrame:
    """Load capital allocation patterns for all companies."""
    try:
        df = pd.read_csv("output/capital_allocation.csv")
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=600)
def get_valuation() -> pd.DataFrame:
    """Load valuation summary if available."""
    try:
        df = pd.read_excel("output/valuation_summary.xlsx")
        return df
    except Exception:
        return pd.DataFrame()


def safe_val(val, decimals: int = 2, suffix: str = "") -> str:
    """Format a value safely — return N/A if None or NaN."""
    try:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return "N/A"
        return f"{round(float(val), decimals)}{suffix}"
    except Exception:
        return "N/A"