from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


class Dashboard:

    def __init__(
        self,
        analytics_dir="output",
        charts_dir="output/charts"
    ):

        self.analytics_dir = Path(analytics_dir)
        self.charts_dir = Path(charts_dir)

        self.charts_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    def create_dashboard(self):

        print("=" * 60)
        print("Generating Dashboard")
        print("=" * 60)

        self.market_cap_chart()
        self.roe_chart()
        self.roce_chart()
        self.sector_chart()

        print("=" * 60)
        print("Dashboard Completed")
        print("=" * 60)

    def market_cap_chart(self):

        df = pd.read_csv(
            self.analytics_dir / "top_market_cap.csv"
        )

        plt.figure(figsize=(10,5))
        plt.bar(df["company_id"], df["market_cap"])
        plt.xticks(rotation=45)
        plt.title("Top Market Cap Companies")
        plt.tight_layout()

        plt.savefig(
            self.charts_dir / "top_market_cap.png"
        )

        plt.close()

    def roe_chart(self):

        df = pd.read_csv(
            self.analytics_dir / "top_roe.csv"
        )

        plt.figure(figsize=(10,5))
        plt.barh(
            df["company_name"],
            df["roe_percentage"]
        )

        plt.title("Top ROE Companies")
        plt.tight_layout()

        plt.savefig(
            self.charts_dir / "top_roe.png"
        )

        plt.close()

    def roce_chart(self):

        df = pd.read_csv(
            self.analytics_dir / "top_roce.csv"
        )

        plt.figure(figsize=(10,5))
        plt.barh(
            df["company_name"],
            df["roce_percentage"]
        )

        plt.title("Top ROCE Companies")
        plt.tight_layout()

        plt.savefig(
            self.charts_dir / "top_roce.png"
        )

        plt.close()

    def sector_chart(self):

        df = pd.read_csv(
            self.analytics_dir / "sector_summary.csv"
        )

        plt.figure(figsize=(8,8))
        plt.pie(
            df["total_companies"],
            labels=df["broad_sector"],
            autopct="%1.1f%%"
        )

        plt.title("Sector Distribution")

        plt.savefig(
            self.charts_dir / "sector_summary.png"
        )

        plt.close()