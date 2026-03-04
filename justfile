test:
    uv run pytest

lint:
    uv run ruff check

fmt:
    uv run ruff format

check: lint test

shell:
    uv run python

jupyter:
    uv run jupyter lab
