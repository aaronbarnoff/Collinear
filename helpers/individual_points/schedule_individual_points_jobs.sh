#!/usr/bin/env bash
set -euo pipefail

# This will call run_individual_points.py for all of the tests below

tests=(
  k6_n97_all
  k6_n98_all
  k7_n220_CNF
  k7_n220_KNF
  k7_n240_CNF
  k7_n240_KNF
  k7_n261_CNF
  k7_n261_KNF
  k7_n122_all
  k7_n151_CNF
  k7_n151_KNF
  k7_n180_CNF
  k7_n180_KNF
)

for t in "${tests[@]}"; do
  echo "Running $t"
  python3 individualRun.py "$t"
  sleep 1
done

echo "All runs submitted."