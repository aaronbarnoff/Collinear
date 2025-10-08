#!/usr/bin/env python3
import re, subprocess, argparse
from pathlib import Path

# This checks the slurm-*.out files for any "TIME LIMIT" errors and then runs seff on the job to check the wall-clock/CPU-time ratio.

LOG_OUT = "low_efficiency_timeouts.log"
JOB_RE        = re.compile(r"^slurm-(\d+)\.out$")
CPU_RE        = re.compile(r"CPU Efficiency:\s*([0-9]+(?:\.[0-9]+)?)%")
TIME_LIMIT_RE = re.compile(r"DUE TO TIME LIMIT", re.IGNORECASE)

def first_path_line(p: Path) -> str:
    try:
        with p.open(errors="ignore") as f:
            for line in f:
                if line.startswith("/"):
                    return line.strip()
    except: pass
    return ""

def file_has_time_limit(p: Path) -> bool:
    try:
        with p.open(errors="ignore") as f:
            for line in f:
                if TIME_LIMIT_RE.search(line):
                    return True
    except: pass
    return False

def seff_cpu(jobid: str):
    try:
        out = subprocess.check_output(["seff", jobid], text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return None
    m = CPU_RE.search(out)
    return float(m.group(1)) if m else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-c","--cutoff", type=float, default=75.0,
                    help="CPU efficiency cutoff percentage (default 75.0)")
    args = ap.parse_args()
    cutoff = float(args.cutoff)
    print(f"Using cutoff: {cutoff:.2f}%")

    records = []  # (job, path, cpu)
    for f in sorted(Path(".").glob("slurm-*.out")):
        m = JOB_RE.match(f.name)
        if not m: 
            continue
        if not file_has_time_limit(f):
            continue
        job  = m.group(1)
        path = first_path_line(f)
        cpu  = seff_cpu(job)
        if cpu is not None:
            records.append((job, path, cpu))

    kept = [(j,p,c) for (j,p,c) in records if c < cutoff]
    for j,p,c in kept:
        print(f"{j} {p} {c:.2f}%")

    if kept:
        Path(LOG_OUT).write_text("\n".join(f"{j} {p} {c:.2f}%" for j,p,c in kept) + "\n")
        print(f"\nWrote {len(kept)} low-efficiency TIMEOUT jobs to {LOG_OUT}")
    else:
        print(f"No TIMEOUT jobs under {cutoff:.2f}% CPU efficiency found.")

if __name__ == "__main__":
    main()
