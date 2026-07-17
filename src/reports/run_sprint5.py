"""
run_sprint5.py — Sprint 5 Full Runner.

Runs all Sprint 5 components in order:
  1. NLP Parser         — parse analysis text
  2. Pros Cons Generator — auto generate pros and cons
  3. Cash Flow Intelligence — CFO quality, CapEx, distress flags
  4. Tearsheet PDFs     — 92 company tearsheets
  5. Sector PDFs        — 11 sector reports
  6. Portfolio PDF      — portfolio summary

Run: python -m src.reports.run_sprint5
"""

import sqlite3
from src.utils.logger import logger
from src.utils.config import cfg


def main():
    logger.info("=" * 60)
    logger.info("Sprint 5 — NLP + Reports + Cash Flow Intelligence")
    logger.info("=" * 60)

    # Step 1: NLP Parser
    logger.info("Step 1: NLP Analysis Parser...")
    try:
        from src.nlp.parser import run_parser
        run_parser()
    except Exception as e:
        logger.error(f"NLP Parser failed: {e}")

    # Step 2: Pros Cons Generator
    logger.info("Step 2: Auto Pros Cons Generator...")
    try:
        from src.nlp.pros_cons_generator import ProsConsGenerator
        ProsConsGenerator().run()
    except Exception as e:
        logger.error(f"Pros Cons Generator failed: {e}")

    # Step 3: Cash Flow Intelligence
    logger.info("Step 3: Cash Flow Intelligence...")
    try:
        from src.analytics.cashflow_intelligence import CashFlowIntelligence
        CashFlowIntelligence().run()
    except Exception as e:
        logger.error(f"Cash Flow Intelligence failed: {e}")

    # Step 4: Tearsheet PDFs
    logger.info("Step 4: Generating Company Tearsheets...")
    try:
        from src.reports.tearsheet import TearsheetBatchRunner
        TearsheetBatchRunner().run()
    except Exception as e:
        logger.error(f"Tearsheet generation failed: {e}")

    # Step 5: Sector PDFs
    logger.info("Step 5: Generating Sector Reports...")
    try:
        from src.reports.sector_report import SectorReportBatchRunner
        SectorReportBatchRunner().run()
    except Exception as e:
        logger.error(f"Sector report generation failed: {e}")

    # Step 6: Portfolio Summary PDF
    logger.info("Step 6: Generating Portfolio Summary...")
    try:
        from src.reports.portfolio_summary import generate_portfolio_summary
        conn = sqlite3.connect(cfg.DB_PATH)
        generate_portfolio_summary(conn)
        conn.close()
    except Exception as e:
        logger.error(f"Portfolio summary failed: {e}")

    logger.success("Sprint 5 complete!")


if __name__ == "__main__":
    main()