#!/usr/bin/env bash
#SBATCH --account=def-cbright
#SBATCH --job-name=CUBE_ARRAY
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=4G

# This takes as argument -f the "res_k..." folder which contains the <num>_dimacsFile.knf files.
# It is submitted as a job array of 0 to (<max_cube_number>-1) jobs
# e.g. For 114 cubes: "sbatch --array=0-113 --time=120:00:00 run_cube.sh -f results_k7_n305_id2025-05-23_17-27-15"

while [[ $# -gt 0 ]]; do
    case "$1" in
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

SAT_SOLVER="$cwd/solvers/Cardinality-CDCL/cardinality-cadical/build/cadical" 

# Redirect stdout/stderr manually into logs folder
#exec > "$LOG_DIR/out_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.txt"
#exec 2> "$LOG_DIR/err_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.txt"


echo "Running task ID $SLURM_ARRAY_TASK_ID on file $INPUT_FILE"

"$SAT_SOLVER" "$INPUT_FILE" > "$LOG_DIR/solverLog_${SLURM_ARRAY_TASK_ID}.txt"
SOLVER_EXIT_CODE=$?

case $SOLVER_EXIT_CODE in
    10)
        echo "Result: SATISFIABLE"
        ;;

    20)
        echo "Result: UNSATISFIABLE"
        ;;

    *)
        echo "Result: UNKNOWN or ERROR (exit code $SOLVER_EXIT_CODE)"
        ;;
esac