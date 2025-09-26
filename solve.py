import time
import argparse
import time
import os
import subprocess
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-k", default=5, help="number of collinear points to avoid")
    parser.add_argument("-n", default=28, help="n points; n-1 steps")
    parser.add_argument("-x", default=0, help="point x")
    parser.add_argument("-y", default=0, help="point y")
    parser.add_argument("-f", default=0, help="0=CNF (cadical), 1=KNF (card. cadical)")
    parser.add_argument("-e", default=None, help="CNF cardinality encoding type: seqcounter, totalizer, sortnetwrk, cardnetwrk, mtotalizer, kmtotalizer")
    parser.add_argument("-t", default=0, help="sat solver wall-clock timeout (s)")
    parser.add_argument("-r", default=0, help="SAT solver seed")
    parser.add_argument("-p", default=0, help="results folder name")
    parser.add_argument("-z", default=0, help="0=regular solve, 1=exhaustive (cadical-exhaust)")
    return vars(parser.parse_args())

args = parse_arguments()
k=int(args["k"])
n=int(args["n"])
px=int(args["x"])
py=int(args["y"])
use_KNF=int(args["f"])
cnf_encoding=(args["e"])
solver_timeout=int(args["t"])
solver_seed=int(args["r"])
results_folder_name=str(args["p"])
use_exhaustive_search=int(args["z"])

cwd_path = os.getcwd()

if use_KNF and use_exhaustive_search:
    print("KNF can't be used with exhaustive search (cadical-exhaust)")
    exit(-1)

output_folder_path = os.path.join(cwd_path, 'output')
if not os.path.exists(output_folder_path):
    os.makedirs(output_folder_path, exist_ok=True)

result_folder_path = os.path.join(output_folder_path, results_folder_name)
knf_dimacs_filename = f'dimacsFile.knf'
knf_dimacs_filepath = f'{result_folder_path}/{knf_dimacs_filename}'

cnf_dimacs_filename = f'dimacsFile.cnf'
cnf_dimacs_filepath = f'{result_folder_path}/{cnf_dimacs_filename}'

sat_log_filename = f'satOutput.log'
sat_log_filepath = f'{result_folder_path}/{sat_log_filename}'

out_log_filename = f'logOutput.log'
out_log_filepath = f'{result_folder_path}/{out_log_filename}'
out_log_file = open(f'{out_log_filepath}', 'a', buffering=1)

pysat_encode_path= f'{cwd_path}/solvers/Cardinality-CDCL/Tools/pysat_encode.py'
knf2cnf_path = f'{cwd_path}/solvers/Cardinality-CDCL/Tools/knf2cnf'
CCDCL_path = f'{cwd_path}/solvers/Cardinality-CDCL/cardinality-cadical/build/cadical'
CDCL_path = f'{cwd_path}/solvers/cadical/build/cadical'
CDCLEX_path = f'{cwd_path}/solvers/cadical-exhaust/build/cadical-exhaust'

sat_time_wc = 0
start_time = time.time()
end_time = 0

collinear_list = []
point_list = []

v = [[0 for _ in range(n)] for _ in range(n)]
tmp_cnt =1
for b in range(n):        # Define vars diagonally: 
    for x in range(n):
        y = b-x
        if y >= 0:
                v[x][y] = tmp_cnt
                tmp_cnt += 1

