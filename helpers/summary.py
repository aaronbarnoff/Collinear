#!/usr/bin/env python3
import os
import csv
import argparse

# Search through output folder for all results folders and collect data
# Not yet updated for new -e param and change to b param

OUTPUT_DIR = os.path.abspath(os.path.join(os.getcwd(), "..", "output"))
SUMMARY_FILE = "summary.csv"

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=0, help="summarize results for first n results in /output (test)")
    ap.add_argument("-T", "--filter-timeout", default="0", help="filter by timeout value")
    return ap.parse_args()

def parse_folder_fields(name):
    # looking for folders in /output with name format e.g. "res_k4_n9_x0_y0_s1_c0_v1_a0_l0_b0.0_f0_r0_2025-09-18_17-48-25"
    p = name.split("_")
    k    = p[1][1:]; n = p[2][1:];  x = p[3][1:];  y = p[4][1:]
    s    = p[5][1:]; c = p[6][1:];  v = p[7][1:];  a = p[8][1:]
    l    = p[9][1:]; b = p[10][1:]; f = p[11][1:]; seed = p[12][1:]
    id_  = "_".join(p[13:]) if len(p) > 13 else ""
    return k,n,x,y,s,c,v,a,l,b,f,seed,id_

def scan_timeout(log_path):
    try:
        with open(log_path, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                if "Solver Timeout:" in line:
                    part = line.split(":", 1)[1].strip().split()[0]
                    return part[:-1] if part.endswith("s") else part
    except OSError:
        return "0"
    return "0"

def scan_status_and_cpu_time(log_path):
    status = None
    cpu_time = None
    try:
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
    except OSError:
        return "UNKNOWN", "0"

def main():
    args = parse_args()
    filter_timeout = args.filter_timeout

    processed = 0
    with open(SUMMARY_FILE, "w", newline="", encoding="utf-8") as out_csv:
        w = csv.writer(out_csv, lineterminator="\n")
        w.writerow([
            "k","n","x","y","symBreak","VHCard","VHBinary",
            "antidiag","lineLen","boundary","KNF",
            "seed","id","status","time","timeout","folder"
        ])

        with os.scandir(OUTPUT_DIR) as it:
            for e in it:
                name = e.name
                if not e.is_dir() or not name.startswith("res_"):
                    continue

                if args.n and processed >= args.n:
                    break

                try:
                    k,n,x,y,s,c,v,a,l,b,f,seed,id_ = parse_folder_fields(name)
                except Exception:
                    continue

                d = e.path
                log_path = os.path.join(d, "logOutput_k.log")
                if not os.path.isfile(log_path):
                    continue

                timeout = scan_timeout(log_path)
                if timeout != filter_timeout:
                    continue

                status, cpu_time = scan_status_and_cpu_time(log_path)
                if cpu_time == "0":
                    continue # ignoring cancelled/unfinished results

                w.writerow([k,n,x,y,s,c,v,a,l,b,f,seed,id_,status,cpu_time,timeout,d])
                processed += 1

    print(f"processed {processed} folders into {SUMMARY_FILE}")

if __name__ == "__main__":
    main()
