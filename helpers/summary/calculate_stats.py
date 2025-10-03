#!/usr/bin/env python3
import csv
import statistics
from collections import defaultdict
# (untested with new changes)

# Group tests and calculate median time from the random seeds; assumes 15 trials
# Treats unfinished tests as having a solve time of INF.
# Gives groups with less than 8 completed tests inf median time

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

# (This assumes the tests were all scheduled around the same time)
TRIALS = 15                         # Assume all tests have 15 trials; any missing trials (unfinished) are given INF time
POST_MEDIAN = (TRIALS + 1) // 2     # Ignore unfinished trials after the median is known

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
            trial_count = len(times)
            row["count"] = trial_count

        if trial_count >= POST_MEDIAN:
            row["avg"] = round(statistics.mean(times), 2)
            row["min"] = round(min(times), 2)
            row["max"] = round(max(times), 2)
        else:
            row["avg"] = float("inf")
            row["min"] = float("inf")
            row["max"] = float("inf")

        if trial_count < POST_MEDIAN:
            row["median"] = float("inf")
            print("Incomplete group:",
                  row["k"], row["n"], row["x"], row["y"], row["symBreak"],
                  row["VHCard"], row["VHBinary"], row["antidiag"], row["lineLen"],
                  row["boundary"], row["KNF"], row["timeout"], row["encoding"])
        else:
            s = sorted(times)
            row["median"] = round(s[POST_MEDIAN - 1], 2)

        out_tests.append(row)

    out_tests.sort(key=sort_cols)

    sum_medians = sum(
        r["median"] for r in out_tests
        if isinstance(r["median"], float) and r["median"] != float("inf") # Ignore INF times for the total time calculation
    )
    sum_medians = round(sum_medians, 2)

    print(f"Writing grouped table: {OUTPUT}")
    print(f"Sum of medians across {len(out_tests)} completed groups: {sum_medians}")

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
