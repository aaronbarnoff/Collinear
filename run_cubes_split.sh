#!/usr/bin/env bash
#SBATCH --account=rrg-cbright
#SBATCH --job-name=CUBE_ARRAY
#SBATCH --cpus-per-task=1
#mem-per-cpu moved out

# This takes as argument:
# -f the "res_k..." folder which contains the <num>_dimacsFile.knf files.
# -s the solver type: 1=CNF, 2=KNF

# It is submitted as a job array of 0 to (<max_cube_number>-1) jobs

# example:
# ./run.sh -k 7 -n 282 -x 140 -y 141 -b 2 -j 10 -f 0 -p 1 -m 0
# python3 generate_cubes_diag.py -n 282 -d 2 -s 1 -o cubes.txt -f res_k7_n282_x140_y141_b2_f0_r0_j10_w0_z0_g0_q0_2025-11-17_00-36-06
# sbatch --array=0-53 --mem-per-cpu=12G --time=168:00:00 run_cubes.sh -k 7 -n 282 -s 1 -f res_k7_n282_x140_y141_b2_f0_r0_j10_w0_z0_g0_q0_2025-11-17_00-36-06

while [[ $# -gt 0 ]]; do
    case "$1" in
        -s|--solver)
            SOLVER_TYPE="$2"
            shift 2
            ;;
        -n)
            n="$2"
            shift 2
            ;;         
        -k)
            k="$2"
            shift 2
            ;;                  
        -f|--folder)
            CNF_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done
cwd="$(pwd)"
echo "n:$n, k:$k, solver:$SOLVER_TYPE, folder: $CNF_DIR"

if [[ -z "$CNF_DIR" ]]; then
    echo "Error: Missing -f <folder> argument"
    exit 1
fi

if [[ -z "$SOLVER_TYPE" ]]; then
    echo "Error: Missing solver type: 1=CNF, 2=KNF"
    exit 1
fi
echo $CNF_DIR

output_dir="$cwd/output/$CNF_DIR"
if [[ ! -d "$output_dir" ]]; then
    echo "Error: Directory '$output_dir' does not exist"
    exit 1
fi

LOG_DIR="$output_dir/logs"
mkdir -p "$LOG_DIR"

if (( $SOLVER_TYPE == 2)); then
echo "Solving KNF with Cardinality-CDCL"
SAT_SOLVER="$cwd/solvers/Cardinality-CDCL/cardinality-cadical/build/cadical" 
INPUT_FILE="$output_dir/dimacsFile.knf"
BASE_FILE="$output_dir/dimacsFile.knf" 
else
echo "Solving CNF with Cadical"
SAT_SOLVER="$cwd/solvers/cadical/build/cadical"
INPUT_FILE="$output_dir/dimacsFile.cnf"
BASE_FILE="$output_dir/dimacsFile.cnf" 
fi

CUBES_FILE="$output_dir/cubes.icnf"

if [[ ! -f "$BASE_FILE" ]]; then
    echo "Error: BASE_FILE '$BASE_FILE' not found"
    exit 1
fi
if [[ ! -f "$CUBES_FILE" ]]; then
    echo "Error: CUBES_FILE '$CUBES_FILE' not found"
    exit 1
fi

cube_line=$(grep -E '^a ' "$CUBES_FILE" | sed -n "$((SLURM_ARRAY_TASK_ID + 1))p")
if [[ -z "$cube_line" ]]; then
    echo "No cube line for index $task_id in $CUBES_FILE"
    exit 1
fi

lits=$(printf '%s\n' "$cube_line" \
       | sed 's/#.*//' \
       | awk '{for (i = 2; i <= NF && $i != "0"; i++) print $i}')

extra=$(printf '%s\n' "$lits" | wc -l)

echo "Running task ID $SLURM_ARRAY_TASK_ID on file $INPUT_FILE with cube $cube_line, total $extra clauses."
echo "Fixed assignments (and errors) saved to: $output_dir/${SLURM_ARRAY_TASK_ID}_fixed_assignments.txt"

#debug
#(
#  awk -v extra="$extra" '
#    /^[ \t]*p[ \t]/ && !done {
#        $4 = $4 + extra
#        done = 1
#        print
#        next
#    }
#    { print }
#  ' "$INPUT_FILE"
#
#  for lit in $lits; do
#      printf "%s 0\n" "$lit"
#  done
#) > "$output_dir/debug_patched_${SLURM_ARRAY_TASK_ID}.cnf"

(
  awk -v extra="$extra" '
    /^p[ \t]/ && !done {
        $4 = $4 + extra
        done = 1
        print
        next
    }
    { print }
  ' "$INPUT_FILE"

  for lit in $lits; do
      printf "%s 0\n" "$lit"
  done
) | "$SAT_SOLVER" > "$LOG_DIR/${SLURM_ARRAY_TASK_ID}_solver_log.txt" 2> "$output_dir/${SLURM_ARRAY_TASK_ID}_fixed_assignments.txt"

#"$SAT_SOLVER" "$INPUT_FILE" > "$LOG_DIR/${SLURM_ARRAY_TASK_ID}_solver_log.txt" 2> "$output_dir/${SLURM_ARRAY_TASK_ID}_fixed_assignments.txt"
SOLVER_EXIT_CODE=$?

case $SOLVER_EXIT_CODE in
    10)
        echo "Result: SATISFIABLE"
        python3 -u helpers/verify_solution.py -k "$k" -n "$n" -f "$LOG_DIR/${SLURM_ARRAY_TASK_ID}_solver_log.txt"
        VERIFY_EXIT_CODE=$?
        if ((VERIFY_EXIT_CODE == 0)); then
        echo "Solution verified, cancelling remaining cube jobs in array ${SLURM_ARRAY_JOB_ID}..."
        scancel "${SLURM_ARRAY_JOB_ID}"   # stop every other task in this job array
        fi
        ;;

    20)
        echo "Result: UNSATISFIABLE"
        ;;

    *)
        echo "Result: UNKNOWN or ERROR (exit code $SOLVER_EXIT_CODE)"
        ;;
esac