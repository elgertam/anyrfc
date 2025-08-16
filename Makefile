.PHONY: clean build build-clean test lint typecheck bump deploy testdeploy

# Clean all build artifacts and caches
clean:
	rm -rf dist/ build/ src/*.egg-info/ .pytest_cache/ .mypy_cache/ .ruff_cache/

# Build the package
build:
	uv build

# Clean and then build fresh
build-clean: clean build

# Run tests
test:
	uv run pytest

# Run linting
lint:
	uv run ruff check src/

# Run type checking
typecheck:
	uv run mypy src/

# Bump version using commitizen
bump:
	uv run cz bump --yes

deploy: build-clean
	uv run twine upload dist/*

testdeploy: build-clean
	uv run twine upload --repository testpypi dist/*