"""
Solve Regular
"""
def solve_regular():
    global sat_time_wc
    mode = "KNF" if use_KNF == 1 else "CNF"

    if mode == "CNF":
        #if cnf_encoding is not None:
        #    print(f"CNF Encode: {cnf_encoding}")
        #    out_log_file.write(f"CNF Encode: {cnf_encoding}\n")
        #else:
        #    print("CNF Encode: knf2cnf (sequential counter, linear AMO)")
        #    out_log_file.write("CNF Encode: knf2cnf (sequential counter, linear AMO)\n")
        knf2cnf()

    if mode == "KNF":
        command = [CCDCL_path, knf_dimacs_filepath, "-t", str(solver_timeout), f"--seed={solver_seed}", "--ccdclMode=0"]
    else:
        command = [CDCL_path, cnf_dimacs_filepath, "-t", str(solver_timeout), f"--seed={solver_seed}"]

    print(f"Starting ({mode}) solver:", time.time() - start_time, "seconds")

    sat_start = time.time()

    with open(sat_log_filepath, "w") as sat_log_file:
        proc = subprocess.Popen(command, stdout=sat_log_file, stderr=subprocess.STDOUT)
        proc.wait()

    sat_time_wc = time.time() - sat_start
    print("Finished SAT solver:", time.time() - start_time, "seconds")

    if proc.returncode == 10:
        print(f"SAT {sat_time_wc}s (wall)")
        out_log_file.write(f"SAT {sat_time_wc}s (wall)\n")
        extract_solution()
        verify_solution(point_list)
        return True
    elif proc.returncode == 20:
        print(f"UNSAT {sat_time_wc}s")
        out_log_file.write(f"UNSAT {sat_time_wc}s (wall)\n")
        get_cpu_time()
        return False
    else:
        print(f"Solver error: exit code {proc.returncode}")
        out_log_file.write(f"Solver error: exit code {proc.returncode}\n")
        return False


"""
Solve Exhaustively
"""
def solve_exhaustive():
    global sat_time_wc

    #if cnf_encoding is not None:
    #    print(f"CNF Encode: {cnf_encoding}")
    #    out_log_file.write(f"CNF Encode: {cnf_encoding}\n")
    #else:
    #    print("CNF Encode: knf2cnf (sequential counter, linear AMO)")
    #    out_log_file.write("CNF Encode: knf2cnf (sequential counter, linear AMO)\n")
    knf2cnf()

    maxVar = 1
    for b in range(n):          # Pass cadical-exhaust max var to block
        for x in range(n):
            y = b-x
            if y >= 0:
                    v[x][y] = maxVar
                    maxVar += 1

    command = [CDCLEX_path, cnf_dimacs_filepath, "-t", str(solver_timeout), f"--seed={solver_seed}", f"--order", f"{maxVar}"]

    print(f"Starting exhaustive solver:", time.time() - start_time, "seconds")

    sat_start = time.time()

    with open(sat_log_filepath, "w") as sat_log_file:
        proc = subprocess.Popen(command, stdout=sat_log_file, stderr=subprocess.STDOUT)
        proc.wait()

    sat_time_wc = time.time() - sat_start
    print("Finished SAT solver:", time.time() - start_time, "seconds")

    if proc.returncode == 20: # Should always return UNSAT
        print(f"UNSAT {sat_time_wc}s")
        out_log_file.write(f"UNSAT {sat_time_wc}s (wall)\n") # Total time from all solves
        get_cpu_time()
        get_num_solns()
        return False
    else:
        print(f"Solver error: exit code {proc.returncode}")
        out_log_file.write(f"Solver error: exit code {proc.returncode}\n")
        return False
    



"""
Extract
"""
def extract_solution():
    global point_list
    print("Extract Model:", time.time() - start_time, "seconds")

    model = []
    cpu_time = None
    with open(sat_log_filepath, "r") as logFile:
        for line in logFile:
            if line.startswith("v "):
                model.extend(map(int, line[2:].strip().split()))
            elif line.startswith("c total process time since initialization:"):
                parts = line.strip().split()
                if len(parts) >= 2:
                    cpu_time = parts[-2]

    point_list = []
    for x in range(n):
        for y in range(n):
            if y < n - x:
                if v[x][y] in model:
                    point_list.append((x, y))

    with open(sat_log_filepath, "a") as logFile:
        logFile.write(f"Results n={n}, k={k} 0\n")

    if cpu_time is not None:
        out_log_file.write(f"CPU solve time: {cpu_time} seconds\n")
        print(f"CPU Time: {cpu_time} seconds")
        out_log_file.flush()

