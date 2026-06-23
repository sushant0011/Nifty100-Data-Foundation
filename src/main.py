from etl import transformer
from etl.loader import ExcelLoader
from etl.validator import DataValidator
from etl.transformer import DataTransformer
from database.database_loader import DatabaseLoader
from database.database_validator import DatabaseValidator
from database.query_runner import QueryRunner


def main():

    loader = ExcelLoader()
    loader.load_all_files()

    validator = DataValidator()
    validator.validate()

    transformer = DataTransformer()
    transformer.transform_all()

    database = DatabaseLoader()
    database.load_all()

    db_validator = DatabaseValidator()
    db_validator.validate()

    query = QueryRunner()
    query.run_queries()


if __name__ == "__main__":
    main()