#!/usr/bin/env bash
set -e

SOLVERS_DIR="$(pwd)/solvers"
mkdir -p "$SOLVERS_DIR"

if [ ! -d "$SOLVERS_DIR/Cardinality-CDCL" ]; then
  git clone git@github.com:jreeves3/Cardinality-CDCL.git "$SOLVERS_DIR/Cardinality-CDCL"
fi
if [ ! -f "$SOLVERS_DIR/Cardinality-CDCL/cardinality-cadical/build/cadical" ]; then
  cd "$SOLVERS_DIR/Cardinality-CDCL"
  sh build.sh
  cd - >/dev/null
fi

if [ ! -d "$SOLVERS_DIR/cadical" ]; then
  git clone git@github.com:arminbiere/cadical.git "$SOLVERS_DIR/cadical"
fi
if [ ! -f "$SOLVERS_DIR/cadical/build/cadical" ]; then
  cd "$SOLVERS_DIR/cadical"
  ./configure && make
  cd - >/dev/null
fi

echo "$SOLVERS_DIR/Cardinality-CDCL/cardinality-cadical/build/cadical"
echo "$SOLVERS_DIR/cadical/build/cadical"
