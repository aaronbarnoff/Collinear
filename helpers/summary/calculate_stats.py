#!/usr/bin/env python3
import csv
import statistics
from collections import defaultdict

# Group tests and calculate median time from the random seeds
# Double check how timeout=0 is treated (e.g. used SBATCH timeout rather than SAT solver timeout)

INPUT = "summary.csv"
OUTPUT = "tables.csv"

keys = [
    "k","n","x","y",
    "symBreak",
    "VHCard","VHBinary",
    "antidiag","lineLen","boundary",
    "KNF",
    "timeout",
    "encoding",
]

def main():
    tests = defaultdict(list)

    with open(INPUT, newline="", encoding="utf-8") as f:
        table = csv.DictReader(f)
        for row in table:
            time_str = row.get("time", "").strip()
            try:
                t = float(time_str)
            except ValueError:
                continue

            key = tuple(row.get(col, "").strip() for col in keys)
            tests[key].append(t)

    out_tests = []
    for key, times in tests.items():
        row = dict(zip(keys, key))
        row["count"] = len(times)
        row["avg"] = round(statistics.mean(times), 2)
        row["min"] = round(min(times), 2)
        row["max"] = round(max(times), 2)
        row["median"] = round(statistics.median(times), 2)
        out_tests.append(row)

    out_tests.sort(key=sort_cols)

    sum_medians = round(sum(r["median"] for r in out_tests), 2)
    print(f"Writing grouped table: {OUTPUT}")
    print(f"Sum of medians across {len(out_tests)} groups: {sum_medians}")

    flagged = []
    for r in out_tests:
        try:
            to_val = float(r["timeout"])
            if to_val > 0 and r["max"] >= 0.85 * to_val:
                flagged.append(r)
        except ValueError:
            pass

    if flagged:
        print("Groups near timeout:")
        for r in flagged:
            print(
                f"k={r['k']} n={r['n']} x={r['x']} y={r['y']} "
                f"f={r['KNF']} b={r['boundary']} enc={r['encoding']} "
                f"count={r['count']} max={r['max']} timeout={r['timeout']}"
            )

    headers = keys + ["count","avg","min","max","median"]
    with open(OUTPUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=headers)
        w.writeheader()
        w.writerows(out_tests)

def sort_cols(r):
    return (
        int(r["k"]), int(r["n"]),
        int(r["x"]), int(r["y"]), int(r["symBreak"]),
        int(r["VHCard"]), int(r["VHBinary"]),
        int(r["antidiag"]), int(r["lineLen"]),
        float(r["boundary"]), int(r["KNF"]),
        int(float(r["timeout"])) if r["timeout"] != "" else 0,
        r["encoding"] or ""
    )

if __name__ == "__main__":
    main()
    