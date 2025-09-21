import time

from globals import g
from constraints_main import defineVars, stepConstraint, cardinalityConstraint
from constraints_reachability import BUP_SolverFoundPoints, BUP_EachPoint_VHLine, BUP_EachPoint_NegDiagonalLine
from constraints_symmetry import createLexEncoding
from solve_normal import solveNormal
import re


def main():
    g.logFile2 = open(f'{g.logFilePath2}', 'w+', buffering=1)
    g.start_time = time.time()
    print(g.outputPath)

    # Main Constraints #
    defineVars()
    stepConstraint()
    cardinalityConstraint()
    """
    #Problem: Got SAT for k7_n149_x101_y47_s1_c0_v1_a0_l0_b2.0_f1_s12_2025-09-13_04-11-56, but failed collinearity check for: (20,5) (23,7) (29,11) (47,23) (62,33) (71,39) (77,43)
    addClause(g.v[77][43])
    addClause(g.v[71][39])
    addClause(g.v[62][33])
    addClause(g.v[47][23])
    addClause(g.v[29][11])
    addClause(g.v[23][7])
    addClause(g.v[20][5])
    """
    print("Config:")
    g.logFile2.write("Config:\n")
    if g.useKNF:
        print("     +Solver: KNF")
        g.logFile2.write("     +Solver: KNF\n")
    else:
        print("     +Solver: CNF")
        g.logFile2.write("     +Solver: CNF\n")

    if g.solverTimeout > 0:
        print(f"     +Solver Timeout: {g.solverTimeout}s")
        g.logFile2.write(f"     +Solver Timeout: {g.solverTimeout}s\n")

    if g.symBreak:
        if g.n > 1:
            print("     +(0,1) Symmetry Break On")
            g.logFile2.write("     +(0,1) Symmetry Break On\n")
            addClause(g.v[0][1])                       
    else:
        print("     +(0,1) Symmetry Break Off")
        g.logFile2.write("     +(0,1) Symmetry Break Off\n")

    if (g.px > 0 and g.py > 0):
        print(f"     +Solving for point ({g.px},{g.py})")
        g.logFile2.write(f"     +Solving for point ({g.px},{g.py})\n")
        addClause(g.v[g.px][g.py])
    else:
        print("     +Solving for any point")
        g.logFile2.write("     +Solving for any point\n")

    if g.vhLine:
        print(f"     +V/H Line Binary Clauses On: LineLen={g.lineLen}")
        g.logFile2.write(f"    +V/H Line Binary Clauses On: LineLen={g.lineLen}\n")
        BUP_EachPoint_VHLine(g.lineLen)         
    else:
        print("     +V/H Line Binary Clauses Off")
        g.logFile2.write("     +V/H Line Binary Clauses Off\n")

    if g.negDiag:
        print(f"     +Antidiagonal On: LineLen={g.lineLen}")
        g.logFile2.write(f"     +Antidiagonal On: LineLen={g.lineLen}\n")
        BUP_EachPoint_NegDiagonalLine(g.lineLen)  
    else:
        print("     +Antidiagonal Off")
        g.logFile2.write("     +Antidiagonal Off\n")
    
    if g.diff > 0.0000000:
        print(f"     +BoundaryPoints On: {g.diff}% coverage")
        g.logFile2.write(f"     +BoundaryPoints On: {g.diff}% coverage\n")
        BUP_SolverFoundPoints()
    else:
        print("     +BoundaryPoints Off")
        g.logFile2.write(f"     +BoundaryPoints Off\n")

    g.logFile2.write(f"numVars: {g.vCnt}, numClauses: {g.numClauses}, numCardClauses: {g.numCardClauses}\n")

    #  Write KNF Dimacs File #
    #print("Writing KNF file:", time.time() - g.start_time, "seconds")

    f = open(f'{g.outputPath}/{g.knfDimacsFileName}', "w+")
    f.write(f"p knf {g.numVars} {g.numClauses}\n")
    for lines in g.dimacsBuffer:
        f.write(lines + "\n")
    f.flush()
    f.close()

    # Solve and Verify #
    solveNormal()
    g.logFile2.close()

    # Done
    print("Done:", time.time() - g.start_time, "seconds")

def addClauseList(strList):
    tmpStr = []
    strList.append(0)
    clauseStr = ''.join(tmpStr)
    g.numClauses += 1
    g.dimacsBuffer.append(clauseStr)
    if g.debug:
        print(clauseStr)


def addClause(*literals):
    res = toClause(literals)
    g.dimacsBuffer.append(res)
    if g.debug:
        print(res)


def toClause(*literals):
    tmpStr = []
    for lit in literals:
        for i in lit:
            tmpStr.append(str(i))
            tmpStr.append(" ")
    tmpStr.append("0")
    clauseStr = ''.join(tmpStr)
    g.numClauses += 1
    return clauseStr


def newVar():
    g.numVars += 1
    return g.numVars

if __name__ == "__main__":
    main()
