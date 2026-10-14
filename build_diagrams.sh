#!/usr/bin/env bash
# Пересборка PNG/SVG из исходников Graphviz (нужен пакет graphviz: https://graphviz.org/download/)
set -e
cd "$(dirname "$0")"
for f in Diagrams/src/*.dot;   do b=$(basename "${f%.dot}"); dot -Tsvg "$f" -o "Diagrams/$b.svg";   dot -Tpng -Gdpi=150 "$f" -o "Diagrams/$b.png"; done
for f in Flowcharts/src/*.dot; do b=$(basename "${f%.dot}"); dot -Tsvg "$f" -o "Flowcharts/$b.svg"; dot -Tpng -Gdpi=150 "$f" -o "Flowcharts/$b.png"; done
echo "Готово"
