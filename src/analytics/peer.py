"""
peer.py — Peer Percentile Ranking Engine for Nifty100.

Day 18: Compute PERCENT_RANK for 10 metrics within each of 11 peer groups.
        Populate peer_percentiles table in SQLite.
"""

import sqlite3
import pandas as pd
from pathlib import Path

from src.utils.config import cfg
from src.utils.logger import logger


PEER_METRICS = [
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "net_profit_margin_pct",
    "debt_to_equity",           # inverse — lower is better
    "free_cash_flow_cr",
    "pat_cagr_5yr",
    "revenue_cagr_5yr",
    "eps_cagr_5yr",
    "interest_coverage",
    "asset_turnover",
]

INVERSE_METRICS = {"debt_to_equity"}  # lower = better, so invert rank

CREATE_PEER_TABLE = """
CREATE TABLE IF NOT EXISTS peer_percentiles (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id          TEXT NOT NULL,
    peer_group_name     TEXT NOT NULL,
    metric              TEXT NOT NULL,
    value               REAL,
    percentile_rank     REAL,
    year                INTEGER NOT NULL,
    UNIQUE(company_id, peer_group_name, metric, year)
)
"""


def load_peer_groups(conn: sqlite3.Connection) -> pd.DataFrame:
    """Load peer_groups table from SQLite."""
    try:
        df = pd.read_sql_query("SELECT * FROM peer_groups", conn)
        logger.info(f"Loaded peer_groups: {len(df)} rows, {df['peer_group_name'].nunique() if 'peer_group_name' in df.columns else '?'} groups")
        return df
    except Exception as e:
        logger.error(f"Failed to load peer_groups: {e}")
        return pd.DataFrame()


def load_latest_ratios(conn: sqlite3.Connection) -> pd.DataFrame:
    """Load latest year financial_ratios per company."""
    query = """
        SELECT fr.*
        FROM financial_ratios fr
        INNER JOIN (
            SELECT company_id, MAX(year) as max_year
            FROM financial_ratios
            GROUP BY company_id
        ) latest ON fr.company_id = latest.company_id AND fr.year = latest.max_year
    """
    return pd.read_sql_query(query, conn)


def percent_rank(series: pd.Series) -> pd.Series:
    """
    Compute PERCENT_RANK (0.0 to 1.0) for a series.
    Ties get the average rank.
    NaN values get NaN rank.
    """
    return series.rank(pct=True, na_option="keep")


def compute_peer_percentiles(peer_groups: pd.DataFrame,
                              ratios: pd.DataFrame) -> list[dict]:
    """
    Compute percentile ranks for all companies within their peer groups.

    Returns list of row dicts ready for DB insert.
    """
    rows = []

    # Detect column names in peer_groups
    company_col = None
    for c in ["company_id", "ticker", "id"]:
        if c in peer_groups.columns:
            company_col = c
            break

    group_col = None
    for c in ["peer_group_name", "peer_group", "group_name"]:
        if c in peer_groups.columns:
            group_col = c
            break

    if company_col is None or group_col is None:
        logger.error(f"Cannot find company/group columns in peer_groups. Columns: {peer_groups.columns.tolist()}")
        return rows

    # Rename for consistency
    peer_groups = peer_groups.rename(columns={
        company_col: "company_id",
        group_col: "peer_group_name"
    })

    for group_name, group_df in peer_groups.groupby("peer_group_name"):
        group_companies = group_df["company_id"].tolist()

        # Get ratios for companies in this group
        group_ratios = ratios[ratios["company_id"].isin(group_companies)].copy()

        if group_ratios.empty:
            logger.warning(f"No ratio data for peer group: {group_name}")
            continue

        logger.info(f"Peer group [{group_name}]: {len(group_ratios)} companies")

        for metric in PEER_METRICS:
            if metric not in group_ratios.columns:
                logger.warning(f"  Metric not found: {metric}")
                continue

            series = group_ratios[metric].copy()
            ranks = percent_rank(series)

            # Invert rank for metrics where lower is better
            if metric in INVERSE_METRICS:
                ranks = 1 - ranks

            for _, row in group_ratios.iterrows():
                company_id = row["company_id"]
                value = row.get(metric)
                rank = ranks.loc[row.name]

                rows.append({
                    "company_id": company_id,
                    "peer_group_name": group_name,
                    "metric": metric,
                    "value": float(value) if pd.notna(value) else None,
                    "percentile_rank": float(rank) if pd.notna(rank) else None,
                    "year": int(row["year"]),
                })

    return rows


def get_no_peer_companies(peer_groups: pd.DataFrame,
                           ratios: pd.DataFrame,
                           company_col: str = "company_id") -> list[str]:
    """Return list of companies not assigned to any peer group."""
    all_companies = set(ratios["company_id"].unique())
    peer_companies = set(peer_groups[company_col].unique()) if company_col in peer_groups.columns else set()
    return list(all_companies - peer_companies)


class PeerEngine:

    def __init__(self):
        cfg.ensure_dirs()
        self.conn = sqlite3.connect(cfg.DB_PATH)
        self.conn.row_factory = sqlite3.Row

    def run(self):
        logger.info("=" * 60)
        logger.info("Peer Engine - Starting Sprint 3")
        logger.info("=" * 60)

        # Create table
        self.conn.execute(CREATE_PEER_TABLE)
        self.conn.commit()

        # Load data
        peer_groups = load_peer_groups(self.conn)
        ratios = load_latest_ratios(self.conn)

        if peer_groups.empty:
            logger.warning("No peer groups found — skipping peer ranking")
            return

        logger.info(f"Loaded {len(ratios)} company-ratio rows")

        # Compute percentiles
        rows = compute_peer_percentiles(peer_groups, ratios)

        if rows:
            self.conn.executemany("""
                INSERT OR REPLACE INTO peer_percentiles
                (company_id, peer_group_name, metric, value, percentile_rank, year)
                VALUES (:company_id, :peer_group_name, :metric, :value, :percentile_rank, :year)
            """, rows)
            self.conn.commit()
            logger.success(f"Inserted {len(rows)} peer percentile rows")
        else:
            logger.warning("No peer percentile rows computed")

        # Log no-peer companies
        company_col = "company_id" if "company_id" in peer_groups.columns else "ticker"
        no_peer = get_no_peer_companies(peer_groups, ratios, company_col)
        if no_peer:
            logger.info(f"Companies with no peer group ({len(no_peer)}): {no_peer[:10]}...")
        else:
            logger.info("All companies have peer group assignments")

        count = self.conn.execute("SELECT COUNT(*) FROM peer_percentiles").fetchone()[0]
        logger.info(f"peer_percentiles table: {count} rows")

        self.conn.close()
        logger.success("Peer Engine complete!")


if __name__ == "__main__":
    PeerEngine().run()