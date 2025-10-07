#!/usr/bin/env python3
import csv
import statistics
from collections import defaultdict

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
    "hybrid",
    "k_plus_c",
    "status",
]

TRIALS = 1
POST_MEDIAN = 1 if TRIALS == 1 else (TRIALS + 1) // 2
SIMPLE = (TRIALS == 1)

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

        if SIMPLE:
            if trial_count > 0:
                row["avg"] = round(statistics.mean(times), 2)
                row["min"] = round(min(times), 2)
                row["max"] = round(max(times), 2)
                row["median"] = round(statistics.median(times), 2)
            else:
                row["avg"] = row["min"] = row["max"] = row["median"] = float("inf")
        else:
            if trial_count >= POST_MEDIAN:
                s = sorted(times)
                row["avg"] = round(statistics.mean(times), 2)
                row["min"] = round(min(times), 2)
                row["max"] = round(max(times), 2)
                row["median"] = round(s[POST_MEDIAN - 1], 2)
            else:
                row["avg"] = row["min"] = row["max"] = row["median"] = float("inf")

        out_tests.append(row)

    out_tests.sort(key=sort_cols)

    sum_medians = round(sum(
        r["median"] for r in out_tests
        if isinstance(r["median"], float) and r["median"] != float("inf")
    ), 2)

    print(f"Writing grouped table: {OUTPUT}")
    print(f"Sum of medians across {len([r for r in out_tests if isinstance(r['median'], float) and r['median'] != float('inf')])} completed groups: {sum_medians}")

    headers = keys + ["count","avg","min","max","median"]
    with open(OUTPUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=headers)
        w.writeheader()
        w.writerows(out_tests)

def sort_cols(r):
    def to_int(v, d=0):
        s = ("" if v is None else str(v).strip())
        if s == "":
            return d
        try:
            return int(float(s))
        except:
            return d

    def to_float(v, d=0.0):
        s = ("" if v is None else str(v).strip())
        if s == "":
            return d
        try:
            return float(s)
        except:
            return d

    return (
        to_int(r.get("k")), to_int(r.get("n")),
        to_int(r.get("x")), to_int(r.get("y")), to_int(r.get("symBreak")),
        to_int(r.get("VHCard")), to_int(r.get("VHBinary")),
        to_int(r.get("antidiag")), to_int(r.get("lineLen")),
        to_float(r.get("boundary")), to_int(r.get("KNF")),
        to_int(r.get("timeout")),
        r.get("encoding") or "",
        to_int(r.get("hybrid")),
        to_int(r.get("k_plus_c")),
        r.get("status") or ""
    )

if __name__ == "__main__":
    main()
