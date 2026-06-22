from pathlib import Path
import pandas as pd


class ExcelLoader:
    def __init__(self, raw_dir="data/raw", processed_dir="data/processed"):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)

        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def load_all_files(self):
        excel_files = sorted(self.raw_dir.glob("*.xlsx"))

        if not excel_files:
            raise FileNotFoundError("No Excel files found in data/raw")

        dataframes = {}
        summary = []

        print("=" * 60)
        print("Starting ETL Loader")
        print("=" * 60)

        for file in excel_files:

            try:
                print(f"\nLoading : {file.name}")

                df = pd.read_excel(file, header=1)

                dataframes[file.stem] = df

                output_file = self.processed_dir / f"{file.stem}.csv"

                df.to_csv(output_file, index=False)

                summary.append({
                    "file": file.name,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "status": "Success"
                })

                print(f"Rows    : {len(df)}")
                print(f"Columns : {len(df.columns)}")
                print("Status  : Success")

            except Exception as e:

                summary.append({
                    "file": file.name,
                    "rows": 0,
                    "columns": 0,
                    "status": f"Failed : {e}"
                })

                print(f"Error loading {file.name}")
                print(e)

        audit = pd.DataFrame(summary)
        audit.to_csv("output/load_audit.csv", index=False)

        print("\n")
        print("=" * 60)
        print("Loading Completed")
        print("=" * 60)

        return dataframes