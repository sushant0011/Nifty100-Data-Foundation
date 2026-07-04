"""
radar.py — Radar Chart Generator for Nifty100 Peer Comparison.

Day 19: Generate radar/polar charts for each company showing
        8 metrics vs peer group average.
"""

import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

from src.utils.config import cfg
from src.utils.logger import logger


RADAR_METRICS = [
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "pat_cagr_5yr",
    "revenue_cagr_5yr",
    "composite_quality_score",
]

RADAR_LABELS = [
    "ROE",
    "ROCE",
    "NPM",
    "D/E",
    "FCF",
    "PAT CAGR 5yr",
    "Rev CAGR 5yr",
    "Quality Score",
]

RADAR_OUTPUT_DIR = Path("reports/radar_charts")


def load_peer_percentiles(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query("SELECT * FROM peer_percentiles", conn)


def load_latest_ratios(conn: sqlite3.Connection) -> pd.DataFrame:
    query = """
        SELECT fr.*, c.company_name, s.broad_sector
        FROM financial_ratios fr
        LEFT JOIN companies c ON c.id = fr.company_id
        LEFT JOIN sectors s ON s.company_id = fr.company_id
        INNER JOIN (
            SELECT company_id, MAX(year) as max_year
            FROM financial_ratios
            GROUP BY company_id
        ) latest ON fr.company_id = latest.company_id AND fr.year = latest.max_year
    """
    return pd.read_sql_query(query, conn)


def normalise_for_radar(df: pd.DataFrame, metrics: list) -> pd.DataFrame:
    """Scale each metric to 0-100 using P10/P90 winsorisation."""
    result = df.copy()
    for col in metrics:
        if col not in df.columns:
            result[col + "_scaled"] = 50.0
            continue
        series = df[col].copy()
        low = np.nanpercentile(series.dropna(), 10)
        high = np.nanpercentile(series.dropna(), 90)
        series = series.clip(lower=low, upper=high)
        mn, mx = series.min(), series.max()
        if mx == mn:
            result[col + "_scaled"] = 50.0
        else:
            result[col + "_scaled"] = (series - mn) / (mx - mn) * 100
    return result


def draw_radar(company_id: str,
               company_name: str,
               company_values: list,
               peer_avg_values: list,
               labels: list,
               output_path: Path) -> None:
    """Draw and save a radar chart for one company."""
    N = len(labels)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]  # close the polygon

    company_values = company_values + company_values[:1]
    peer_avg_values = peer_avg_values + peer_avg_values[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    # Company polygon
    ax.plot(angles, company_values, "o-", linewidth=2, color="#1f77b4", label=company_id)
    ax.fill(angles, company_values, alpha=0.25, color="#1f77b4")

    # Peer average dashed outline
    ax.plot(angles, peer_avg_values, "--", linewidth=1.5, color="#ff7f0e", label="Peer Avg")
    ax.fill(angles, peer_avg_values, alpha=0.08, color="#ff7f0e")

    # Labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=8)

    ax.set_title(f"{company_name}\n({company_id})", size=14, fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=10)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def draw_standalone_radar(company_id: str,
                           company_name: str,
                           company_values: list,
                           nifty100_avg: list,
                           labels: list,
                           output_path: Path) -> None:
    """Draw radar chart for companies with no peer group vs Nifty100 average."""
    draw_radar(
        company_id=company_id,
        company_name=f"{company_name} (No Peer Group)",
        company_values=company_values,
        peer_avg_values=nifty100_avg,
        labels=labels,
        output_path=output_path,
    )


class RadarChartEngine:

    def __init__(self):
        self.conn = sqlite3.connect(cfg.DB_PATH)
        RADAR_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def run(self):
        logger.info("=" * 60)
        logger.info("Radar Chart Engine - Starting")
        logger.info("=" * 60)

        ratios = load_latest_ratios(self.conn)
        peer_percentiles = load_peer_percentiles(self.conn)

        # Normalise metrics
        ratios_scaled = normalise_for_radar(ratios, RADAR_METRICS)

        scaled_cols = [m + "_scaled" for m in RADAR_METRICS]

        # Nifty100 average (for standalone charts)
        nifty100_avg = [
            ratios_scaled[c].mean() if c in ratios_scaled.columns else 50.0
            for c in scaled_cols
        ]

        # Get peer group assignments
        peer_groups_list = {}
        if not peer_percentiles.empty:
            for company_id, grp_df in peer_percentiles.groupby("company_id"):
                peer_groups_list[company_id] = grp_df["peer_group_name"].iloc[0]

        generated = 0
        for _, row in ratios_scaled.iterrows():
            company_id = row["company_id"]
            company_name = row.get("company_name", company_id) or company_id

            company_values = [
                float(row[c]) if c in row and pd.notna(row[c]) else 50.0
                for c in scaled_cols
            ]

            output_path = RADAR_OUTPUT_DIR / f"{company_id}_radar.png"

            if company_id in peer_groups_list:
                # Get peer group average
                peer_group = peer_groups_list[company_id]
                peer_companies = [
                    cid for cid, grp in peer_groups_list.items()
                    if grp == peer_group
                ]
                peer_df = ratios_scaled[ratios_scaled["company_id"].isin(peer_companies)]
                peer_avg = [
                    float(peer_df[c].mean()) if c in peer_df.columns else 50.0
                    for c in scaled_cols
                ]

                draw_radar(
                    company_id=company_id,
                    company_name=company_name,
                    company_values=company_values,
                    peer_avg_values=peer_avg,
                    labels=RADAR_LABELS,
                    output_path=output_path,
                )
            else:
                draw_standalone_radar(
                    company_id=company_id,
                    company_name=company_name,
                    company_values=company_values,
                    nifty100_avg=nifty100_avg,
                    labels=RADAR_LABELS,
                    output_path=output_path,
                )

            generated += 1
            logger.info(f"  Chart: {company_id}_radar.png")

        self.conn.close()
        logger.success(f"Radar charts complete: {generated} charts -> {RADAR_OUTPUT_DIR}")


if __name__ == "__main__":
    RadarChartEngine().run()