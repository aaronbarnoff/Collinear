#!/usr/bin/env bash
#SBATCH --account=rrg-cbright
#SBATCH --job-name=CUBE_ARRAY
#SBATCH --cpus-per-task=1
#mem-per-cpu moved out

# This takes as argument:
# -f the "res_k..." folder which contains the <num>_dimacsFile.knf files.
# -s the solver type: 1=CNF, 2=KNF

# It is submitted as a job array of 0 to (<max_cube_number>-1) jobs
# e.g. For 114 cubes: "sbatch --array=0-113 --mem-per-cpu=4G --time=72:00:00 run_cubes.sh -s 1 -f results_k7_n305_id2025-05-23_17-27-15"

while [[ $# -gt 0 ]]; do
    case "$1" in
        -s|--solver)
            SOLVER_TYPE="$2"
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

LOG_DIR="$output_dir/logs"
mkdir -p "$LOG_DIR"

INPUT_FILE="$output_dir/${SLURM_ARRAY_TASK_ID}_dimacsFile.knf"
if [[ ! -d "$output_dir" ]]; then
    echo "Error: Directory '$output_dir' does not exist"
    exit 1
fi
echo "Opening $output_dir..."

if (( $SOLVER_TYPE == 1)); then
SAT_SOLVER="$cwd/solvers/Cardinality-CDCL/cardinality-cadical/build/cadical" 
else
SAT_SOLVER="$cwd/solvers/cadical/build/cadical" 
fi

echo "Running task ID $SLURM_ARRAY_TASK_ID on file $INPUT_FILE"

"$SAT_SOLVER" "$INPUT_FILE" > "$LOG_DIR/${SLURM_ARRAY_TASK_ID}_solver_log.txt" 2> "$output_dir/${SLURM_ARRAY_TASK_ID}_fixed_assignments.txt"
SOLVER_EXIT_CODE=$?

case $SOLVER_EXIT_CODE in
    10)
        echo "Result: SATISFIABLE"
        python3 -u helpers/verify_solution.py -k "$k" -n "$n" -f "$LOG_DIR/${SLURM_ARRAY_TASK_ID}_solver_log.txt" 
        ;;

    20)
        echo "Result: UNSATISFIABLE"
        ;;

    *)
        echo "Result: UNKNOWN or ERROR (exit code $SOLVER_EXIT_CODE)"
        ;;
esac