#!/usr/bin/env bash
set -euo pipefail

if ! options=$(getopt -o i:f: -- "$@"); then
    echo "Error: invalid options"
    exit 2
fi
eval set -- "$options"

res_folder=""
cubes_file_name=""

while true; do
    case "$1" in
        -f) res_folder="$2"; shift 2;;
        -i) cubes_file_name="$2"; shift 2;;   
        --) shift; break;;
        *) echo "Unknown option: $1"; exit 1;;
    esac
done

if [[ -z "$cubes_file_name" ]]; then
    echo "Error: require cube file"
    exit 1
fi

if [[ -z "$res_folder" ]]; then
    echo "Error: require results folder"
    exit 1
fi

base_dir="$PWD/output/$res_folder"
slurm_dir="$base_dir/slurm_logs"

cubes_file="$base_dir/$cubes_file_name"
base_name="${cubes_file_name%.icnf}"
trimmed_file="$base_dir/${base_name}_trimmed.icnf"


if [[ ! -d "$slurm_dir" ]]; then
    echo "Error: $slurm_dir not found"
    exit 1
fi

if [[ ! -f "$cubes_file" ]]; then
    echo "Error: $cubes_file not found"
    exit 1
fi

tmp_lines=$(mktemp)

for f in "$slurm_dir"/*.out; do
    [[ -e "$f" ]] || continue

    fname=$(basename "$f")

    case "$fname" in
        *"${base_name}"*.out) ;;
        *) continue ;;
    esac

    base_no_ext=${fname%.out}
    num_part=${base_no_ext##*_}

    case "$num_part" in
        *[!0-9]*|'') continue ;;
    esac

    if grep -q 'UNSATISFIABLE' "$f"; then
        continue
    else
        echo $((10#$num_part + 1)) >> "$tmp_lines"
    fi
done

if [[ ! -s "$tmp_lines" ]]; then
    echo "No matching cubes found (all UNSAT or no matching *.out files)"
    rm -f "$tmp_lines"
    exit 0
fi

: > "$trimmed_file"

sort -n "$tmp_lines" | uniq | while read -r line; do
    sed -n "${line}p" "$cubes_file" >> "$trimmed_file"
done

rm -f "$tmp_lines"

echo "Wrote trimmed cubes to: $trimmed_file"
