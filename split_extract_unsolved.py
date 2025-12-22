#!/usr/bin/env python3

import os
import argparse
import re


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", required=True, help="source/output folder")
    parser.add_argument("-i", required=True, help="cubes source file")
    parser.add_argument("-o", required=True, help="output cubes file")
    return vars(parser.parse_args())


args = parse_arguments()

results_folder = args["r"]
cubes_src_filename = args["i"]
cubes_dest_filename = args["o"]

cwd_path = os.getcwd()
results_folder_path = os.path.join(cwd_path, f"output/{results_folder}")
slurm_logs_path = os.path.join(results_folder_path, "slurm_logs")

cubes_src_path = os.path.join(cwd_path, cubes_src_filename)
cubes_dest_path = cubes_dest_filename if os.path.isabs(cubes_dest_filename) else os.path.join(cwd_path, cubes_dest_filename)

task_pat = re.compile(r'_(\d+)\.out$')


def extract_task_number(filename):
    m = task_pat.search(filename)
    if not m:
        return None
    return int(m.group(1))


def find_unsat_tasks():
    unsat_tasks = set()
    files_scanned = 0

    for root, _, files in os.walk(slurm_logs_path):
        for name in files:
            if not name.endswith(".out"):
                continue

            task = extract_task_number(name)
            if task is None:
                continue

            files_scanned += 1
            path = os.path.join(root, name)

            with open(path, "r", errors="ignore") as f:
                for line in f:
                    if "UNSATISFIABLE" in line:
                        unsat_tasks.add(task)
                        break

    return unsat_tasks, files_scanned


unsat_tasks, files_scanned = find_unsat_tasks()
print(f"Scanned {files_scanned} .out files in {slurm_logs_path}")
print(f"Found {len(unsat_tasks)} UNSAT tasks")

init_line_cnt = 0
kept_line_cnt = 0

with open(cubes_src_path, "r", errors="ignore") as fin, open(cubes_dest_path, "w") as fout:
    for task, line in enumerate(fin):
        init_line_cnt += 1
        if task in unsat_tasks:
            continue
        fout.write(line)
        kept_line_cnt += 1

print(f"Input cubes lines: {init_line_cnt}")
print(f"Kept cubes lines: {kept_line_cnt}")
print(f"Wrote: {cubes_dest_path}")