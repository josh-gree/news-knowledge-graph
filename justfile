# Requires Java and Maven (mvn) to be installed.
setup:
    #!/usr/bin/env bash
    SUTIME_DIR=$(uv run python -c "import sutime, os; print(os.path.dirname(sutime.__file__))")
    mkdir -p jars
    mvn dependency:copy-dependencies -f "$SUTIME_DIR/pom.xml" -DoutputDirectory="$(pwd)/jars" -P english
    cp "$SUTIME_DIR/jars/stanford-corenlp-sutime-python-1.4.0.jar" "$(pwd)/jars/"

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
