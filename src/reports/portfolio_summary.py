"""
portfolio_summary.py — Portfolio Summary PDF Generator for Nifty100.

Day 35: Generates one-page-per-company portfolio summary PDF
        with trend arrows for each KPI.
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


OUTPUT_DIR = Path("reports/portfolio")
NAVY = colors.HexColor("#1F3B6B")
GREEN = colors.HexColor("#2E7D32")
RED = colors.HexColor("#C62828")
LIGHT_GRAY = colors.HexColor("#F5F5F5")
WHITE = colors.white

UP_ARROW = "▲"
DOWN_ARROW = "▼"
FLAT_ARROW = "►"


def safe(val, decimals=2, suffix=""):
    try:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return "N/A"
        return f"{round(float(val), decimals)}{suffix}"
    except Exception:
        return "N/A"


def trend_arrow(current, previous, threshold=2.0) -> str:
    """Return trend arrow based on YoY change."""
    try:
        if pd.isna(current) or pd.isna(previous) or previous == 0:
            return FLAT_ARROW
        pct_change = ((current - previous) / abs(previous)) * 100
        if pct_change > threshold:
            return UP_ARROW
        elif pct_change < -threshold:
            return DOWN_ARROW
        else:
            return FLAT_ARROW
    except Exception:
        return FLAT_ARROW


def get_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="NavyHeader",
        fontSize=14,
        textColor=WHITE,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="SectionTitle",
        fontSize=10,
        textColor=NAVY,
        fontName="Helvetica-Bold",
        spaceBefore=8,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="NormalSmall",
        fontSize=8,
        fontName="Helvetica",
        spaceAfter=2,
    ))
    return styles


def build_kpi_tile_table(kpi_data: list) -> Table:
    """Build KPI table with trend arrows — 2 rows x 3 cols."""
    row1 = kpi_data[:3]
    row2 = kpi_data[3:6]

    def make_cell(label, value, arrow):
        arrow_color = GREEN if arrow == UP_ARROW else (
            RED if arrow == DOWN_ARROW else colors.grey
        )
        return [
            Paragraph(
                f'<b>{value}</b> <font color="{"#2E7D32" if arrow == UP_ARROW else ("#C62828" if arrow == DOWN_ARROW else "#9E9E9E")}">{arrow}</font>',
                ParagraphStyle("KPIVal", fontSize=12, fontName="Helvetica-Bold",
                               textColor=NAVY, alignment=TA_CENTER)
            ),
            Paragraph(label, ParagraphStyle("KPILbl", fontSize=7,
                                            fontName="Helvetica",
                                            textColor=colors.grey,
                                            alignment=TA_CENTER)),
        ]

    data = [
        [make_cell(l, v, a) for l, v, a in row1],
        [make_cell(l, v, a) for l, v, a in row2],
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


def generate_portfolio_summary(conn: sqlite3.Connection) -> Path:
    """Generate portfolio summary PDF — one page per company."""
    styles = get_styles()

    companies = pd.read_sql_query("""
        SELECT c.id as company_id, c.company_name, s.broad_sector
        FROM companies c
        LEFT JOIN sectors s ON s.company_id = c.id
        ORDER BY c.id
    """, conn)

    ratios = pd.read_sql_query(
        "SELECT * FROM financial_ratios ORDER BY company_id, year",
        conn
    )

    output_path = OUTPUT_DIR / "portfolio_summary.pdf"
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
    first_page = True

    for _, co in companies.iterrows():
        company_id = co["company_id"]
        company_name = co.get("company_name", company_id)
        sector = co.get("broad_sector", "N/A")

        co_ratios = ratios[ratios["company_id"] == company_id].sort_values("year")

        if co_ratios.empty:
            continue

        if not first_page:
            story.append(PageBreak())
        first_page = False

        latest = co_ratios.iloc[-1]
        prev = co_ratios.iloc[-2] if len(co_ratios) >= 2 else latest

        # Header
        header_data = [[
            Paragraph(f"{company_name}", styles["NavyHeader"]),
            Paragraph(f"{company_id}  |  {sector}",
                      ParagraphStyle("TickerRight", fontSize=10,
                                     textColor=WHITE, fontName="Helvetica",
                                     alignment=TA_RIGHT)),
        ]]
        header_table = Table(header_data, colWidths=[12*cm, 6*cm])
        header_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), NAVY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (0, -1), 10),
            ("RIGHTPADDING", (-1, 0), (-1, -1), 10),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.3*cm))

        # 6 KPI tiles with trend arrows
        kpi_metrics = [
            ("ROE %", "return_on_equity_pct", "%"),
            ("ROCE %", "return_on_capital_employed_pct", "%"),
            ("Net Profit Margin", "net_profit_margin_pct", "%"),
            ("Debt / Equity", "debt_to_equity", ""),
            ("Revenue CAGR 5yr", "revenue_cagr_5yr", "%"),
            ("FCF (Cr)", "free_cash_flow_cr", ""),
        ]

        kpi_data = []
        for label, col, suffix in kpi_metrics:
            curr_val = latest.get(col)
            prev_val = prev.get(col)
            arrow = trend_arrow(curr_val, prev_val)
            kpi_data.append((label, safe(curr_val, suffix=suffix), arrow))

        story.append(Paragraph("Key Performance Indicators", styles["SectionTitle"]))
        story.append(build_kpi_tile_table(kpi_data))
        story.append(Spacer(1, 0.3*cm))

        # Historical ratios table
        story.append(Paragraph("Historical Ratios", styles["SectionTitle"]))
        recent = co_ratios.tail(8)
        hist_headers = ["Year", "ROE %", "ROCE %", "D/E", "NPM %",
                        "Rev CAGR 5yr %", "FCF (Cr)", "Quality"]
        hist_data = [hist_headers]
        for _, row in recent.iterrows():
            hist_data.append([
                str(row.get("year", "N/A")),
                safe(row.get("return_on_equity_pct")),
                safe(row.get("return_on_capital_employed_pct")),
                safe(row.get("debt_to_equity")),
                safe(row.get("net_profit_margin_pct")),
                safe(row.get("revenue_cagr_5yr")),
                safe(row.get("free_cash_flow_cr")),
                safe(row.get("composite_quality_score")),
            ])

        hist_table = Table(
            hist_data,
            colWidths=[2*cm, 2.2*cm, 2.2*cm, 1.8*cm, 2*cm, 2.8*cm, 2.2*cm, 2*cm],
            repeatRows=1
        )
        hist_table.setStyle(TableStyle([
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
        story.append(hist_table)

        # Footer
        story.append(Spacer(1, 0.3*cm))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=colors.lightgrey))
        story.append(Paragraph(
            "N100 Financial Intelligence Platform  |  For internal use only",
            ParagraphStyle("Footer", fontSize=7, textColor=colors.grey,
                           alignment=TA_CENTER)
        ))

    doc.build(story)
    logger.success(f"Portfolio summary -> {output_path}")
    return output_path


if __name__ == "__main__":
    conn = sqlite3.connect(cfg.DB_PATH)
    generate_portfolio_summary(conn)
    conn.close()