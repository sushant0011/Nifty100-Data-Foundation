from src.etl.loader import ExcelLoader


def test_loader_object():
    loader = ExcelLoader()
    assert loader is not None


def test_raw_directory():
    loader = ExcelLoader()
    assert loader.raw_dir.exists()


def test_processed_directory():
    loader = ExcelLoader()
    assert loader.processed_dir.exists()


def test_excel_files_present():
    loader = ExcelLoader()
    files = list(loader.raw_dir.glob("*.xlsx"))
    assert len(files) == 12