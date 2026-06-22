install:
	pip install -r requirements.txt

run:
	python src/main.py

test:
	pytest

format:
	black src tests

lint:
	flake8 src