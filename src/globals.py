import time
import os
import subprocess
from datetime import datetime
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="e.g. for k=7, n=122, point (33, 88): python main.py -k 7 -n 122 -x 33 -y 88 -s 1 -c 0 -v 1 -a 0 -l -0 -b 0 -f 0 -t 0 -r 0")
    parser.add_argument("-k", default=5, help="number of collinear points to avoid")
    parser.add_argument("-n", default=28, help="n points; n-1 steps")
    
    parser.add_argument("-x", default=0, help="point x")
    parser.add_argument("-y", default=0, help="point y")

    parser.add_argument("-s", default=1, help="symmetry break [0=off, 1=on]")
    parser.add_argument("-c", default=0, help="v/h cardinality constraints [0=off, 1=on]")
    parser.add_argument("-v", default=1, help="v/h line binary clauses [0=off, 1=on]")
    parser.add_argument("-a", default=0, help="antidiagonal cardinality constraints [0=off, 1=on]")

    parser.add_argument("-l", default=0, help="line length for vhline and antidiagonal. 0=1 point, 5=6 points")

    parser.add_argument("-b", default=0, help="boundary constraints [0=off, 1=unit clauses, 2=unit+binary clauses]") # at one point this was used as float value, haven't changed
    parser.add_argument("-f", default=0, help="0=CNF (cadical), 1=KNF (card. cadical)")
    parser.add_argument("-t", default=0, help="sat solver wall-clock timeout (s)")

    parser.add_argument("-e", default=None, help="CNF cardinality encoding type: seqcounter, totalizer, sortnetwrk, cardnetwrk, mtotalizer, kmtotalizer")

    parser.add_argument("-r", default=0, help="SAT solver seed")
    return vars(parser.parse_args())

class Globals:
    def __init__(self):
        args = parse_arguments()
        self.k=int(args["k"])
        self.n=int(args["n"])

        self.lineLen=int(args["l"])
        self.vhCard=int(args["c"])
        self.vhLine=int(args["v"])
        self.negDiag=int(args["a"])

        self.px=int(args["x"])
        self.py=int(args["y"])
        self.symBreak=int(args["s"])
        self.diff=float(args["b"])
        self.useKNF=int(args["f"])

        self.cnfEncodingType=(args["e"])

        self.solverTimeout=int(args["t"])
        self.solverSeed=int(args["r"])
        
        if self.cnfEncodingType is not None and self.useKNF:
            print("Must use CNF solver with encoding type.")
            exit(-1)

        self.solvePt = False
        if self.px >0 and self.py > 0:
            if self.px + self.py >= self.n:
                print("Invalid final point to solve for.")
                exit(-1)
            else:
                self.solvePt = True    

        if self.vhLine == 0 and self.vhCard == 0:
            print("Vertical/horizontal constraints required.")
            exit(-1)

        self.runID = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.cwd=os.getcwd()

        self.v = [[0 for _ in range(self.n)] for _ in range(self.n)]
        self.pointList = []
        self.collinearList = []
        self.dimacsBuffer = []
        self.numSolutions = 0
        self.numVars = 0
        self.vCnt = 0
        self.numClauses = 0
        self.debug = 0
        self.numCardClauses = 0

        self.satTime = 0
        self.start_time = 0
        self.end_time = 0

        self.mainPath = os.path.dirname(os.getcwd())
        self.outputFolderPath = os.path.join(self.mainPath, 'output')
        if not os.path.exists(self.outputFolderPath):
            os.makedirs(self.outputFolderPath)

        self.outputPath = os.path.join(self.outputFolderPath, f'res_k{self.k}_n{self.n}_x{self.px}_y{self.py}_s{self.symBreak}_c{self.vhCard}_v{self.vhLine}_a{self.negDiag}_l{self.lineLen}_b{self.diff}_f{self.useKNF}_r{self.solverSeed}_e{self.cnfEncodingType}_{self.runID}')
        
        #print(self.outputPath)
        if not os.path.exists(self.outputPath):
            os.makedirs(self.outputPath)

        self.knfDimacsFileName = f'dimacsFile.knf'
        self.knfDimacsFilePath = f'{self.outputPath}/{self.knfDimacsFileName}'

        self.cnfDimacsFileName = f'dimacsFile.cnf'
        self.cnfDimacsFilePath = f'{self.outputPath}/{self.cnfDimacsFileName}'

        self.logFileName = f'satOutput_k.log'
        self.logFilePath = f'{self.outputPath}/{self.logFileName}'
        self.logFile = None

        self.logFileName2 = f'logOutput_k.log'
        self.logFilePath2 = f'{self.outputPath}/{self.logFileName2}'
        #self.logFile2 = None
        self.logFile2 = open(f'{self.logFilePath2}', 'w+', buffering=1)

        self.pysatEncodePath= f'{self.mainPath}/solvers/Cardinality-CDCL-main/Tools/pysat_encode.py'
        self.knf2cnfPath = f'{self.mainPath}/solvers/Cardinality-CDCL-main/Tools/knf2cnf'
        self.cadknf_path = f'{self.mainPath}/solvers/Cardinality-CDCL-main/cardinality-cadical/build/cadical'
        self.cadcnf_path = f'{self.mainPath}/solvers/cadical-master/build/cadical'

