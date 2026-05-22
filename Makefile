.PHONY: install install-dev test lint typecheck format format-check clean ci pre-commit-install

PIP = pip

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e .
	$(PIP) install -r requirements-dev.txt

test:
	pytest -v --cov=yt_dlp_script

lint:
	ruff check src/ tests/

typecheck:
	mypy src/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

format-check:
	ruff format --check src/ tests/

ifeq ($(OS),Windows_NT)
clean:
	@if exist build rmdir /s /q build
	@if exist dist rmdir /s /q dist
	@for /d /r . %%d in (*.egg-info .pytest_cache .mypy_cache __pycache__) do @if exist "%%d" rmdir /s /q "%%d" 2>nul
else
clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
endif

pre-commit-install:
	pre-commit install

ci: lint format-check typecheck test
