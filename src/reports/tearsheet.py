"""
tearsheet.py — Company Tearsheet PDF Generator for Nifty100.

Day 33-34: Generates 2-page PDF tearsheet for each company using ReportLab.
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


OUTPUT_DIR = Path("reports/tearsheets")
NAVY = colors.HexColor("#1F3B6B")
GREEN = colors.HexColor("#2E7D32")
RED = colors.HexColor("#C62828")
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
        fontSize=18,
        textColor=WHITE,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="SubHeader",
        fontSize=10,
        textColor=WHITE,
        fontName="Helvetica",
        alignment=TA_LEFT,
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
        name="ProText",
        fontSize=9,
        textColor=GREEN,
        fontName="Helvetica",
        spaceAfter=3,
        leftIndent=10,
    ))
    styles.add(ParagraphStyle(
        name="ConText",
        fontSize=9,
        textColor=RED,
        fontName="Helvetica",
        spaceAfter=3,
        leftIndent=10,
    ))
    styles.add(ParagraphStyle(
        name="NormalSmall",
        fontSize=8,
        fontName="Helvetica",
        spaceAfter=2,
    ))
    return styles


def build_kpi_table(kpis: list[tuple]) -> Table:
    """Build a 2-row x 3-col KPI tile table."""
    row1 = kpis[:3]
    row2 = kpis[3:6]

    def make_cell(label, value):
        return [
            Paragraph(f"<b>{value}</b>",
                      ParagraphStyle("KPIVal", fontSize=14,
                                     fontName="Helvetica-Bold",
                                     textColor=NAVY, alignment=TA_CENTER)),
            Paragraph(label,
                      ParagraphStyle("KPILbl", fontSize=8,
                                     fontName="Helvetica",
                                     textColor=colors.grey, alignment=TA_CENTER)),
        ]

    data = [
        [make_cell(l, v) for l, v in row1],
        [make_cell(l, v) for l, v in row2],
    ]

    t = Table(data, colWidths=[5.9*cm, 5.9*cm, 5.9*cm])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def build_revenue_table(pl_df: pd.DataFrame) -> Table:
    """Build revenue and net profit table for last 10 years."""
    recent = pl_df.sort_values("year").tail(10)
    if recent.empty:
        return Paragraph("No P&L data available", getSampleStyleSheet()["Normal"])

    headers = ["Year", "Revenue (Cr)", "Net Profit (Cr)", "OPM %"]
    data = [headers]
    for _, row in recent.iterrows():
        data.append([
            str(row.get("year", "N/A")),
            safe(row.get("sales")),
            safe(row.get("net_profit")),
            safe(row.get("opm_percentage", row.get("operating_profit", None))),
        ])

    t = Table(data, colWidths=[3*cm, 4*cm, 4*cm, 4*cm],
              repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("WORDWRAP", (0, 0), (-1, -1), True),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def build_ratio_table(ratios_df: pd.DataFrame) -> Table:
    """Build ROE and ROCE table."""
    recent = ratios_df.sort_values("year").tail(10)
    if recent.empty:
        return Paragraph("No ratio data available", getSampleStyleSheet()["Normal"])

    headers = ["Year", "ROE %", "ROCE %", "D/E", "NPM %", "FCF (Cr)"]
    data = [headers]
    for _, row in recent.iterrows():
        data.append([
            str(row.get("year", "N/A")),
            safe(row.get("return_on_equity_pct")),
            safe(row.get("return_on_capital_employed_pct")),
            safe(row.get("debt_to_equity")),
            safe(row.get("net_profit_margin_pct")),
            safe(row.get("free_cash_flow_cr")),
        ])

    t = Table(data, colWidths=[2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 3*cm],
              repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("WORDWRAP", (0, 0), (-1, -1), True),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def build_cashflow_table(cf_df: pd.DataFrame) -> Table:
    """Build cash flow table."""
    recent = cf_df.sort_values("year").tail(5)
    if recent.empty:
        return Paragraph("No cash flow data available", getSampleStyleSheet()["Normal"])

    headers = ["Year", "CFO (Cr)", "CFI (Cr)", "CFF (Cr)", "Net Cash (Cr)"]
    data = [headers]
    for _, row in recent.iterrows():
        data.append([
            str(row.get("year", "N/A")),
            safe(row.get("operating_activity")),
            safe(row.get("investing_activity")),
            safe(row.get("financing_activity")),
            safe(row.get("net_cash_flow")),
        ])

    t = Table(data, colWidths=[2.5*cm, 3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm],
              repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("WORDWRAP", (0, 0), (-1, -1), True),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def generate_tearsheet(company_id: str, conn: sqlite3.Connection,
                        pros_cons_df: pd.DataFrame = None) -> Path:
    """Generate a 2-page PDF tearsheet for one company."""
    styles = get_styles()

    # Load data
    co = pd.read_sql_query(
        "SELECT c.*, s.broad_sector, s.sub_sector FROM companies c "
        "LEFT JOIN sectors s ON s.company_id = c.id WHERE c.id = ?",
        conn, params=[company_id]
    )
    if co.empty:
        logger.warning(f"Company not found: {company_id}")
        return None

    co = co.iloc[0]
    company_name = co.get("company_name", company_id)
    sector = co.get("broad_sector", "N/A")
    sub_sector = co.get("sub_sector", "N/A")

    pl_df = pd.read_sql_query(
        "SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year",
        conn, params=[company_id]
    )
    ratios_df = pd.read_sql_query(
        "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year",
        conn, params=[company_id]
    )
    cf_df = pd.read_sql_query(
        "SELECT * FROM cashflow WHERE company_id = ? ORDER BY year",
        conn, params=[company_id]
    )

    if ratios_df.empty or len(ratios_df) < 3:
        logger.warning(f"Skipping {company_id} — insufficient data")
        return None

    latest = ratios_df.sort_values("year").iloc[-1]

    # Output path
    output_path = OUTPUT_DIR / f"{company_id}_tearsheet.pdf"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm,
    )

    story = []

    # ── PAGE 1 ─────────────────────────────────────────────────────────────

    # Navy header
    header_data = [[
        Paragraph(f"{company_name}", styles["NavyHeader"]),
        Paragraph(f"{company_id}", ParagraphStyle(
            "TickerRight", fontSize=16, textColor=WHITE,
            fontName="Helvetica-Bold", alignment=TA_RIGHT
        )),
    ]]
    header_table = Table(header_data, colWidths=[13*cm, 5*cm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(header_table)

    sub_data = [[
        Paragraph(f"Sector: {sector}  |  Sub-sector: {sub_sector}  |  NSE: {company_id}",
                  styles["SubHeader"])
    ]]
    sub_table = Table(sub_data, colWidths=[18*cm])
    sub_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#2C4F8A")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(sub_table)
    story.append(Spacer(1, 0.4*cm))

    # 6 KPI tiles
    story.append(Paragraph("Key Metrics (Latest Year)", styles["SectionTitle"]))
    kpis = [
        ("ROE %", safe(latest.get("return_on_equity_pct"), suffix="%")),
        ("ROCE %", safe(latest.get("return_on_capital_employed_pct"), suffix="%")),
        ("Net Profit Margin", safe(latest.get("net_profit_margin_pct"), suffix="%")),
        ("Debt / Equity", safe(latest.get("debt_to_equity"))),
        ("Revenue CAGR 5yr", safe(latest.get("revenue_cagr_5yr"), suffix="%")),
        ("FCF (Cr)", safe(latest.get("free_cash_flow_cr"))),
    ]
    story.append(build_kpi_table(kpis))
    story.append(Spacer(1, 0.4*cm))

    # Revenue and Net Profit table
    story.append(Paragraph("Revenue and Net Profit (10 Years)", styles["SectionTitle"]))
    story.append(build_revenue_table(pl_df))
    story.append(Spacer(1, 0.4*cm))

    # ROE ROCE table
    story.append(Paragraph("Return Ratios (10 Years)", styles["SectionTitle"]))
    story.append(build_ratio_table(ratios_df))

    story.append(PageBreak())

    # ── PAGE 2 ─────────────────────────────────────────────────────────────

    # Header on page 2
    story.append(header_table)
    story.append(Spacer(1, 0.4*cm))

    # Cash Flow table
    story.append(Paragraph("Cash Flow Summary (5 Years)", styles["SectionTitle"]))
    story.append(build_cashflow_table(cf_df))
    story.append(Spacer(1, 0.4*cm))

    # Pros and Cons
    if pros_cons_df is not None and not pros_cons_df.empty:
        co_pc = pros_cons_df[pros_cons_df["company_id"] == company_id]
        pros = co_pc[co_pc["type"] == "pro"]["text"].tolist()
        cons = co_pc[co_pc["type"] == "con"]["text"].tolist()
    else:
        pros = []
        cons = []

    pc_col1 = []
    pc_col2 = []

    pc_col1.append(Paragraph("Strengths", styles["SectionTitle"]))
    if pros:
        for p in pros[:6]:
            pc_col1.append(Paragraph(f"+ {p}", styles["ProText"]))
    else:
        pc_col1.append(Paragraph("No specific strengths identified", styles["NormalSmall"]))

    pc_col2.append(Paragraph("Concerns", styles["SectionTitle"]))
    if cons:
        for c in cons[:6]:
            pc_col2.append(Paragraph(f"- {c}", styles["ConText"]))
    else:
        pc_col2.append(Paragraph("No specific concerns identified", styles["NormalSmall"]))

    pc_table = Table([[pc_col1, pc_col2]], colWidths=[9*cm, 9*cm])
    pc_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(pc_table)
    story.append(Spacer(1, 0.4*cm))

    # Capital allocation badge
    try:
        cap_alloc = pd.read_csv("output/capital_allocation.csv")
        co_cap = cap_alloc[cap_alloc["company_id"] == company_id]
        if not co_cap.empty:
            pattern = co_cap.sort_values("year").iloc[-1].get("pattern_label", "Unknown")
        else:
            pattern = "Unknown"
    except Exception:
        pattern = "Unknown"

    story.append(Paragraph("Capital Allocation Pattern", styles["SectionTitle"]))
    badge_data = [[Paragraph(f"{pattern}", ParagraphStyle(
        "Badge", fontSize=12, fontName="Helvetica-Bold",
        textColor=WHITE, alignment=TA_CENTER
    ))]]
    badge_table = Table(badge_data, colWidths=[8*cm])
    badge_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(badge_table)

    # Footer
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph(
        "N100 Financial Intelligence Platform  |  Data sourced from public filings  |  For internal use only",
        ParagraphStyle("Footer", fontSize=7, textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(story)
    return output_path


class TearsheetBatchRunner:

    def __init__(self):
        cfg.ensure_dirs()
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def run(self, tickers: list = None):
        logger.info("=" * 60)
        logger.info("Tearsheet Batch Runner - Starting Day 34")
        logger.info("=" * 60)

        conn = sqlite3.connect(cfg.DB_PATH)

        if tickers is None:
            companies = pd.read_sql_query(
                "SELECT id as company_id FROM companies", conn
            )
            tickers = companies["company_id"].tolist()

        # Load pros cons
        try:
            pros_cons_df = pd.read_csv("output/pros_cons_generated.csv")
        except Exception:
            pros_cons_df = pd.DataFrame()

        generated = []
        skipped = []

        for ticker in tickers:
            try:
                path = generate_tearsheet(ticker, conn, pros_cons_df)
                if path:
                    generated.append(ticker)
                    logger.info(f"  Generated: {ticker}_tearsheet.pdf")
                else:
                    skipped.append(ticker)
            except Exception as e:
                logger.error(f"  Failed [{ticker}]: {e}")
                skipped.append(ticker)

        conn.close()

        # Save skipped
        if skipped:
            pd.DataFrame({"ticker": skipped}).to_csv(
                "output/skipped_tearsheets.csv", index=False
            )
            logger.warning(f"Skipped {len(skipped)} companies -> output/skipped_tearsheets.csv")

        logger.success(f"Tearsheets complete: {len(generated)} generated, {len(skipped)} skipped")
        return generated, skipped


if __name__ == "__main__":
    runner = TearsheetBatchRunner()
    runner.run()