"""
sector_report.py — Sector PDF Report Generator for Nifty100.

Day 34: Generates 11 sector PDFs with median KPIs and company listings.
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from src.utils.config import cfg
from src.utils.logger import logger


SECTOR_OUTPUT_DIR = Path("reports/sector")
NAVY = colors.HexColor("#1F3B6B")
GREEN = colors.HexColor("#2E7D32")
LIGHT_GRAY = colors.HexColor("#F5F5F5")
WHITE = colors.white


def safe(val, decimals=2, suffix=""):
    try:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return "N/A"
        return f"{round(float(val), decimals)}{suffix}"
    except Exception:
        return "N/A"


def get_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="NavyHeader",
        fontSize=20,
        textColor=WHITE,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="SectionTitle",
        fontSize=12,
        textColor=NAVY,
        fontName="Helvetica-Bold",
        spaceBefore=12,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="NormalSmall",
        fontSize=8,
        fontName="Helvetica",
        spaceAfter=2,
    ))
    return styles


def build_median_kpi_table(sector_df: pd.DataFrame) -> Table:
    """Build sector median KPI summary table."""
    metrics = {
        "ROE %": "return_on_equity_pct",
        "ROCE %": "return_on_capital_employed_pct",
        "NPM %": "net_profit_margin_pct",
        "D/E": "debt_to_equity",
        "Rev CAGR 5yr %": "revenue_cagr_5yr",
        "PAT CAGR 5yr %": "pat_cagr_5yr",
        "FCF (Cr)": "free_cash_flow_cr",
        "Quality Score": "composite_quality_score",
    }

    headers = ["Metric", "Median", "Min", "Max"]
    data = [headers]

    for label, col in metrics.items():
        if col in sector_df.columns:
            series = sector_df[col].dropna()
            if not series.empty:
                data.append([
                    label,
                    safe(series.median()),
                    safe(series.min()),
                    safe(series.max()),
                ])

    t = Table(data, colWidths=[5*cm, 4*cm, 4*cm, 4*cm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("WORDWRAP", (0, 0), (-1, -1), True),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (0, -1), 8),
    ]))
    return t


def build_company_table(sector_df: pd.DataFrame,
                         companies_df: pd.DataFrame) -> Table:
    """Build company listing table for a sector."""
    merged = sector_df.merge(
        companies_df[["ticker", "company_name"]],
        left_on="company_id", right_on="ticker", how="left"
    )
    merged = merged.sort_values("composite_quality_score",
                                ascending=False).reset_index(drop=True)

    headers = ["#", "Ticker", "Company", "ROE %", "D/E",
               "Rev CAGR %", "PAT CAGR %", "FCF (Cr)", "Score"]
    data = [headers]

    for i, row in merged.iterrows():
        data.append([
            str(i + 1),
            str(row.get("company_id", "N/A")),
            str(row.get("company_name", "N/A"))[:25],
            safe(row.get("return_on_equity_pct")),
            safe(row.get("debt_to_equity")),
            safe(row.get("revenue_cagr_5yr")),
            safe(row.get("pat_cagr_5yr")),
            safe(row.get("free_cash_flow_cr")),
            safe(row.get("composite_quality_score")),
        ])

    col_widths = [1*cm, 2.5*cm, 5*cm, 2*cm, 1.5*cm, 2*cm, 2*cm, 2*cm, 1.5*cm]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 2), (2, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("WORDWRAP", (0, 0), (-1, -1), True),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def generate_sector_report(sector_name: str,
                             sector_df: pd.DataFrame,
                             companies_df: pd.DataFrame) -> Path:
    """Generate a PDF report for one sector."""
    styles = get_styles()
    safe_name = sector_name.replace("/", "-").replace(" ", "_")
    output_path = SECTOR_OUTPUT_DIR / f"{safe_name}_report.pdf"
    SECTOR_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm,
    )

    story = []

    # Header
    header_data = [[
        Paragraph(f"{sector_name} Sector Report",
                  styles["NavyHeader"])
    ]]
    header_table = Table(header_data, colWidths=[18*cm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.5*cm))

    # Summary stats
    n_companies = len(sector_df)
    story.append(Paragraph(
        f"Companies in sector: {n_companies}  |  "
        f"Median Quality Score: {safe(sector_df['composite_quality_score'].median())}  |  "
        f"Median ROE: {safe(sector_df['return_on_equity_pct'].median())}%",
        ParagraphStyle("Summary", fontSize=10, fontName="Helvetica",
                       spaceAfter=8, textColor=NAVY)
    ))

    story.append(Paragraph("Sector Median KPIs", styles["SectionTitle"]))
    story.append(build_median_kpi_table(sector_df))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("Company Rankings", styles["SectionTitle"]))
    story.append(build_company_table(sector_df, companies_df))

    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph(
        "N100 Financial Intelligence Platform  |  For internal use only",
        ParagraphStyle("Footer", fontSize=7, textColor=colors.grey,
                       alignment=TA_CENTER)
    ))

    doc.build(story)
    return output_path


class SectorReportBatchRunner:

    def __init__(self):
        cfg.ensure_dirs()
        SECTOR_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def run(self):
        logger.info("=" * 60)
        logger.info("Sector Report Batch Runner - Starting")
        logger.info("=" * 60)

        conn = sqlite3.connect(cfg.DB_PATH)

        companies = pd.read_sql_query("""
            SELECT c.id as ticker, c.company_name, s.broad_sector
            FROM companies c
            LEFT JOIN sectors s ON s.company_id = c.id
        """, conn)

        ratios = pd.read_sql_query("""
            SELECT fr.*
            FROM financial_ratios fr
            INNER JOIN (
                SELECT company_id, MAX(year) as max_year
                FROM financial_ratios GROUP BY company_id
            ) latest ON fr.company_id = latest.company_id
            AND fr.year = latest.max_year
        """, conn)

        conn.close()

        # Merge
        df = ratios.merge(
            companies[["ticker", "company_name", "broad_sector"]],
            left_on="company_id", right_on="ticker", how="left"
        )

        sectors = df["broad_sector"].dropna().unique()
        generated = []

        for sector in sorted(sectors):
            sector_df = df[df["broad_sector"] == sector].copy()
            if sector_df.empty:
                continue
            try:
                path = generate_sector_report(sector, sector_df, companies)
                generated.append(sector)
                logger.info(f"  Generated: {sector}_report.pdf")
            except Exception as e:
                logger.error(f"  Failed [{sector}]: {e}")

        logger.success(f"Sector reports complete: {len(generated)}/{len(sectors)} generated")
        return generated


if __name__ == "__main__":
    SectorReportBatchRunner().run()