#!/usr/bin/env python3
import subprocess
import time

# this will run the different cardinality encodings, each on their own job, for up to n=180 (given by runBounds.sh)

RUN_SCRIPT = "./runBounds.sh"
SBATCH_TIME = "72:00:00"

COMMON_ARGS = [
    "-k", "7",
    "-l", "0",
    "-s", "1",
    "-v", "1",
    "-a", "0",
    "-c", "0",
    "-b", "2",
    "-f", "0",
    "-t", "7200",
]

# CNF cardinality encodings from pysat
ENCODINGS = [
    "seqcounter", "totalizer", "sortnetwrk",
    "cardnetwrk", "mtotalizer", "kmtotalizer",
]
SEEDS = range(1,16)  

for enc in ENCODINGS:
    for seed in SEEDS:
        jobname = f"{enc}_r{seed}"
        cmd = [
            "sbatch",
            f"--time={SBATCH_TIME}",
            f"--job-name={jobname}",
            RUN_SCRIPT,
        ] + COMMON_ARGS + ["-e", enc, "-r", str(seed)]
        print(" ".join(cmd))
        out = subprocess.check_output(cmd, text=True).strip()
        print(" ->", out)
        time.sleep(1)
