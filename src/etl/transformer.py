from pathlib import Path
import pandas as pd


class DataTransformer:

    def __init__(
        self,
        processed_dir="data/processed",
        transformed_dir="data/transformed"
    ):
        self.processed_dir = Path(processed_dir)
        self.transformed_dir = Path(transformed_dir)

        self.transformed_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.audit = []

    def standardize_columns(self, df):
        """
        Standardize column names.
        """

        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
        )

        return df

    def clean_text(self, df):
        """
        Remove leading and trailing spaces from text columns.
        """

        for column in df.select_dtypes(include="object").columns:
            df[column] = (
                df[column]
                .astype(str)
                .str.strip()
            )

        return df

    def convert_numeric(self, df):
        """
        Convert numeric columns wherever possible.
        """

        for column in df.columns:

            if column in ["id", "company_id"]:
                continue

            try:
                df[column] = pd.to_numeric(df[column])
            except Exception:
                pass

        return df

    def convert_dates(self, df):
        """
        Convert date column to datetime.
        """

        if "date" in df.columns:

            df["date"] = pd.to_datetime(
                df["date"],
                errors="coerce"
            )

        return df

    def transform_all(self):
        """
        Perform transformations on all processed CSV files.
        """

        csv_files = sorted(
            self.processed_dir.glob("*.csv")
        )

        if not csv_files:
            raise FileNotFoundError(
                "No processed CSV files found."
            )

        print("=" * 60)
        print("Starting Data Transformation")
        print("=" * 60)

        for file in csv_files:

            print(f"\nTransforming : {file.name}")

            df = pd.read_csv(file)

            rows_before = len(df)

            # Apply transformations
            df = self.standardize_columns(df)
            df = self.clean_text(df)
            df = self.convert_numeric(df)
            df = self.convert_dates(df)

            # Remove duplicate rows
            df = df.drop_duplicates()

            rows_after = len(df)

            # Save transformed CSV
            output_file = self.transformed_dir / file.name

            df.to_csv(
                output_file,
                index=False
            )

            # Audit information
            self.audit.append({
                "file": file.name,
                "rows_before": rows_before,
                "rows_after": rows_after,
                "duplicates_removed": rows_before - rows_after,
                "status": "Success"
            })

            print(f"Saved : {output_file}")

        # Save audit report
        audit_df = pd.DataFrame(self.audit)

        audit_df.to_csv(
            "output/transformation_audit.csv",
            index=False
        )

        print("\n" + "=" * 60)
        print("Transformation Completed")
        print("=" * 60)
        print("Audit Saved : output/transformation_audit.csv")