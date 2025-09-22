import math
import time
from globals import g


def defineVars():
    # Define vars diagonally: 
    for b in range(g.n):
        for x in range(g.n):
            for y in range(g.n): # remove
                if y == b - x:
                    g.v[x][y] = newVar()
                    g.var_cnt += 1
            if g.debug:
                print(f"v[{x}][{y}]={g.v[x][y]}")

# These constraints below don't account for symmetry break; only a unit clause is given

def stepConstraint(): 
    addClause(g.v[0][0]) # The origin is always on the path

    # print("Step Constriants:", time.time() - start_time, "seconds")
    # Step constraint 1a
    for x in range(0, g.n):
        for y in range(0, g.n):
            if y < g.n - x - 1:
                # v(x, y) --> v(x + 1, y) or v(x, y + 1)
                addClause(-g.v[x][y], g.v[x + 1][y], g.v[x][y + 1])
                # ~[v(x + 1, y) and v(x, y + 1)]
                addClause(-g.v[x + 1][y], -g.v[x][y + 1])

    # Step constraint 1b
    for x in range(0, g.n): 
        for y in range(0, g.n):
            # v(x, y) --> v(x - 1, y) or v(x, y - 1)
            if x > 0 and y == 0:
                addClause(-g.v[x][y], g.v[x - 1][y])
            elif x == 0 and y > 0:
                addClause(-g.v[x][y], g.v[x][y - 1])
            elif x > 0 and y > 0:
                if y < g.n - x:
                    addClause(-g.v[x][y], g.v[x - 1][y], g.v[x][y - 1])
                    # ~[v(x - 1, y) and v(x, y - 1)]
                    addClause(-g.v[x - 1][y], -g.v[x][y - 1])


def cardinalityConstraint():
    if g.vh_card:
        print("* VHCard True")
        g.out_log_file.write("* VHCard True")

        # At most k constraint: vertical lines
        # print("AMK Vertical Constraints:", time.time() - start_time, "seconds")
        for x in range(0, g.n):
            tmpStr = []
            cnt = 0
            for y in range(0, g.n):
                if y < g.n - x:
                    tmpStr.append(str(-g.v[x][y]))
                    tmpStr.append(" ")
                    cnt = cnt + 1
                else:
                    break
            if len(tmpStr) > 0 and cnt >= g.k:
                clauseStr = f'k {cnt - g.k + 1} {"".join(tmpStr)} 0'
                g.num_clauses += 1
                g.dimacs_buffer.append(clauseStr)
                # print(clauseStr)

        # At most k constraint: horizontal lines
        # print("AMK Horizontal Constraints:", time.time() - start_time, "seconds")
        for y in range(0, g.n):
            tmpStr = []
            cnt = 0
            for x in range(0, g.n):
                if x < g.n - y:
                    tmpStr.append(str(-g.v[x][y]))
                    tmpStr.append(" ")
                    cnt = cnt + 1
                else:
                    break
            if len(tmpStr) > 0 and cnt >= g.k:
                clauseStr = f'k {cnt - g.k + 1} {"".join(tmpStr)} 0'
                g.num_clauses += 1
                g.dimacs_buffer.append(clauseStr)
                # print(clauseStr)
    else:
        print("* VHCard False")
        g.out_log_file.write("* VHCard False")

    # At most k constraint: slope line
    decN = g.n - 1
    decNcnt = decN

    """
    I have removed floating point arithmetic to fix the precision/rounding problem; all division involving slope=m_p/m_q and b=b_p/b_q is removed.
    Still need to do a rigorous test to make sure it's working correctly.
    """

    #print("Slope Constraints:", time.time() - g.start_time, "seconds")
    for m_p in range(0, g.n):
        m_q = 1
        while m_q <= decN: #decN is max value of m_q that was found in previous m_p loop iteration that had a line with #points >= k
            if (m_p == 0 and m_q != 1) or (math.gcd(m_p, m_q) > 1):
                m_q += 1
                continue
            if (m_p * g.k) < m_q: 
                break
            if m_p > (g.k * m_q): # slope > k should be caught by the horizontal/vertical lines
                m_q += 1
                continue
            for b_q in range(1, m_q+1): # lowest slopes: y = (m_p/m_q)*x - (b_p=m_p/b_q=m_q)*n; highest slopes: y = (m_p/m_q)x + n
                for b_p in range(-int(m_p*g.n), int(b_q*g.n)+1): # was missing b_p = 315, b_q = 5 for y=1/5x+312/5 for k=7, n=261    
                    if (b_p == 0 and b_q != 1) or (math.gcd(b_p, b_q) > 1) or m_q % b_q != 0:
                        # b_q always divisor of m_q for numPoints >= k?
                        continue
                    if abs(b_p) > (g.n * b_q): 
                        continue   
                    tmpStr = []
                    #tmpStr2 = []  # For debugging the cardinality constraint lines
                    cnt = 0
                    x = 0
                    flag = 0
                    denominator = m_q*b_q
                    while x < g.n:
                        # first point should be within first n/k x values
                        numerator = m_p*x*b_q + b_p*m_q #y is integer iff (m_p*x*b_q + b_p*m_q) % (m_q*b_q) = 0
                        y1 = numerator//denominator
                        if y1 > g.n: 
                            break
                        if numerator % denominator != 0: 
                            x += 1
                            continue
                        else:
                            y=y1
                            flag = 1
                            break
                    if flag:
                        # once first point is found, include all the rest by adding m_p and m_q
                        while x < g.n:
                            if int(y) >= 0:
                                if int(y) < g.n - x:
                                    tmpStr.append(str(-g.v[x][int(y)]))
                                    tmpStr.append(" ")
                                    #tmpStr2.append(f"({x},{int(y)})")
                                    cnt += 1
                                    
                                    if cnt >= g.k and m_p != 0: # only looking for k or more points
                                        decNcnt = m_q # largest value of m_q always seems to be the last point found where #points >=k
                                        #print(f"tmpCnt: {cnt}, m_p: {m_p}, m_q: {m_q}, decN: {decN}, slope: {slope}, b_p: {b_p}, b_q: {b_q}, b: {b}, x: {x}, y: {int(y)}, yf: {y}")
                                else:
                                    break
                            x += m_q
                            y += m_p
                    if len(tmpStr) > 0 and cnt >= g.k:
                        clauseStr = f'k {cnt - g.k + 1} {"".join(tmpStr)}0'
                        g.num_clauses += 1
                        g.dimacs_buffer.append(clauseStr)
                        g.num_card_clauses +=1
                        #if f"(77,43)" in tmpStr2 and f"(71,39)" in tmpStr2:
                        #tmpStr3 = "".join(", ".join(tmpStr2))
                        #g.logFile2.write(tmpStr3)
                        #g.logFile2.write("\n")
            m_q += 1
            if decNcnt + 2 < g.n:
                decN = decNcnt + 2



def addClauseList(strList, debug=False):
    tmpStr = []
    strList.append(0)
    clauseStr = ''.join(tmpStr)
    g.num_clauses += 1
    g.dimacs_buffer.append(clauseStr)
    if debug:
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