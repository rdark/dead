.PHONY: test clean

# test
test:
	python -m pytest -vs

# remove pyc & __pycache__ files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
