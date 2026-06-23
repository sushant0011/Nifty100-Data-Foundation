from pathlib import Path
import pandas as pd


class ReportGenerator:

    def __init__(
        self,
        analytics_dir="output",
        report_dir="output"
    ):

        self.analytics_dir = Path(analytics_dir)
        self.report_dir = Path(report_dir)

    def generate_report(self):

        print("=" * 60)
        print("Generating Final Report")
        print("=" * 60)

        report = []

        files = [
            "analytics_summary.csv",
            "top_market_cap.csv",
            "top_roe.csv",
            "top_roce.csv",
            "sector_summary.csv"
        ]

        for file in files:

            path = self.analytics_dir / file

            if not path.exists():
                continue

            report.append("=" * 60)
            report.append(file)
            report.append("=" * 60)

            df = pd.read_csv(path)

            report.append(df.to_string(index=False))
            report.append("")

        output_file = self.report_dir / "final_report.txt"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(report))

        print(f"Report Saved : {output_file}")

        print("=" * 60)
        print("Report Generation Completed")
        print("=" * 60)