from pathlib import Path
import pandas as pd

REQUIRED_COLUMNS = {
    "balancesheet.csv": ["id", "company_id", "year"],
    "cashflow.csv": ["id", "company_id", "year"],
    "companies.csv": ["id", "company_name"],
    "documents.csv": ["id", "company_id"],
    "financial_ratios.csv": ["id", "company_id", "year"],
    "market_cap.csv": ["id", "company_id", "year"],
    "peer_groups.csv": ["id", "company_id"],
    "profitandloss.csv": ["id", "company_id", "year"],
    "prosandcons.csv": ["id"],
    "sectors.csv": ["id", "company_id"],
    "stock_prices.csv": ["id", "company_id", "date"],
}


class DataValidator:
    """
    Performs data quality validation on processed CSV files.
    """

    def __init__(self, processed_dir="data/processed"):
        self.processed_dir = Path(processed_dir)
        self.failures = []

    def validate(self):
        csv_files = sorted(self.processed_dir.glob("*.csv"))

        if not csv_files:
            raise FileNotFoundError("No processed CSV files found.")

        print("=" * 60)
        print("Starting Data Validation")
        print("=" * 60)

        for file in csv_files:

            print(f"\nValidating : {file.name}")

            df = pd.read_csv(file)

            self.check_empty(file.name, df)
            self.check_duplicate_rows(file.name, df)
            self.check_missing_values(file.name, df)
            self.check_primary_key(file.name, df)

        self.save_report()

    def check_empty(self, file_name, df):

        if df.empty:
            self.add_failure(file_name, "EMPTY_DATASET", "Dataset contains zero rows")

    def check_duplicate_rows(self, file_name, df):

        duplicates = df.duplicated().sum()

        if duplicates > 0:
            self.add_failure(
                file_name,
                "DUPLICATE_ROWS",
                f"{duplicates} duplicate rows found"
            )

    def check_missing_values(self, file_name, df):

        required = REQUIRED_COLUMNS.get(file_name, [])

        for column in required:

            if column not in df.columns:
                self.add_failure(
                    file_name,
                    "MISSING_COLUMN",
                    column
                )
                continue

            count = df[column].isnull().sum()

            if count > 0:
                self.add_failure(
                    file_name,
                    "MISSING_VALUES",
                    f"{column}: {count}"
                )

    def check_primary_key(self, file_name, df):

        if "id" not in df.columns:
            return

        if df["id"].isnull().any():
            self.add_failure(
                file_name,
                "PRIMARY_KEY_NULL",
                "Primary key contains NULL values"
            )

        duplicate_ids = df["id"].duplicated().sum()

        if duplicate_ids > 0:
            self.add_failure(
                file_name,
                "PRIMARY_KEY_DUPLICATE",
                f"{duplicate_ids} duplicate IDs"
            )

    def add_failure(self, file_name, rule, details):

        self.failures.append({
            "file": file_name,
            "rule": rule,
            "details": details
        })

    def save_report(self):

        report = pd.DataFrame(self.failures)

        report.to_csv(
            "output/validation_failures.csv",
            index=False
        )

        print("\n" + "=" * 60)
        print("Validation Completed")
        print("=" * 60)
        print(f"Issues Found : {len(report)}")
        print("Report Saved : output/validation_failures.csv")