#!/usr/bin/env bash
#SBATCH --account=def-cbright
#SBATCH --job-name=CUBE_ARRAY
#SBATCH --cpus-per-task=1
#mem-per-cpu moved out

# Parse options
if ! options=$(getopt -o r:n:k:f:i: -- "$@"); then
    echo "Error: invalid options"
    exit 2
fi
eval set -- "$options"

solver_type=-1
n=-1
k=-1
results_folder=""
cubes_file_name=""

while true; do
    case "$1" in
        -f) solver_type="$2";           shift 2;;
        -n) n="$2";                     shift 2;;
        -k) k="$2";                     shift 2;;
        -r) results_folder="$2";        shift 2;;
        -i) cubes_file_name="$2";       shift 2;;
        --)                             shift; break;;
        *) echo "Unknown option: $1"; exit 1;;
    esac
done

cwd="$(pwd)"
echo "n:$n, k:$k, solver:$solver_type, folder: $results_folder"

if [[ -z "$res_folder" ]]; then
    echo "Error: require folder"
    exit 1
fi
if (( n < 0 )); then
    echo "Error: missing or invalid -n"
    exit 1
fi
if (( k < 0 )); then
    echo "Error: missing or invalid -k"
    exit 1
fi
if (( solver_type < 0 )); then
    echo "Error: missing or invalid -s/--solver"
    exit 1
fi

echo "$results_folder"

output_dir="$cwd/output/$results_folder"
if [[ ! -d "$output_dir" ]]; then
    echo "Error: Directory '$output_dir' does not exist"
    exit 1
fi

log_dir="$output_dir/logs"
mkdir -p "$log_dir"

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

if [[ ! -f "$dimacs_file" ]]; then
    echo "Error: dimacs_file '$dimacs_file' not found"
    exit 1
fi
if [[ ! -f "$cubes_file" ]]; then
    echo "Error: cubes_file '$cubes_file' not found"
    exit 1
fi

cube_line=$(grep -E '^a ' "$cubes_file" | sed -n "$((SLURM_ARRAY_TASK_ID + 1))p")
if [[ -z "$cube_line" ]]; then
    echo "No cube line for index $SLURM_ARRAY_TASK_ID in $cubes_file"
    exit 1
fi

lits=$(printf '%s\n' "$cube_line" \
       | sed 's/#.*//' \
       | awk '{for (i = 2; i <= NF && $i != "0"; i++) print $i}')

extra=$(printf '%s\n' "$lits" | wc -l)

echo "Running task ID $SLURM_ARRAY_TASK_ID on $dimacs_file with cube $cube_line, total $extra clauses."
echo "Fixed assignments (and errors) saved to: $output_dir/${SLURM_ARRAY_TASK_ID}_fixed_assignments.txt"

(
  awk -v extra="$extra" '
    /^p[ \t]/ && !done {
        $4 = $4 + extra
        done = 1
        print
        next
    }
    { print }
  ' "$dimacs_file"

  for lit in $lits; do
      printf "%s 0\n" "$lit"
  done
) | "$solver_path" > "$log_dir/${SLURM_ARRAY_TASK_ID}_solver_log.txt" 2> "$output_dir/${SLURM_ARRAY_TASK_ID}_fixed_assignments.txt"

SOLVER_EXIT_CODE=$?

case $SOLVER_EXIT_CODE in
    10)
        echo "Result: SATISFIABLE"
        python3 -u helpers/verify_solution.py -k "$k" -n "$n" -f "$log_dir/${SLURM_ARRAY_TASK_ID}_solver_log.txt"
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
