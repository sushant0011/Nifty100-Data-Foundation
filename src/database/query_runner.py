from pathlib import Path
import sqlite3
import pandas as pd


class QueryRunner:

    def __init__(self, database_path="database.db"):
        self.database_path = Path(database_path)

    def run_queries(self):

        print("=" * 60)
        print("Running SQL Queries")
        print("=" * 60)

        connection = sqlite3.connect(self.database_path)

        queries = {
            "total_companies": """
                SELECT COUNT(*) AS total_companies
                FROM companies;
            """,

            "top_market_cap": """
                SELECT company_id, market_cap_crore
                FROM market_cap
                ORDER BY market_cap_crore DESC
                LIMIT 10;
            """,

            "top_stock_prices": """
                SELECT company_id, MAX(close_price) AS highest_price
                FROM stock_prices
                GROUP BY company_id
                ORDER BY highest_price DESC
                LIMIT 10;
            """
        }

        for name, sql in queries.items():

            print(f"\n{name}")

            result = pd.read_sql(sql, connection)

            print(result)

            result.to_csv(
                f"output/{name}.csv",
                index=False
            )

        connection.close()

        print("\n" + "=" * 60)
        print("SQL Queries Completed")
        print("=" * 60)