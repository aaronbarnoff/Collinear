#!/usr/bin/env bash
set -uo pipefail

usage() {
cat << EOF
Usage: $0 [options]

Example: 
  Generate dimacs with CNF and then split on y=n/2-x for final point (49,50): 
      ./split_run.sh -n 100 -x 49 -y 50 -f 0 -m 1 -d 2 -o "cubes_1.icnf" -c 0 (creates folder output/res_k7_n100_x49_y50_b2_f0_r0_j10_w0_z0_g0_q0_2025-12-01_18-13-11)
  Split it again on y=n/3-x:
      ./split_run.sh -n 100 -x 49 -y 50 -f 0 -m 1 -d 3 -i "cubes_1.icnf" -o "cubes_2.icnf" -c 0 -r "res_k7_n100_x49_y50_b2_f0_r0_j10_w0_z0_g0_q0_2025-12-01_18-13-11"
  Split it again on y=2n/3-x, then schedule those cubes to run for 168 hours on compute canada:
      ./split_run.sh -n 100 -x 49 -y 50 -f 0 -m 2 -d 3 -i "cubes_2.icnf" -o "cubes_3.icnf" -c 1 -r "res_k7_n100_x49_y50_b2_f0_r0_j10_w0_z0_g0_q0_2025-12-01_18-13-11" -t 168
Options:
  -n   num points in path
  -x   final point x (default 0)
  -y   final point y (default 0)
  -f   0=CNF (cadical), 1=KNF (cardinality cadical) (default 0)
  -m   numerator for line y=(m*n)/d-x
  -d   denominator for line y=(m*n)/d-x
  -i   input cube file (if blank, create folder and generate dimacs file, then cube on line)
  -o   output cube file 
  -r   results folder for input cube file
  -t   sbatch wall clock timeout in hours
  -s   seed
  -c   schedule resulting cubes on compute canada 
  -z   z=1: don't split (use same -i and -o file name)
  -h   help
EOF
}

if ! options=$(getopt -o hx:y:f:n:t:r:i:o:m:d:c:s:z: -- "$@"); then
    usage
    exit 2
fi
eval set -- "$options"
c=0
n=0
fx=0
fy=0
solve_type=0
m=1
d=1
slurm_timeout=0
input_file_name="none"
output_file_name="cubes_out.icnf"
results_folder="none"
seed=0
nosplit=0
while true; do
  case "$1" in
    -h) usage; exit 0 ;;
    -n) n="$2"; shift 2 ;;
    -x) fx="$2"; shift 2 ;;
    -y) fy="$2"; shift 2 ;;
    -f) solve_type="$2"; shift 2 ;;
    -t) slurm_timeout="$2"; shift 2 ;;
    -r) results_folder="$2"; shift 2 ;;
    -i) input_file_name="$2"; shift 2 ;;
    -o) output_file_name="$2"; shift 2 ;;
    -m) m="$2"; shift 2 ;;
    -d) d="$2"; shift 2 ;;
    -c) c="$2"; shift 2 ;;  
    -s) seed="$2"; shift 2 ;;
    -z) nosplit="$2"; shift 2 ;;
    --) shift; break ;;
    *)  echo "Bad option"; usage; exit 2 ;;
  esac
done

if ((fx != 0 && fy != 0)); then
    if ((n != fx+fy+1));then
        echo "Error: n != x+y+1"
        exit 1
    fi
fi

if ((nosplit==0)); then
    if [[ "$input_file_name" == "none" ]]; then
        run_id="$(date +%F_%H-%M-%S)"
        results_folder="res_k7_n${n}_x${fx}_y${fy}_b2_f${solve_type}_r0_j10_w0_z0_g0_q0_${run_id}"
        echo "Generating dimacs file for ${results_folder}"
        ./run.sh -k 7 -n $n -x $fx -y $fy -f $solve_type -j 10 -p 1 -m 0
        sleep 1
        
        echo "Generating split cubes on line y=(${m}/${d})${n}-x"
        python3 split_generate_cubes.py -n $n -fx $fx -fy $fy -m $m -d $d -o "${output_file_name}" -r "${results_folder}"
        sleep 1
    else
        if [[ "$results_folder" == "none" ]]; then
            echo "results folder required for input cubes"
            exit 2
        fi
        echo "Generating split cubes on line y=(${m}/${d})${n}-x"
        python3 split_generate_cubes.py -n $n -fx $fx -fy $fy -m $m -d $d -i "${input_file_name}" -o "${output_file_name}" -r "${results_folder}"
        sleep 1
    fi
fi

full_dir="$PWD/output/${results_folder}"
cnt=$(grep -c '^a ' "$full_dir/$output_file_name")

if (( cnt == 0 )); then
    echo "No cube lines found in ${results_folder}"
    exit 1
fi
last=$((cnt - 1)) 

mkdir -p "$full_dir/slurm_logs"

if (( c == 1 && slurm_timeout <= 0 )); then
    echo "Error: invalid slurm timeout"
    exit 2
fi

if ((c==1)); then
    echo "Scheduling cubes with timeout: ${slurm_timeout} hours, 4G ram (expected for n~=288 and j=10)"
    echo sbatch --array=0-$last --mem-per-cpu=4G --time="${slurm_timeout}:00:00" --output="$full_dir/slurm_logs/k7_n${n}_x${fx}_y${fy}_f${solve_type}_o${output_file_name%.icnf}_%A_%a.out" \
        split_run_task.sh -k 7 -n "$n" -f "$solve_type" -i "$output_file_name" -r "$results_folder" -s "$seed"
    sbatch --array=0-$last --mem-per-cpu=4G --time="${slurm_timeout}:00:00" --output="$full_dir/slurm_logs/k7_n${n}_x${fx}_y${fy}_f${solve_type}_o${output_file_name%.icnf}_%A_%a.out" \
        split_run_task.sh -k 7 -n "$n" -f "$solve_type" -i "$output_file_name" -r "$results_folder" -s "$seed"
fi
echo "Done"