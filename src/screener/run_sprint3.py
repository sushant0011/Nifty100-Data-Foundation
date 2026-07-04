"""
run_sprint3.py — Sprint 3 Full Runner.

Runs all Sprint 3 components in order:
  1. Peer Engine       — compute peer percentile rankings
  2. Radar Charts      — generate PNG radar charts
  3. Screener Export   — screener_output.xlsx (6 presets)
  4. Peer Export       — peer_comparison.xlsx (11 peer groups)

Run: python -m src.screener.run_sprint3
"""

from src.utils.logger import logger
from src.analytics.peer import PeerEngine
from src.analytics.radar import RadarChartEngine
from src.screener.exporter import export_screener_excel, export_peer_comparison_excel


def main():
    logger.info("=" * 60)
    logger.info("Sprint 3 — Screener & Peer Comparison Engine")
    logger.info("=" * 60)

    # Step 1: Peer percentile rankings
    logger.info("Step 1: Computing peer percentile rankings...")
    try:
        PeerEngine().run()
    except Exception as e:
        logger.error(f"PeerEngine failed: {e}")

    # Step 2: Radar charts
    logger.info("Step 2: Generating radar charts...")
    try:
        RadarChartEngine().run()
    except Exception as e:
        logger.error(f"RadarChartEngine failed: {e}")

    # Step 3: Screener Excel export
    logger.info("Step 3: Exporting screener_output.xlsx...")
    try:
        export_screener_excel()
    except Exception as e:
        logger.error(f"Screener export failed: {e}")

    # Step 4: Peer comparison Excel export
    logger.info("Step 4: Exporting peer_comparison.xlsx...")
    try:
        export_peer_comparison_excel()
    except Exception as e:
        logger.error(f"Peer comparison export failed: {e}")

    logger.success("Sprint 3 complete!")


if __name__ == "__main__":
    main()