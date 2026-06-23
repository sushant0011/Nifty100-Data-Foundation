from pathlib import Path
import sqlite3
import pandas as pd


class DatabaseLoader:

    def __init__(
        self,
        transformed_dir="data/transformed",
        database_path="database.db"
    ):

        self.transformed_dir = Path(transformed_dir)
        self.database_path = database_path

    def load_all(self):

        csv_files = sorted(
            self.transformed_dir.glob("*.csv")
        )

        if not csv_files:
            raise FileNotFoundError(
                "No transformed CSV files found."
            )

        print("=" * 60)
        print("Starting Database Load")
        print("=" * 60)

        connection = sqlite3.connect(
            self.database_path
        )

        for file in csv_files:

            print(f"\nLoading : {file.name}")

            df = pd.read_csv(file)

            table_name = file.stem

            df.to_sql(
                table_name,
                connection,
                if_exists="replace",
                index=False
            )

            print(
                f"Rows Loaded : {len(df)}"
            )

        connection.close()

        print("\n" + "=" * 60)
        print("Database Loading Completed")
        print("=" * 60)