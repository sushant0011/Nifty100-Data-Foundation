from etl.loader import ExcelLoader


def main():

    loader = ExcelLoader()

    data = loader.load_all_files()

    print(f"\nSuccessfully loaded {len(data)} datasets.")


if __name__ == "__main__":
    main()