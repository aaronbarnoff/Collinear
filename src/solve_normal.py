import time
import subprocess

from globals import g, checkCollinearK, knf2cnf

logFileN = f'{g.outputPath}/{g.logFileName}'

def solveNormal():
    if g.useKNF == 1: 
        res = solveKNF()
    else:
        res = solveCNF()
    if res:
        extractModel()
        checkCollinearK(g.pointList)
    else:
        getCPUTime() # unsat

def solveCNF():
    if g.cnfEncodingType is not None:
        print(f"CNF Encode: {g.cnfEncodingType}")
        g.logFile2.write(f"CNF Encode: {g.cnfEncodingType}\n")
    else:
        print(f"CNF Encode: knf2cnf (sequential counter, linear AMO)")
        g.logFile2.write(f"CNF Encode: knf2cnf (sequential counter, linear AMO)\n")

    knf2cnf()

    print("Starting (CNF) solver:", time.time() - g.start_time, "seconds")

    command = [g.cadcnf_path, g.cnfDimacsFilePath, "-t", str(g.solverTimeout), f"--seed={str(g.solverSeed)}"]
    #print(command)
    logFile = open(logFileN, 'w')
    
    satStart = time.time()
    result = subprocess.Popen(command, stdout=logFile, stderr=subprocess.STDOUT)
    result.wait()  

    satEnd = time.time()
    g.satTime = satEnd - satStart

    print("Finished SAT solver:", time.time() - g.start_time, "seconds")

    logFile.close() 

    if result.returncode == 10:
        print(f'SAT {g.satTime}s (wall)')
        g.logFile2.write(f"SAT {g.satTime}s (wall)\n") # wall-clock time
        return result.returncode
    elif result.returncode == 20:
        print(f'UNSAT {g.satTime}s')
        g.logFile2.write(f"UNSAT {g.satTime}s (wall)\n")
    else:
        print(f'Solver error: exit code {result.returncode}')
        g.logFile2.write(f"Solver error: exit code {result.returncode}\n")
    return 0

def solveKNF():
    print("Starting (KNF) SAT solver:", time.time() - g.start_time, "seconds")

    command = [g.cadknf_path, g.knfDimacsFilePath, "-t", str(g.solverTimeout), f"--seed={str(g.solverSeed)}", "--ccdclMode=0"] 
    logFile = open(logFileN, 'w')
    
    satStart = time.time()
    result = subprocess.Popen(command, stdout=logFile, stderr=subprocess.STDOUT)
    result.wait()  

    satEnd = time.time()
    g.satTime = satEnd - satStart

    print("Finished SAT solver:", time.time() - g.start_time, "seconds") 

    logFile.close()  

    if result.returncode == 10:
        print(f'SAT {g.satTime}s')
        g.logFile2.write(f"SAT {g.satTime}s (wall)\n")
        return result.returncode
    elif result.returncode == 20:
        print(f'UNSAT {g.satTime}s')
        g.logFile2.write(f"UNSAT {g.satTime}s (wall)\n")
    else:
        print(f'Solver error: exit code {result.returncode}')
        g.logFile2.write(f"Solver error: exit code {result.returncode}\n")
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
        g.logFile2.write(f"CPU solve time: {solve_time} seconds\n")
        print(f'CPU Time: {solve_time} seconds')
        g.logFile2.flush()

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
    g.pointList = []
    
    for x in range(g.n):
        for y in range(g.n):
            if y < g.n - x:
                if g.v[x][y] in model:
                    g.pointList.append((x, y))
                    if g.debug:
                        print(f'v[{x}][{y}]={g.v[x][y]}')
    
    with open(logFileN, 'a') as logFile:
        logFile.writelines(log_output)
    
    if solve_time is not None:
        g.logFile2.write(f"CPU solve time: {solve_time} seconds\n")
        print(f'CPU Time: {solve_time} seconds')
        g.logFile2.flush()