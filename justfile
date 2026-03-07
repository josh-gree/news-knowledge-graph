setup:
    #!/usr/bin/env bash
    SUTIME_DIR=$(uv run python -c "import sutime, os; print(os.path.dirname(sutime.__file__))")
    mvn dependency:copy-dependencies -f "$SUTIME_DIR/pom.xml" -DoutputDirectory="$SUTIME_DIR/jars" -P english

install-hooks:
    uv run pre-commit install

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
