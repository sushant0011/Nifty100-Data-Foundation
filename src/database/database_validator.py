from pathlib import Path
import sqlite3
import pandas as pd


class DatabaseValidator:

    def __init__(
        self,
        database_path="database.db"
    ):

        self.database_path = Path(database_path)
        self.audit = []

    def validate(self):

        print("=" * 60)
        print("Starting Database Validation")
        print("=" * 60)

        connection = sqlite3.connect(
            self.database_path
        )

        tables = pd.read_sql(
            "SELECT name FROM sqlite_master WHERE type='table';",
            connection
        )

        for table in tables["name"]:

            rows = pd.read_sql(
                f"SELECT COUNT(*) AS total FROM {table}",
                connection
            )["total"][0]

            self.audit.append({
                "table": table,
                "rows": rows,
                "status": "Success"
            })

            print(f"{table:<25} {rows}")

        connection.close()

        audit = pd.DataFrame(self.audit)

        audit.to_csv(
            "output/database_audit.csv",
            index=False
        )

        print("\n" + "=" * 60)
        print("Database Validation Completed")
        print("=" * 60)
        print("Audit Saved : output/database_audit.csv")