g = Globals()

def checkCollinearK(pointList):
    print("Confirming Results:", time.time() - g.start_time, "seconds")
    for (x1, y1) in pointList:
        for (x2, y2) in pointList:
            if (x1, y1) == (x2, y2):
                continue
            if (x2 < x1) or (y2 < y1):
                continue
            m_p = x2-x1
            m_q = y2-y1
            tmpPointsList = []
            count = 2
            tmpPointsList.append((x1,y1))
            tmpPointsList.append((x2,y2))

            #print(f'({x1},{y1}), ({x2}, {y2}); slope: {m_p}/{m_q} = {m_p/m_q}')
            x = x2
            y = y2
            while (x < g.n) and (y < g.n - x):
                x += m_p
                y += m_q
                if (x, y) in pointList:
                    count += 1
                    tmpPointsList.append((x, y))
            if count >= g.k:
                # print(tmpPointsList)
                g.collinearList.append(tmpPointsList)    

    if g.collinearList:
        print(f"Failure: {g.k} or more points found on the same line.")
        for line in g.collinearList:
            (x1, y1)= line[0]
            (x2, y2)= line[1]
            if (x2 - x1) == 0:
                print('vline. points: ', end="")
            elif (y2 - y1) == 0:
                print('hline. points: ', end="")
            else:
                print(f'slope: {((y2 - y1) / (x2 - x1)):.2g}; m_p: {(y2-y1)}, m_q: {(x2-x1)}; points: ',end="")
            for points in line:
                (x, y)=points
                print(f'({x},{y}) ', end="")
            print("")

def knf2cnf():
    print("Converting to CNF file:", time.time() - g.start_time, "seconds")

    cnfOutputFile = open(g.cnfDimacsFilePath, 'w+')

    if g.cnfEncodingType is None:
        command = f'\'{g.knf2cnfPath}\' \'{g.knfDimacsFilePath}\''
        result = subprocess.Popen(command, shell=True, stdout=cnfOutputFile, stderr=subprocess.PIPE, text=True)
        result.wait()
    else:
        command = ["python3", g.pysatEncodePath, "-k", g.knfDimacsFilePath, "-c", g.cnfDimacsFilePath, "-e", g.cnfEncodingType] # requires python-sat module
        #print(command)
        result = subprocess.Popen(command, stdout=g.logFile2, stderr=subprocess.STDOUT)
        result.wait()


    cnfOutputFile.close()
    time.sleep(1) # Seems to cause problems without