.PHONY: build test serve
build:
	PYTHONPATH=src python -m aurelia_pension build
test: build
	PYTHONPATH=src python -m unittest discover -s tests -v
	node tests/test_engine.cjs
serve:
	PYTHONPATH=src python -m aurelia_pension serve
