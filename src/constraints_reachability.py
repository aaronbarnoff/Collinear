from globals import g
import re
import math

def BUP_SolverFoundPoints():

    points_stringk7upSymmetric = """
   (0,6),(1,11),(2,16),(3,21),(4,26),(5,31),(6,0),(6,30),
   (7,33),(8,37),(9,41),(10,44),(11,1),(11,45),(12,47),(13,49),
   (14,52),(15,55),(16,2),(16,58),(17,60),(18,63),(19,65),(20,67),
   (21,3),(21,69),(22,70),(23,71),(24,73),(25,75),(26,4),(26,78),
   (27,80),(28,82),(29,83),(30,6),(30,86),(31,5),(31,86),(32,88),
   (33,7),(33,88),(34,89),(35,91),(36,92),(37,8),(37,91),(38,90),
   (39,91),(40,93),(41,9),(41,95),(42,97),(43,99),(44,10),(44,101),
   (45,11),(45,102),(46,104),(47,12),(47,106),(48,108),(49,13),(49,109),
   (50,111),(51,113),(52,14),(52,115),(53,117),(54,119),(55,15),(55,121),
   (56,123),(57,125),(58,16),(58,126),(59,128),(60,17),(60,130),(61,131),
   (62,133),(63,18),(63,135),(64,136),(65,19),(65,138),(66,140),(67,20),
   (67,141),(68,143),(69,21),(69,144),(70,22),(70,146),(71,23),(71,148),
   (72,149),(73,24),(73,151),(74,153),(75,25),(75,155),(76,156),(77,156),
   (78,26),(78,157),(79,156),(80,27),(80,158),(81,159),(82,28),(82,162),
   (83,29),(83,163),(84,165),(85,166),(86,30),(86,31),(86,167),(87,168),
   (88,32),(88,33),(88,170),(89,34),(89,171),(90,38),(91,35),(91,37),
   (91,39),(92,36),(93,40),(95,41),(97,42),(99,43),(101,44),(102,45),
   (104,46),(106,47),(108,48),(109,49),(111,50),(113,51),(115,52),(117,53),
   (119,54),(121,55),(123,56),(125,57),(126,58),(128,59),(130,60),(131,61),
   (133,62),(135,63),(136,64),(138,65),(140,66),(141,67),(143,68),(144,69),
   (146,70),(148,71),(149,72),(151,73),(153,74),(155,75),(156,76),(156,77),
   (156,79),(157,78),(158,80),(159,81),(162,82),(163,83),(165,84),(166,85),
   (167,86),(168,87),(170,88),(171,89)"""

    points_stringk7upperBounds = """
    (0,6),(1,11),(2,16),(3,21),(4,26),(5,31),(6,30),(7,33),(8,37),
    (9,41),(10,44),(11,45),(12,47),(13,49),(14,52),(15,55),(16,58),
    (17,60),(18,63),(19,65),(20,67),(21,69),(22,70),(23,71),(24,73),
    (25,75),(26,78),(27,80),(28,82),(29,83),(30,86),(31,86),(32,88),
    (33,88),(34,89),(35,91),(36,92),(37,91),(38,90),(39,91),(40,93),
    (41,95),(42,97),(43,99),(44,101),(45,102),(46,104),(47,106),(48,108),
    (49,109),(50,111),(51,113),(52,115),(53,117),(54,119),(55,121),(56,123),
    (57,125),(58,126),(59,128),(60,130),(61,131),(62,133),(63,135),(64,136),
    (65,138),(66,140),(67,141),(68,143),(69,144),(70,146),(71,148),(72,149),
    (73,151),(74,153),(75,155),(76,156),(77,156),(78,157),(79,156),(80,158),
    (81,159),(82,162),(83,163),(84,165),(85,166),(86,167),(87,168),(88,170),
    (89,171)"""
    points_stringk7lowerBounds = """
    (1,0),(6,1),(11,2),(16,3),(21,4),(26,5),(30,6),(30,7),
    (33,8),(37,9),(41,10),(43,11),(45,12),(45,13),(48,14),
    (51,15),(54,16),(57,17),(59,18),(62,19),(64,20),(66,21),
    (67,22),(69,23),(71,24),(73,25),(75,26),(78,27),(79,28),
    (82,29),(83,30),(86,31),(86,32),(88,33),(88,34),(89,35),
    (89,38),(89,39),(90,36),(90,37),(90,40),(92,41),(94,42),
    (96,43),(98,44),(100,45),(102,46),(104,47),(105,48),(107,49),
    (109,50),(111,51),(112,52),(115,53),(116,54),(118,55),(120,56),
    (122,57),(124,58),(126,59),(127,60),(129,61),(131,62),(132,63),
    (134,64),(136,65),(137,66),(139,67),(141,68),(142,69),(144,70),
    (145,71),(147,72),(149,73),(151,74),(153,75),(154,76),(154,77),
    (155,78),(156,79),(156,80),(158,81),(159,82),(160,83),(162,84),
    (165,85),(165,86),(166,87),(168,88),(169,89),(171,90),(172,91),
    (174,92)"""
    
    # k6 bounds don't include internal boundary points
    points_stringk6upperbounds = """
    (0,5),(1,9),(2,13),(3,17),(4,21),(5,20),(6,22),(7,24),
    (8,26),(9,28),(10,29),(11,29),(12,31),(13,33),(14,35),
    (15,36),(16,38),(17,39),(18,41),(19,41),(20,42),(21,43),
    (22,45),(23,46),(24,48),(25,49),(26,51),(27,53),(28,55),
    (29,56),(30,57),(31,55),(32,57),(33,57),(34,59),(35,59),
    (36,57),(37,58),(38,58),(39,57)
    """

    points_stringk6lowerbounds= """
    (1,0),(5,1),(9,2),(13,3),(17,4),(20,5),(20,6),(22,7),
    (24,8),(26,9),(27,10),(27,11),(28,12),(30,13),(32,14),
    (34,15),(36,16),(37,17),(38,18),(39,19),(40,20),(41,21),
    (42,22),(44,23),(45,24),(47,25),(49,26),(51,27),(52,28),
    (54,29),(55,30),(55,31),(55,32),(56,33),(56,34),(59,35),
    (57,36),(57,37),(57,38),(57,39),(58,36),
    """

    points_stringk6n97fp = """
    (0,5),(1,9),(2,13),(3,17),(4,21),(5,20),(6,22),(7,24),
    (8,26),(9,28),(10,29),(11,29),(12,31),(13,33),(14,35),
    (15,36),(16,38),(17,39),(18,41),(19,41),(20,42),(21,43),
    (22,45),(23,46),(24,48),(25,49),(26,51),(27,53),(28,55),
    (29,56),(30,57),(31,55),(32,57),(33,57),(34,59),(35,59),
    (36,57),(37,58),(38,58),(39,57),(5,0),(9,1),(13,2),(17,3),
    (20,5),(21,4),(22,6),(24,7),(26,8),(28,9),(29,10),(29,11),
    (31,12),(33,13),(35,14),(36,15),(38,16),(39,17),(41,18),(41,19),
    (42,20),(43,21),(45,22),(46,23),(48,24),(49,25),(51,26),(53,27),
    (55,28),(55,31),(56,29),(57,30),(57,32),(57,33),(57,36),(57,39),
    (58,37),(58,38),(59,34),(59,35),
    """

    pts = None
    symPts = None
    upPts = None
    downPts = None

    if g.k == 7:
        symPts  = re.findall(r'\((\d+),\s*(\d+)\)', points_stringk7upSymmetric)
        upPts   = re.findall(r'\((\d+),\s*(\d+)\)', points_stringk7upperBounds)
        downPts = re.findall(r'\((\d+),\s*(\d+)\)', points_stringk7lowerBounds)

        for x in range(g.n):
            for y in range(g.n):
                if x == 0 and y == 0: #block all unreachable from (0,0)
                    for x_str,y_str in upPts: # upper bound
                        x2,y2 = int(x_str), int(y_str)                          
                        if x+x2 < g.n and y+y2 < g.n and y+y2 < g.n - (x+x2) and x2 + y2 + 1 < g.n:
                            addClause(-g.v[x+x2][y+y2]) 
                    for x_str,y_str in downPts: # lower bound
                        x2,y2 = int(x_str), int(y_str)                          
                        if x+x2 < g.n and y+y2 < g.n and y+y2 < g.n - (x+x2) and x2 + y2 + 1 < g.n:
                            addClause(-g.v[x+x2][y+y2])
                else: #block unreachable from (x,y) within some distance of it
                    if g.boundary_type >= 2.000000:
                        for x_str,y_str in symPts:
                            x2,y2 = int(x_str), int(y_str)    
                            if x2 + y2 + 1 < g.n:                  
                                if x+x2 < g.n and y+y2 < g.n and y+y2 < g.n - (x+x2):
                                    addClause(-g.v[x][y], -g.v[x+x2][y+y2])
                
    elif g.k == 6:
        symPts  = re.findall(r'\((\d+),\s*(\d+)\)', points_stringk6n97fp)
        upPts   = re.findall(r'\((\d+),\s*(\d+)\)', points_stringk6upperbounds)
        downPts = re.findall(r'\((\d+),\s*(\d+)\)', points_stringk6lowerbounds)

        for x in range(g.n):
            for y in range(g.n):
                if x == 0 and y == 0: #block all unreachable from (0,0)
                    for x_str,y_str in upPts: # upper bound
                        x2,y2 = int(x_str), int(y_str)                          
                        if x+x2 < g.n and y+y2 < g.n and y+y2 < g.n - (x+x2) and x2 + y2 + 1 < g.n:
                            #print(f"blocking ({x+x2},{y+y2})")
                            addClause(-g.v[x+x2][y+y2])
                    for x_str,y_str in downPts: # lower bound
                        x2,y2 = int(x_str), int(y_str)                          
                        if x+x2 < g.n and y+y2 < g.n and y+y2 < g.n - (x+x2) and x2 + y2 + 1 < g.n:
                            #print(f"blocking ({x+x2},{y+y2})")
                            addClause(-g.v[x+x2][y+y2])
                else: #block unreachable from (x,y) within some distance of it
                    if g.boundary_type >= 2.000000:
                        for x_str,y_str in symPts:
                            x2,y2 = int(x_str), int(y_str)    
                            if x2 + y2 + 1 < g.n:                     
                                if x+x2 < g.n and y+y2 < g.n and y+y2 < g.n - (x+x2):
                                    #print(f"blocking ({x+x2},{y+y2})")
                                    addClause(-g.v[x][y], -g.v[x+x2][y+y2])


