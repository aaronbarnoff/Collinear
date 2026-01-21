#!/usr/bin/env bash
#SBATCH --account=def-cbright
#SBATCH --job-name=CUBE_ARRAY
#SBATCH --cpus-per-task=1
#mem-per-cpu moved out

# Parse options
if ! options=$(getopt -o r:n:k:f:i:s:v: -- "$@"); then
    echo "Error: invalid options"
    exit 2
fi
eval set -- "$options"

solver_type=-1; n=-1; k=-1; results_folder=""; cubes_file_name=""; seed=0; FA_in_dir=""

while true; do
    case "$1" in
        -f) solver_type="$2";           shift 2;;
        -n) n="$2";                     shift 2;;
        -k) k="$2";                     shift 2;;
        -r) results_folder="$2";        shift 2;;
        -i) cubes_file_name="$2";       shift 2;;
        -s) seed="$2";                  shift 2;;
        -v) FA_in_dir="$2";             shift 2;;
        --)                             shift; break;;
        *) echo "Unknown option: $1"; exit 1;;
    esac
done

cwd="$(pwd)"
echo "n:$n, k:$k, solver:$solver_type, folder: $results_folder, seed: $seed"

if [[ -z "$results_folder" ]]; then echo "Error: require folder"; exit 1; fi
if (( n < 0 )); then echo "Error: missing or invalid -n"; exit 1; fi
if (( k < 0 )); then echo "Error: missing or invalid -k"; exit 1; fi
if (( solver_type < 0 )); then echo "Error: missing or invalid -f"; exit 1; fi

output_dir="$cwd/output/$results_folder"
if [[ ! -d "$output_dir" ]]; then echo "Error: Directory '$output_dir' does not exist"; exit 1; fi

log_dir="$output_dir/logs"
mkdir -p "$log_dir"

fa_out_dir="$output_dir/fixed_assignments_out"
mkdir -p "$fa_out_dir"

fa_in_dir=$FA_in_dir #"$output_dir/fixed_assignments_in"
#mkdir -p "$fa_in_dir"

tmp_dimacs_dir="$output_dir/tmp_dimacs"
mkdir -p "$tmp_dimacs_dir"

if (( solver_type == 1 )); then
    echo "Solving KNF with Cardinality-CDCL"
    solver_path="$cwd/solvers/Cardinality-CDCL/cardinality-cadical/build/cadical"
    dimacs_file="$output_dir/dimacsFile.knf"
elif (( solver_type == 0 )); then
    echo "Solving CNF with Cadical"
    solver_path="$cwd/solvers/cadical/build/cadical"
    dimacs_file="$output_dir/dimacsFile.cnf"
else
    echo "invalid solver"
    exit 1
fi

cubes_file="$output_dir/$cubes_file_name"

if [[ ! -f "$dimacs_file" ]]; then echo "Error: dimacs_file '$dimacs_file' not found"; exit 1; fi
if [[ ! -f "$cubes_file" ]]; then echo "Error: cubes_file '$cubes_file' not found"; exit 1; fi

idx=$SLURM_ARRAY_TASK_ID   # using --array=1-N and cubes_file line 1 is task 1

line_text=$(sed -n "${idx}p" "$cubes_file" | sed 's/#.*//')
if [[ -z "$line_text" ]]; then
  echo "Line $idx for task $SLURM_ARRAY_TASK_ID not found in $cubes_file"
  exit 1
fi

cube_line="${idx}:${line_text}"
points=$(awk '{print $1}' <<< "$line_text")
fa_points=""
if [[ "$points" == *_*_* ]]; then
  fa_points="${points%_*}"
  fa_points="${fa_points%_*}"
fi

fa_in_dir="$FA_in_dir"
fa_in=""
if [[ -n "$fa_in_dir" && -n "$fa_points" ]]; then
  fa_in="$fa_in_dir/${fa_points}_FA_in.txt"
fi

tmp_dimacs_file="$tmp_dimacs_dir/pts${points}_task${SLURM_ARRAY_TASK_ID}_tmp_dimacs.txt"

echo "dimacs file: $dimacs_file"
echo "task id: $SLURM_ARRAY_TASK_ID"
echo "cube: $cube_line"
echo "points: $points"
echo "FA input: $fa_in"
echo "tmp dimacs: $tmp_dimacs_file"

mapfile -t lits < <(awk '
  {
    a_pos = 0
    for (i = 1; i <= NF; i++) {
      if ($i == "a") { a_pos = i; break }
    }
    if (a_pos == 0) exit
    for (i = a_pos + 1; i <= NF && $i != "0"; i++) {
      print $i
    }
  }' <<< "$line_text")

extra=${#lits[@]}
echo "cube lits ($extra): ${lits[*]}"

fa_lits=()
fa_extra=0
if [[ -n "$fa_in" && -f "$fa_in" ]]; then
    mapfile -t fa_lits < <(awk '/^z[ \t]+[+-]?[0-9]+/ {print $2}' "$fa_in")
    fa_extra=${#fa_lits[@]}
    echo "FA lits ($fa_extra): ${fa_lits[*]}"
fi

extra_total=$((extra + fa_extra))

echo "Fixed assignment output (and errors) saved to: $fa_out_dir/${points}_FA_out.txt"

(
  awk -v add="$extra_total" '
    /^p[ \t]/ && !done { $4 = $4 + add; done = 1; print; next }
    { print }
  ' "$dimacs_file"

  for lit in "${lits[@]}"; do
      printf "%s 0\n" "$lit"
  done

  for lit in "${fa_lits[@]}"; do
      printf "%s 0\n" "$lit"
  done
) | tee "$tmp_dimacs_file" | "$solver_path" --seed="$seed" > "$log_dir/${points}_solver_log.txt" 2> "$fa_out_dir/${points}_FA_out.txt"

SOLVER_EXIT_CODE=$?

case $SOLVER_EXIT_CODE in
    10)
        echo "Result: SATISFIABLE"
        python3 -u helpers/verify_solution.py -k "$k" -n "$n" -f "$log_dir/${points}_solver_log.txt"
        VERIFY_EXIT_CODE=$?
        if (( VERIFY_EXIT_CODE == 0 )); then
            echo "Solution verified, cancelling remaining cube jobs in array ${SLURM_ARRAY_JOB_ID}..."
            scancel "${SLURM_ARRAY_JOB_ID}"
        fi
        ;;
    20)
        echo "Result: UNSATISFIABLE"
        ;;
    *)
        echo "Result: UNKNOWN or ERROR (exit code $SOLVER_EXIT_CODE)"
        ;;
esac
