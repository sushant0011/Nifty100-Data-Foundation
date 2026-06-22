from etl import transformer
from etl.loader import ExcelLoader
from etl.validator import DataValidator
from etl.transformer import DataTransformer


def main():

    loader = ExcelLoader()
    loader.load_all_files()

    validator = DataValidator()
    validator.validate()

    transformer = DataTransformer()
    transformer.transform_all()


if __name__ == "__main__":
    main()