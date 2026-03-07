#!/usr/bin/env bash
set -euo pipefail

if ! options=$(getopt -o r: -- "$@"); then
    echo "Error: invalid options"
    exit 2
fi
eval set -- "$options"

results_folder=""
while true; do
    case "$1" in
        -r) results_folder="$2"; shift 2;;
        --) shift; break;;
        *) echo "Unknown option: $1"; exit 1;;
    esac
done

if [[ -z "$results_folder" ]]; then
    echo "Error: require results folder with -r"
    exit 1
fi

logs_dir="$PWD/../../output/$results_folder/logs"
if [[ ! -d "$logs_dir" ]]; then
    echo "Error: $logs_dir not found"
    exit 1
fi

set -- "$logs_dir"/*.txt
if [[ "$1" == "$logs_dir/*.txt" ]]; then
    echo "No .txt files found in $logs_dir"
    exit 0
fi

pattern='^c total process time since initialization:'
total="0"
max_time=""
max_file=""
cnt=0
for f in "$@"; do
    line=$(grep -E "$pattern" -- "$f" | tail -n1 || true)
    if [[ -z "$line" ]]; then
        echo "Warning: time line not found in $f" >&2
        continue
    fi
    time_val=$(printf '%s\n' "$line" | grep -oE '[0-9]+(\.[0-9]+)?' | head -n1 || true)
    if [[ -z "$time_val" ]]; then
        #echo "Warning: could not parse time in $f" >&2
        continue
    fi
    total=$(printf '%s + %s\n' "$total" "$time_val" | bc -l)

    if [[ -z "$max_time" ]]; then
        max_time="$time_val"
        max_file="$f"
    else
        cmp=$(printf '%s > %s\n' "$time_val" "$max_time" | bc -l)
        if [[ "$cmp" -eq 1 ]]; then
            max_time="$time_val"
            max_file="$f"
        fi
    fi
done

if [[ "$total" == "0" && -z "$max_time" ]]; then
    echo "No times parsed."
    exit 0
fi

printf "Total UNSAT/SAT process time: %.2f seconds\n" "$total"
printf "Longest single file time: %.2f seconds (%s)\n" "$max_time" "$max_file"
printf "Approximate total time: %.2f seconds\n" "$total_2"
