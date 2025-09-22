import time
import subprocess

from globals import g, verify_solution, knf2cnf

logFileN = f'{g.result_path}/{g.sat_log_filename}'

def solve_regular():
    if g.use_KNF == 1: 
        res = solveKNF()
    else:
        res = solveCNF()
    if res:
        extractModel()
        verify_solution(g.point_list)
    else:
        getCPUTime() # unsat

def solveCNF():
    if g.cnf_encoding is not None:
        print(f"CNF Encode: {g.cnf_encoding}")
        g.out_log_file.write(f"CNF Encode: {g.cnf_encoding}\n")
    else:
        print(f"CNF Encode: knf2cnf (sequential counter, linear AMO)")
        g.out_log_file.write(f"CNF Encode: knf2cnf (sequential counter, linear AMO)\n")

    knf2cnf()

    print("Starting (CNF) solver:", time.time() - g.start_time, "seconds")

    command = [g.CDCL_path, g.cnf_dimacs_filepath, "-t", str(g.solver_timeout), f"--seed={str(g.solver_seed)}"]
    #print(command)
    logFile = open(logFileN, 'w')
    
    satStart = time.time()
    result = subprocess.Popen(command, stdout=logFile, stderr=subprocess.STDOUT)
    result.wait()  

    satEnd = time.time()
    g.sat_time_wc = satEnd - satStart

    print("Finished SAT solver:", time.time() - g.start_time, "seconds")

    logFile.close() 

    if result.returncode == 10:
        print(f'SAT {g.sat_time_wc}s (wall)')
        g.out_log_file.write(f"SAT {g.sat_time_wc}s (wall)\n") # wall-clock time
        return result.returncode
    elif result.returncode == 20:
        print(f'UNSAT {g.sat_time_wc}s')
        g.out_log_file.write(f"UNSAT {g.sat_time_wc}s (wall)\n")
    else:
        print(f'Solver error: exit code {result.returncode}')
        g.out_log_file.write(f"Solver error: exit code {result.returncode}\n")
    return 0

def solveKNF():
    print("Starting (KNF) SAT solver:", time.time() - g.start_time, "seconds")

    command = [g.CCDCL_path, g.knf_dimacs_filepath, "-t", str(g.solver_timeout), f"--seed={str(g.solver_seed)}", "--ccdclMode=0"] 
    logFile = open(logFileN, 'w')
    
    satStart = time.time()
    result = subprocess.Popen(command, stdout=logFile, stderr=subprocess.STDOUT)
    result.wait()  

    satEnd = time.time()
    g.sat_time_wc = satEnd - satStart

    print("Finished SAT solver:", time.time() - g.start_time, "seconds") 

    logFile.close()  

    if result.returncode == 10:
        print(f'SAT {g.sat_time_wc}s')
        g.out_log_file.write(f"SAT {g.sat_time_wc}s (wall)\n")
        return result.returncode
    elif result.returncode == 20:
        print(f'UNSAT {g.sat_time_wc}s')
        g.out_log_file.write(f"UNSAT {g.sat_time_wc}s (wall)\n")
    else:
        print(f'Solver error: exit code {result.returncode}')
        g.out_log_file.write(f"Solver error: exit code {result.returncode}\n")
    return 0

def getCPUTime(): #UNSAT case
    import time
    
    with open(logFileN, 'r') as logFile:
        lines = logFile.readlines()

    solve_time = None
    for line in lines:
        if line.startswith('c total process time since initialization:'): # CPU time
            parts = line.strip().split()
            if len(parts) >= 2:
                solve_time = parts[-2]

    if solve_time is not None:
        g.out_log_file.write(f"CPU solve time: {solve_time} seconds\n")
        print(f'CPU Time: {solve_time} seconds')
        g.out_log_file.flush()

def extractModel():
    import time
    print("Extract Model:", time.time() - g.start_time, "seconds")
    
    with open(logFileN, 'r') as logFile:
        lines = logFile.readlines()

    model = []
    solve_time = None
    for line in lines:
        if line.startswith('v '):
            numbers = list(map(int, line[2:].strip().split()))
            model.extend(numbers)
        elif line.startswith('c total process time since initialization:'): # CPU time
            parts = line.strip().split()
            if len(parts) >= 2:
                solve_time = parts[-2]

    log_output = [f'Results n={g.n}, k={g.k} 0\n']
    g.point_list = []
    
    for x in range(g.n):
        for y in range(g.n):
            if y < g.n - x:
                if g.v[x][y] in model:
                    g.point_list.append((x, y))
                    if g.debug:
                        print(f'v[{x}][{y}]={g.v[x][y]}')
    
    with open(logFileN, 'a') as logFile:
        logFile.writelines(log_output)
    
    if solve_time is not None:
        g.out_log_file.write(f"CPU solve time: {solve_time} seconds\n")
        print(f'CPU Time: {solve_time} seconds')
        g.out_log_file.flush()