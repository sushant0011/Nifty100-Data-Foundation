from pathlib import Path
import sqlite3
import pandas as pd


class Analytics:

    def __init__(
        self,
        database_path="database.db",
        output_dir="output"
    ):
        self.database_path = Path(database_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_reports(self):

        print("=" * 60)
        print("Starting Analytics")
        print("=" * 60)

        conn = sqlite3.connect(self.database_path)

        reports = {

            "analytics_summary": """
                SELECT
                    COUNT(*) AS total_companies,
                    AVG(roce_percentage) AS avg_roce,
                    AVG(roe_percentage) AS avg_roe
                FROM companies;
            """,

            "top_market_cap": """
                SELECT
                    company_id,
                    MAX(market_cap_crore) AS market_cap
                FROM market_cap
                GROUP BY company_id
                ORDER BY market_cap DESC
                LIMIT 10;
            """,

            "top_roe": """
                SELECT
                    company_name,
                    roe_percentage
                FROM companies
                ORDER BY roe_percentage DESC
                LIMIT 10;
            """,

            "top_roce": """
                SELECT
                    company_name,
                    roce_percentage
                FROM companies
                ORDER BY roce_percentage DESC
                LIMIT 10;
            """,

            "sector_summary": """
                SELECT
                    broad_sector,
                    COUNT(*) AS total_companies
                FROM sectors
                GROUP BY broad_sector
                ORDER BY total_companies DESC;
            """
        }

        for name, query in reports.items():

            print(f"\nGenerating : {name}")

            df = pd.read_sql(query, conn)

            print(df)

            df.to_csv(
                self.output_dir / f"{name}.csv",
                index=False
            )

        conn.close()

        print("\n" + "=" * 60)
        print("Analytics Completed")
        print("=" * 60)