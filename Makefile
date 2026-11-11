.PHONY: reproduce test
reproduce:
	python scripts/reproduce.py
test:
	python -m unittest discover -s tests -v
