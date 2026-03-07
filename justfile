# Requires Java and Maven (mvn) to be installed.
setup:
    #!/usr/bin/env bash
    set -euo pipefail

    echo "--- SUTime: downloading JARs via Maven ---"
    SUTIME_DIR=$(uv run python -c "import sutime, os; print(os.path.dirname(sutime.__file__))")
    mkdir -p jars
    mvn dependency:copy-dependencies -f "$SUTIME_DIR/pom.xml" -DoutputDirectory="$(pwd)/jars" -P english
    cp "$SUTIME_DIR/jars/stanford-corenlp-sutime-python-1.4.0.jar" "$(pwd)/jars/"

    echo "--- HeidelTime: patching with macOS ARM64 TreeTagger binary ---"
    HT_BIN=$(uv run python -c "import importlib.util; from pathlib import Path; print(Path(importlib.util.find_spec('py_heideltime').origin).parent / 'Heideltime' / 'TreeTaggerLinux' / 'bin' / 'tree-tagger')")
    ARCH=$(uname -m)
    if [ "$ARCH" != "arm64" ] && [ "$ARCH" != "x86_64" ]; then
        echo "Unknown architecture $ARCH — skipping TreeTagger patch"
    elif file "$HT_BIN" | grep -q "ELF"; then
        TAGGER_URL="https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-MacOSX-M1-3.2.3.tar.gz"
        TMPDIR=$(mktemp -d)
        echo "Downloading macOS TreeTagger binary..."
        curl -fsSL "$TAGGER_URL" -o "$TMPDIR/tt.tar.gz"
        tar -xzf "$TMPDIR/tt.tar.gz" -C "$TMPDIR"
        cp "$TMPDIR/bin/tree-tagger" "$HT_BIN"
        chmod +x "$HT_BIN"
        rm -rf "$TMPDIR"
        echo "Patched: $HT_BIN"
    else
        echo "TreeTagger binary already looks like a native binary — skipping patch"
        file "$HT_BIN"
    fi

    echo "--- Setup complete ---"

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