def BUP_EachPoint_VHLine(lineLen): # does not account for symmetry break
    g.out_log_file.write(f"BUP_EachPoint_VHLine: {lineLen}\n") 
    for x in range(g.n): 
        for y in range(g.n):
            if y < g.n - x:
                i = 0
                while y+(g.k-1)+i < g.n - x and y+(g.k-1)+i < g.n and i <= lineLen:
                    # print(f'x:{x},y:{y},y+k-1+i:{y+k-1+i}')
                    addClause(-g.v[x][y],-g.v[x][y+(g.k-1)+i]) # positive
                    i += 1

    for y in range(g.n):
        for x in range(g.n):
            if x < g.n - y:        
                i = 0
                while x+(g.k-1)+i < g.n - y and x+(g.k-1)+i < g.n and i <= lineLen:
                    addClause(-g.v[x][y],-g.v[x+(g.k-1)+i][y]) # positive
                    i += 1


def BUP_EachPoint_NegDiagonalLine(lineLen):
    g.out_log_file.write(f"BUP_EachPoint_NegDiagonalLine: {lineLen}\n") 
    # constraint: if (x,y) is true then all upper/lower negative diagonal are false
    for x in range(g.n): 
        for y in range(g.n):
            if y < g.n - x:
                i = 1
                while x+i < g.n and y-i >=0 and i <= lineLen:
                    # print(f'x:{x},y:{y},-v[{x+i}][{y-i}]')
                    addClause(-g.v[x][y],-g.v[x+i][y-i]) # right-down
                    i += 1

                i = 1 
                while x-i >= 0 and y+i < g.n and i <= lineLen:
                   # print(f'x:{x},y:{y},y+k-1+i:{y+k-1+i}')
                   addClause(-g.v[x][y],-g.v[x-i][y+i]) # left-up
                   i += 1


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