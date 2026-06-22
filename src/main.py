from etl.loader import ExcelLoader
from etl.validator import DataValidator


def main():

    loader = ExcelLoader()
    loader.load_all_files()

    validator = DataValidator()
    validator.validate()


if __name__ == "__main__":
    main()