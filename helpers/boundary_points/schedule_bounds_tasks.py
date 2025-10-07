#!/usr/bin/env python3
import subprocess
import time
import argparse

RUN_SCRIPT = "./run_bounds_tasks.sh"

COMMON_ARGS = [
    "-k", "7",
    "-l", "0",
    "-s", "1",
    "-v", "1",
    "-a", "0",
    "-c", "0",
    "-b", "2",
    "-t", "0",   # SAT solver timeout (wall-clock)
]

TEMPLATES = {
    # 1) points_all_180
    "points_all_180_CNF":     {"name": "points_all_180",     "f": 0, "i": 1, "mem": "4G",  "time": "24:00:00", "hybrid": "0", "seeds": "15"},
    "points_all_180_KNF":     {"name": "points_all_180",     "f": 1, "i": 1, "mem": "4G",  "time": "24:00:00", "hybrid": "0", "seeds": "15"},
    "points_all_180_HYBRID":  {"name": "points_all_180",     "f": 1, "i": 1, "mem": "4G",  "time": "24:00:00", "hybrid": "1", "seeds": "15"},

    # 2) points_all_past_180 (too slow)
    #"points_all_past_180_CNF":    {"name": "points_all_past_180", "f": 0, "i": 2, "mem": "12G", "time": "24:00:00", "hybrid": "0", "seeds": "1"},
    #"points_all_past_180_KNF":    {"name": "points_all_past_180", "f": 1, "i": 2, "mem": "4G",  "time": "24:00:00", "hybrid": "0", "seeds": "1"},
    #"points_all_past_180_HYBRID": {"name": "points_all_past_180", "f": 1, "i": 2, "mem": "12G",  "time": "24:00:00", "hybrid": "1", "seeds": "1"},

    # 3) points_SAT_180
    "points_SAT_180_CNF":     {"name": "points_SAT_180",     "f": 0, "i": 3, "mem": "4G",  "time": "04:00:00", "hybrid": "0", "seeds": "15"},
    "points_SAT_180_KNF":     {"name": "points_SAT_180",     "f": 1, "i": 3, "mem": "4G",  "time": "04:00:00", "hybrid": "0", "seeds": "15"},
    "points_SAT_180_HYBRID":  {"name": "points_SAT_180",     "f": 1, "i": 3, "mem": "4G",  "time": "04:00:00", "hybrid": "1", "seeds": "15"},

    # 4) points_UNSAT_180
    "points_UNSAT_180_CNF":   {"name": "points_UNSAT_180",   "f": 0, "i": 4, "mem": "4G",  "time": "04:00:00", "hybrid": "0", "seeds": "15"},
    "points_UNSAT_180_KNF":   {"name": "points_UNSAT_180",   "f": 1, "i": 4, "mem": "4G",  "time": "04:00:00", "hybrid": "0", "seeds": "15"},
    "points_UNSAT_180_HYBRID":{"name": "points_UNSAT_180",   "f": 1, "i": 4, "mem": "4G",  "time": "04:00:00", "hybrid": "1", "seeds": "15"},

    # 5) points_SAT_past_180  (too slow)
    #"points_SAT_past_180_CNF":    {"name": "points_SAT_past_180", "f": 0, "i": 5, "mem": "12G", "time": "24:00:00", "hybrid": "0", "seeds": "1"},
    #"points_SAT_past_180_KNF":    {"name": "points_SAT_past_180", "f": 1, "i": 5, "mem": "4G",  "time": "24:00:00", "hybrid": "0", "seeds": "1"},
    #"points_SAT_past_180_HYBRID": {"name": "points_SAT_past_180", "f": 1, "i": 5, "mem": "12G",  "time": "24:00:00", "hybrid": "1", "seeds": "1"},

    # 6) points_UNSAT_past_180  (too slow)
    #"points_UNSAT_past_180_CNF":    {"name": "points_UNSAT_past_180", "f": 0, "i": 6, "mem": "12G", "time": "24:00:00", "hybrid": "0", "seeds": "1"},
    #"points_UNSAT_past_180_KNF":    {"name": "points_UNSAT_past_180", "f": 1, "i": 6, "mem": "4G",  "time": "24:00:00", "hybrid": "0", "seeds": "1"},
    #"points_UNSAT_past_180_HYBRID": {"name": "points_UNSAT_past_180", "f": 1, "i": 6, "mem": "12G",  "time": "24:00:00", "hybrid": "1", "seeds": "1"},

    # 7) points_fast_SAT_past_180
    "points_fast_SAT_past_180_CNF":     {"name": "points_fast_SAT_past_180", "f": 0, "i": 7, "mem": "12G", "time": "24:00:00", "hybrid": "0", "seeds": "1"},
    "points_fast_SAT_past_180_KNF":     {"name": "points_fast_SAT_past_180", "f": 1, "i": 7, "mem": "4G",  "time": "24:00:00", "hybrid": "0", "seeds": "1"},
    "points_fast_SAT_past_180_HYBRID":  {"name": "points_fast_SAT_past_180", "f": 1, "i": 7, "mem": "12G",  "time": "24:00:00", "hybrid": "1", "seeds": "1"},

    # 8) points_fast_UNSAT_past_180
    "points_fast_UNSAT_past_180_CNF":    {"name": "points_fast_UNSAT_past_180", "f": 0, "i": 8, "mem": "12G", "time": "24:00:00", "hybrid": "0", "seeds": "1"},
    "points_fast_UNSAT_past_180_KNF":    {"name": "points_fast_UNSAT_past_180", "f": 1, "i": 8, "mem": "4G",  "time": "24:00:00", "hybrid": "0", "seeds": "1"},
    "points_fast_UNSAT_past_180_HYBRID": {"name": "points_fast_UNSAT_past_180", "f": 1, "i": 8, "mem": "12G",  "time": "24:00:00", "hybrid": "1", "seeds": "1"},
}

