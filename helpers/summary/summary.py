#!/usr/bin/env python3
import os
import csv
import argparse

#this needs to be redone to grab #trials from slurm logs

OUTPUT_DIR = os.path.abspath(os.path.join(os.getcwd(), "..", "..", "output"))
SUMMARY_FILE = "summary.csv"

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=0)
    ap.add_argument("-T", "--filter-timeout", default="0")
    return ap.parse_args()

def scan_status_and_cpu_time(log_path):
    status = None
    cpu_time = None
    with open(log_path, encoding="utf-8", errors="ignore") as fh:
        for raw in fh:
            line = raw.strip()
            if status is None and (line.startswith("SAT ") or line.startswith("UNSAT ") or line.startswith("UNKNOWN ")):
                if not line.startswith("CPU solve time:"):
                    status = line.split()[0]
            if cpu_time is None and line.startswith("CPU solve time:"):
                try:
                    cpu_time = line.split(":", 1)[1].strip().split()[0]
                except Exception:
                    pass
    return status or "UNKNOWN", cpu_time or "0"

def scan_params(log_path):
    with open(log_path, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if line.startswith("k:"):
                parts = [p.strip() for p in line.split(",") if p.strip()]
                kv = {}
                for p in parts:
                    if ":" in p:
                        k, v = p.split(":", 1)
                        kv[k.strip()] = v.strip()
                return kv
    return {}

def iter_res_dirs(root, depth=0, max_depth=3):
    if depth > max_depth:
        return
    for e in os.scandir(root):
        if not e.is_dir():
            continue
        if e.name.startswith("res_"):
            yield e.path
        else:
            yield from iter_res_dirs(e.path, depth + 1, max_depth)

def main():
    args = parse_args()
    processed = 0

    with open(SUMMARY_FILE, "w", newline="", encoding="utf-8") as out_csv:
        w = csv.writer(out_csv, lineterminator="\n")
        w.writerow([
            "k","n","x","y","symBreak","VHCard","VHBinary",
            "antidiag","lineLen","boundary","KNF",
            "seed","encoding","hybrid","k_plus_c",
            "id","status","time","timeout","folder"
        ])

        for d in iter_res_dirs(OUTPUT_DIR):
            if args.n and processed >= args.n:
                break
            log_path = os.path.join(d, "logOutput.log")
            if not os.path.isfile(log_path):
                continue

            params = scan_params(log_path)
            if not params:
                continue

            status, cpu_time = scan_status_and_cpu_time(log_path)
            if cpu_time == "0":
                continue

            k = params.get("k",""); n = params.get("n",""); x = params.get("x",""); y = params.get("y","")
            s = params.get("sym_break",""); vhc = params.get("vh_card",""); vhl = params.get("vh_line","")
            a = params.get("antidiag",""); line_len = params.get("cutoff",""); b = params.get("boundary","")
            knf = params.get("solver",""); seed = params.get("seed",""); enc = params.get("encoding","")
            timeout = params.get("timeout",""); hybrid = params.get("hybrid_mode",""); k_plus_c = params.get("(k+c)","")

            if not all([k, n, x, y, s, vhc, vhl, a, line_len, b, knf, seed]):
                print(f"Skipping corrupted entry in folder: {d}")
                continue

            w.writerow([
                k,n,x,y,s,vhc,vhl,a,line_len,b,knf,
                seed,enc,hybrid,k_plus_c,
                "",status,cpu_time,timeout,d
            ])
            processed += 1

    print(f"processed {processed} folders into {SUMMARY_FILE}")

if __name__ == "__main__":
    main()
