#!/usr/bin/env bash
set -euo pipefail

DOCS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$DOCS_DIR/.." && pwd)"
SRC_DIR="$ROOT_DIR/src"
PACKAGE_DIR="$SRC_DIR/n10w02"
OUTPUT_DIR="$DOCS_DIR/_build/html"

export PYTHONPATH="$SRC_DIR:${PYTHONPATH:-}"

rm -rf "$DOCS_DIR/_build" "$DOCS_DIR/en/api" "$DOCS_DIR/ja/api"
mkdir -p "$OUTPUT_DIR" "$DOCS_DIR/en/api" "$DOCS_DIR/ja/api"

for lang in en ja; do
    sphinx-apidoc -f --module-first -o "$DOCS_DIR/$lang/api" "$PACKAGE_DIR"
    sphinx-build -b html -c "$DOCS_DIR" -D "language=$lang" "$DOCS_DIR/$lang" "$OUTPUT_DIR/$lang"
done

cp -a "$OUTPUT_DIR/en/." "$OUTPUT_DIR/"
touch "$OUTPUT_DIR/.nojekyll"