def get_cpu_time():
    try:
        with open(sat_log_filepath, "r") as f:
            for line in f:
                if line.startswith("c total process time since initialization:"):
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        cpu_time = parts[-2]
                        out_log_file.write(f"CPU solve time: {cpu_time} seconds\n")
                        print(f"CPU Time: {cpu_time} seconds")
                        out_log_file.flush()
                        return
    except FileNotFoundError:
        return

def get_num_solns():
    try:
        with open(sat_log_filepath, "r") as f:
            for line in f:
                if line.startswith("c Number of solutions: "):
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        num_solns = parts[-1]
                        out_log_file.write(f"Number of solutions: {num_solns}.\n")
                        print(f"Number of solutions: {num_solns}.")
                        out_log_file.flush()
                        return
    except FileNotFoundError:
        return



"""
Verify
"""
def verify_solution(point_list):
    print("Confirming Results:", time.time() - start_time, "seconds")
    for (x1, y1) in point_list:
        for (x2, y2) in point_list:
            if (x1, y1) == (x2, y2):
                continue
            if (x2 < x1) or (y2 < y1):
                continue
            m_p = x2-x1
            m_q = y2-y1
            tmp_point_list = []
            count = 2
            tmp_point_list.append((x1,y1))
            tmp_point_list.append((x2,y2))

            #print(f'({x1},{y1}), ({x2}, {y2}); slope: {m_p}/{m_q} = {m_p/m_q}')
            x = x2
            y = y2
            while (x < n) and (y < n - x):
                x += m_p
                y += m_q
                if (x, y) in point_list:
                    count += 1
                    tmp_point_list.append((x, y))
            if count >= k:
                # print(tmpPointsList)
                collinear_list.append(tmp_point_list)    

    if collinear_list:
        print(f"Failure: {k} or more points found on the same line.")
        out_log_file.write(f"Failure: {k} or more points found on the same line.\n")
        for line in collinear_list:
            (x1, y1)= line[0]
            (x2, y2)= line[1]
            if (x2 - x1) == 0:
                print('vline. points: ', end="")
                out_log_file.write(f"vline. points: ")
            elif (y2 - y1) == 0:
                print('hline. points: ', end="")
                out_log_file.write(f"hline. points: ")
            else:
                print(f'slope: {((y2 - y1) / (x2 - x1)):.2g}; m_p: {(y2-y1)}, m_q: {(x2-x1)}; points: ',end="")
                out_log_file.write(f"slope: {((y2 - y1) / (x2 - x1)):.2g}; m_p: {(y2-y1)}, m_q: {(x2-x1)}; points: ")
            for points in line:
                (x, y)=points
                print(f'({x},{y}) ', end="")
                out_log_file.write(f"({x},{y}) ")
            print("")
            out_log_file.write(f"\n")




"""
Convert KNF to CNF
"""
def knf2cnf():
    print("Converting to CNF file:", time.time() - start_time, "seconds")

    cnf_output_file = open(cnf_dimacs_filepath, 'w+')

    if cnf_encoding is None:
        command = f'\'{knf2cnf_path}\' \'{knf_dimacs_filepath}\''
        result = subprocess.Popen(command, shell=True, stdout=cnf_output_file, stderr=subprocess.PIPE, text=True)
        result.wait()
    else:
        command = ["python3", pysat_encode_path, "-k", knf_dimacs_filepath, "-c", cnf_dimacs_filepath, "-e", cnf_encoding]
        #print(command)
        result = subprocess.Popen(command, stdout=out_log_file, stderr=subprocess.STDOUT)
        result.wait()


    cnf_output_file.close()
    time.sleep(1) 



def main():
    if not use_exhaustive_search:
        solve_regular()
    else:
        solve_exhaustive()
    out_log_file.close()

    print("Finished:", time.time() - start_time, "seconds")

if __name__ == "__main__":
    main()