def submit(template_name, f_flag, i_val, mem_val, time_val, seed, w_val, j_val):
    jobname = f"{template_name}_r{seed}_j{j_val}"
    cmd = [
        "sbatch",
        f"--time={time_val}",
        f"--mem-per-cpu={mem_val}",
        f"--job-name={jobname}",
        RUN_SCRIPT,
    ] + COMMON_ARGS + [
        "-f", str(f_flag),
        "-i", str(i_val),
        "-r", str(seed),
        "-w", str(w_val),
        "-j", str(j_val),
    ]
    print(" ".join(cmd))
    out = subprocess.check_output(cmd, text=True).strip()
    print("->", out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("template", choices=list(TEMPLATES.keys()))
    ap.add_argument("-j", type=int, default=0,
                    help="Line-filter heuristic; block lines with length at least k+j")
    args = ap.parse_args()

    name = args.template
    cfg = TEMPLATES[name]
    folder_name = cfg["name"]
    f_flag = cfg["f"]
    i_val = cfg["i"]
    mem_val = cfg["mem"]
    time_val = cfg["time"]
    w_val = cfg["hybrid"]
    j_val = args.j
    seeds = int(cfg["seeds"])

    print(f"Submitting for folder: {folder_name}")

    for seed in range(1, seeds + 1):
        submit(folder_name, f_flag, i_val, mem_val, time_val, seed, w_val, j_val)
        time.sleep(1)

if __name__ == "__main__":
    main()

# These difficult points past 180 should be solved individually:
## UPPER SAT:
# "(84,163)" "(88,169)" "(90,171)" "(82,158)" "(82,161)" "(82,160)" "(87,167)" "(80,157)" "(82,159)" "(88,167)" "(87,166)" "(86,166)" "(83,162)" "(83,161)" "(90,170)" "(88,168)" "(85,164)" "(89,170)" "(78,156)" "(85,165)" "(89,169)" "(86,165)" "(5,28)" "(78,156)" "(80,157)" "(82,158)" "(82,159)" "(82,160)" "(82,161)" "(83,161)" "(83,162)" "(84,163)" "(85,164)" "(85,165)" "(86,165)" "(86,166)" "(87,166)" "(87,167)" "(88,167)" "(88,168)" "(88,169)" "(89,169)" "(89,170)" "(90,170)" "(90,171)"

## LOWER SAT:
# "(170,91)" "(170,90)" "(161,85)" "(164,86)" "(158,82)" "(156,81)" "(172,92)" "(155,81)" "(163,85)" "(155,79)" "(158,83)" "(168,90)" "(164,87)" "(167,89)" "(168,89)" "(159,83)" "(171,91)" "(173,93)" "(155,80)" "(167,88)" "(173,92)" "(171,92)" "(153,78)" "(165,88)" "(160,84)" "(169,90)" "(166,88)" "(157,81)" "(174,93)" "(161,84)" "(153,78)" "(155,79)" "(155,80)" "(155,81)" "(156,81)" "(157,81)" "(158,82)" "(158,83)" "(159,83)" "(160,84)" "(161,84)" "(161,85)" "(163,85)" "(164,86)" "(164,87)" "(165,88)" "(166,88)" "(167,88)" "(167,89)" "(168,89)" "(168,90)" "(169,90)" "(170,90)" "(170,91)" "(171,91)" "(171,92)" "(172,92)" "(173,92)" "(173,93)" "(174,93)"

## UPPER UNSAT:
# "(84,165)" "(89,171)" "(78,157)" "(85,166)" "(79,156)" "(88,170)" "(83,163)" "(86,167)" "(87,168)" "(77,156)" "(80,158)" "(81,159)" "(82,162)" "(30,86)" "(77,156)" "(78,157)" "(79,156)" "(80,158)" "(81,159)" "(82,162)" "(83,163)" "(84,165)" "(85,166)"

## LOWER UNSAT:
# "(172,91)" "(156,79)" "(165,86)" "(169,89)" "(174,92)" "(155,78)" "(166,87)" "(162,84)" "(160,83)" "(154,77)" "(154,77)" "(155,78)" "(156,79)" "(160,83)" "(162,84)" "(165,86)"
