#!/usr/bin/env python3
import subprocess
import time
import argparse

RUN_SCRIPT = "./run_bounds.sh"
SBATCH_TIME = "04:00:00" # should now only take an hour or so 

COMMON_ARGS = [
    "-k", "7",
    "-l", "0",
    "-s", "1",
    "-v", "1",
    "-a", "0",
    "-c", "0",
    "-b", "2",
    "-t", "7200",
]

SEEDS = range(1, 16)
SLEEP_BETWEEN = 1

TEMPLATES = {
    "run_sat_180":        {"f": 1, "i": 3},
    "run_sat_past_180":   {"f": 1, "i": 5},
    "run_unsat_180":      {"f": 0, "i": 4}, # run_bounds.sh is only configured for 4GB, so it likely will get OOM killed on CNF tasks beyond n180
    "run_unsat_past_180": {"f": 0, "i": 6},
}

def submit(template_name, f_flag, i_val, seed):
    jobname = f"{template_name}_{seed}"
    cmd = [
        "sbatch",
        f"--time={SBATCH_TIME}",
        f"--job-name={jobname}",
        RUN_SCRIPT,
    ] + COMMON_ARGS + ["-f", str(f_flag), "-i", str(i_val), "-r", str(seed)]
    print(" ".join(cmd))
    out = subprocess.check_output(cmd, text=True).strip()
    print("->", out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("template", choices=list(TEMPLATES.keys()) + ["run_all"])
    args = ap.parse_args()

    tasks = (
        [(name, TEMPLATES[name]["f"], TEMPLATES[name]["i"]) for name in TEMPLATES]
        if args.template == "run_all"
        else [(args.template, TEMPLATES[args.template]["f"], TEMPLATES[args.template]["i"])]
    )

    for name, f_flag, i_val in tasks:
        for seed in SEEDS:
            submit(name, f_flag, i_val, seed)
            time.sleep(SLEEP_BETWEEN)

if __name__ == "__main__":
    main()
