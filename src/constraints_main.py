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
                    g.vCnt += 1
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
    if g.vhCard:
        print("* VHCard True")
        g.logFile2.write("* VHCard True")

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
                g.numClauses += 1
                g.dimacsBuffer.append(clauseStr)
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
                g.numClauses += 1
                g.dimacsBuffer.append(clauseStr)
                # print(clauseStr)
    else:
        print("* VHCard False")
        g.logFile2.write("* VHCard False")

    # At most k constraint: slope line
    decN = g.n - 1
    decNcnt = decN
    tolerance = 1e-14 # is_integer() is failing to identify (3/22)*21 + 3/22 as 3 (2.9999999999999996) due to fp precision
    #print("Slope Constraints:", time.time() - g.start_time, "seconds")
    for m_p in range(0, g.n):
        m_q = 1
        while m_q <= decN: #decN is max value of m_q that was found in previous m_p loop iteration that had a line with #points >= k
            if (m_p == 0 and m_q != 1) or (math.gcd(m_p, m_q) > 1):
                m_q += 1
                continue
            slope = m_p / m_q
            if (slope < 1/g.k): 
                break
            if (slope > g.k): # slope > k should be caught by the horizontal/vertical lines
                m_q += 1
                continue
            for b_q in range(1, m_q+1): # lowest slopes: y = (m_p/m_q)*x - (b_p=m_p/b_q=m_q)*n; highest slopes: y = (m_p/m_q)x + n
                for b_p in range(-int(m_p*g.n), int(b_q*g.n)+1): # was missing b_p = 315, b_q = 5 for y=1/5x+312/5 for k=7, n=261    
                    if (b_p == 0 and b_q != 1) or (math.gcd(b_p, b_q) > 1) or m_q % b_q != 0:
                        # b_q always divisor of m_q for numPoints >= k?
                        continue
                    b = b_p / b_q
                    if (int(b) > g.n or -int(b) < -g.n):
                        continue
                    tmpStr = []
                    cnt = 0
                    x = 0
                    flag = 0
                    while x < g.n:
                        # first point should be within first n/k x values
                        y = slope * x + b
                        if int(y) > g.n:
                            break
                        if not (abs(y - round(y)) < tolerance):
                            x += 1
                            continue
                        else:
                            flag = 1
                            break
                    if flag:
                        # once first point is found, include all the rest by adding m_p and m_q
                        while x < g.n:
                            if int(y) >= 0:
                                if int(y) < g.n - x:
                                    tmpStr.append(str(-g.v[x][int(y)]))
                                    tmpStr.append(" ")
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
                        g.numClauses += 1
                        g.dimacsBuffer.append(clauseStr)
                        g.numCardClauses +=1
            m_q += 1
            if decNcnt + 2 < g.n:
                decN = decNcnt + 2



def addClauseList(strList, debug=False):
    tmpStr = []
    strList.append(0)
    clauseStr = ''.join(tmpStr)
    g.numClauses += 1
    g.dimacsBuffer.append(clauseStr)
    if debug:
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