#!/usr/bin/env bash

mkdir -p solvers
cd solvers

# Cadical
git clone https://github.com/arminbiere/cadical.git
cd cadical
./configure && make
echo "$(pwd)/build/cadical"
cd ..

# Cardinality Cadical
git clone https://github.com/jreeves3/Cardinality-CDCL.git
cd Cardinality-CDCL
sh build.sh
echo "$(pwd)/cardinality-cadical/build/cadical"
cd ..

# Cadical-Exhaust
git clone https://github.com/curtisbright/cadical-exhaust.git
cd cadical-exhaust
./configure && make
echo "$(pwd)/build/cadical"

#set everything possible as executable (for CC)
#find . -type f -print0 | while IFS= read -r -d '' f; do if file -b "$f" | grep -qE 'executable|script text'; then chmod +x "$f"; fi; done