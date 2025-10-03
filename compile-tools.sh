#!/usr/bin/env bash

mkdir -p solvers
cd solvers

# Cadical
git clone https://github.com/arminbiere/cadical.git
cd cadical
./configure && make
cd ..

# Cardinality Cadical
git clone https://github.com/jreeves3/Cardinality-CDCL.git
cd Cardinality-CDCL
sh build.sh
cd ..

# Cadical-Exhaust
git clone https://github.com/curtisbright/cadical-exhaust.git
cd cadical-exhaust
./configure && make

# Cube-and-Conquer
git clone https://github.com/curtisbright/CnC.git
cd CnC
sh build.sh
cd ..

#set everything possible as executable (for CC)
#find . -type f -print0 | while IFS= read -r -d '' f; do if file -b "$f" | grep -qE 'executable|script text'; then chmod +x "$f"; fi; done