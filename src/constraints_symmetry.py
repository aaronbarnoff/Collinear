import math
from globals import g
dbg = 0

def lex_compare(seqA, seqB): # from knuth eq 169
    L = len(seqA)
    assert L == len(seqB), "string lengths must be equal"
    # Create L-1 lex variables
    lex_vars = [newVar() for _ in range(L-1)]

    # Base case at position 0:
    # (~A0 ∨ B0)
    if dbg: print(f"lex[0] clause: -{seqA[0]}, {seqB[0]}")
    addClause(-seqA[0], seqB[0])
    # (~A0 ∨ lex0)
    if dbg: print(f"lex[0] clause: -{seqA[0]}, {lex_vars[0]}")
    addClause(-seqA[0], lex_vars[0])
    # (B0 ∨ lex0)
    if dbg: print(f"lex[0] clause: {seqB[0]}, {lex_vars[0]}")
    addClause(seqB[0],  lex_vars[0])
    # (lex0)
    if dbg: print(f"lex[0] clause: {lex_vars[0]}")
    addClause(lex_vars[0])

    # Recurrence for positions 1..L-2:
    for i in range(1, L-1):
        a = seqA[i]
        b = seqB[i]
        prev = lex_vars[i-1]
        curr = lex_vars[i]
        # (~Ai ∨ Bi ∨ ~prev)
        if dbg: print(f"lex[{i}] clause: -{a}, {b}, -{prev}")
        addClause(-a, b,     -prev)
        # (~Ai ∨ curr ∨ ~prev)
        if dbg: print(f"lex[{i}] clause: -{a}, {curr}, -{prev}")
        addClause(-a, curr,  -prev)
        # (Bi ∨ curr ∨ ~prev)
        if dbg: print(f"lex[{i}] clause: {b}, {curr}, -{prev}")
        addClause(b,  curr,  -prev)

    # Final boundary at position L-1:
    a_last = seqA[L-1]
    b_last = seqB[L-1]
    prev   = lex_vars[L-2]
    # (~A_last ∨ B_last ∨ ~prev)
    if dbg: print(f"lex[final] clause: -{a_last}, {b_last}, -{prev}")
    addClause(-a_last, b_last, -prev)

    return lex_vars


def createLexEncoding(numPoints):
    n  = g.n
    NP = min(numPoints, n//2)   # only need floor(n/2) to avoid midpoint overlap

    for i in range(n):
        g.rightStep[i] = newVar()

    cells_per_step = [[] for _ in range(n)]
    for x in range(n):
        for y in range(n):
            step = x + y
            if step < n:
                cells_per_step[step].append((x, y))

    for i in range(1, n):
        for x, y in cells_per_step[i]:
            if x > 0:
                if dbg: print(f"step[{i}] RIGHT clause: -v[{x-1}][{y}], -v[{x}][{y}], r[{i}]")
                addClause(-g.v[x-1][y], -g.v[x][y],  g.rightStep[i])
                if dbg: print(f"step[{i}] RIGHT clause: -r[{i}], -v[{x}][{y}], v[{x-1}][{y}]")
                addClause(-g.rightStep[i],   -g.v[x][y],   g.v[x-1][y])
            if y > 0:
                if dbg: print(f"step[{i}] UP clause: -v[{x}][{y-1}], -v[{x}][{y}], -r[{i}]")
                addClause(-g.v[x][y-1], -g.v[x][y], -g.rightStep[i])
                if dbg: print(f"step[{i}] UP clause: r[{i}], -v[{x}][{y}], v[{x}][{y-1}]")
                addClause( g.rightStep[i],  -g.v[x][y],   g.v[x][y-1])

    # Rotation
    i_indices = list(range(0, NP))
    j_indices = [n - 1 - i for i in i_indices]
    seqA = [g.rightStep[i] for i in i_indices]
    seqB = [g.rightStep[j] for j in j_indices]

    if dbg: print(f"LEX reverse compare indices A{ i_indices } = {seqA}  vs B{ j_indices } = {seqB}")
    lex_vars = lex_compare(seqA, seqB)
    for k, lv in enumerate(lex_vars):
        g.lexVar[k] = lv
        if dbg: print(f"lexVar[{k}] = {lv}")

   # Rotation+Reflection
    rot_seq = []
    for i in i_indices:
        rev = (n - 1) - i
        rot_seq.append(-g.rightStep[rev])
    if dbg: print(f"LEX rot compare seqA={seqA}  vs rot_seq={rot_seq}")
    rot_lex_vars = lex_compare(seqA, rot_seq)
    g.rotLexVars = rot_lex_vars
    for k, rv in enumerate(rot_lex_vars):
        if dbg: print(f"rotLexVar[{k}] = {rv}")


def addClauseList(strList):
    tmpStr = []
    strList.append(0)
    clauseStr = ''.join(tmpStr)
    g.num_clauses += 1
    g.dimacs_buffer.append(clauseStr)
    if g.debug:
        print(clauseStr)


def addClause(*literals):
    res = toClause(literals)
    g.dimacs_buffer.append(res)
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
    g.num_clauses += 1
    return clauseStr


def newVar():
    g.num_vars += 1
    return g.num_vars