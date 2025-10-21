import math
import time
import re
import time
import os
from datetime import datetime
import argparse
import subprocess

lex_debug = 0

def parse_arguments():
    parser = argparse.ArgumentParser(description="e. for k=7, n=122, point (33, 88): python3 encode.py -k 7 -n 122 -x 33 -y 88 -s 1 -c 0 -v 1 -a 0 -l -0 -b 0 -f 0 -t 0 -r 0")
    parser.add_argument("-k", default=5, help="number of collinear points to avoid")
    parser.add_argument("-n", default=28, help="n points; n-1 steps")
    parser.add_argument("-x", default=0, help="point x")
    parser.add_argument("-y", default=0, help="point y")
    parser.add_argument("-s", default=1, help="symmetry break [0=off, 1=on]")
    parser.add_argument("-c", default=0, help="v/h cardinality constraints [0=off, 1=on]")
    parser.add_argument("-v", default=1, help="v/h line binary clauses [0=off, 1=on]")
    parser.add_argument("-a", default=0, help="antidiagonal constraints [0=off, 1=on]")
    parser.add_argument("-l", default=0, help="cutoff length for v/h line and antidiagonal. 0=1 point, 5=6 points")
    parser.add_argument("-b", default=0, help="boundary constraints [0=off, 1=unit clauses, 2=unit+binary clauses]") # at one point this was used as float value, haven't changed
    parser.add_argument("-f", default=0, help="0=CNF (cadical), 1=KNF (card. cadical)")
    parser.add_argument("-t", default=0, help="sat solver wall-clock timeout (s)")
    parser.add_argument("-e", default=None, help="CNF cardinality encoding type: seqcounter, totalizer, sortnetwrk, cardnetwrk, mtotalizer, kmtotalizer")
    parser.add_argument("-r", default=0, help="SAT solver seed")
    parser.add_argument("-o", default=0, help="Use lexicographic symmetry breaking constraints")
    parser.add_argument("-p", default=0, help="results folder name")
    parser.add_argument("-j", default=0, help="Line-Filter Heuristic; only block lines with length at least k+j points")
    parser.add_argument("-z", default=0, help="1=Generate cube files for .icnf")
    parser.add_argument("--zr", default=0, help="march free variable removal cutoff")
    parser.add_argument("--zl", default=0, help="march cube limit")
    parser.add_argument("--zc", default=0, help="Cadical conflict value")
    parser.add_argument("-w", default=0, help="Solve using CCDCL Hybrid Mode")
    
    return vars(parser.parse_args())

args = parse_arguments()
k=int(args["k"])
n=int(args["n"])
px=int(args["x"])
py=int(args["y"])
sym_break=int(args["s"])
vh_card=int(args["c"])
vh_line=int(args["v"])
antidiag=int(args["a"])
cutoff=int(args["l"])
boundary_type=int(args["b"])
use_KNF=int(args["f"])
cnf_encoding=(args["e"])
solver_timeout=int(args["t"])
solver_seed=int(args["r"])
use_lex=int(args["o"])
lex_len=n//2 # hard coded for now
results_folder_name=str(args["p"])
filter_threshold=int(args["j"])
march_generate_cubes=int(args["z"])
march_free_var=int(args["zr"])
march_cube_limit=int(args["zl"])
march_cadical_conflict_value=int(args["zc"])
use_hybrid=int(args["w"])

options_str = f"k:{k}, n:{n}, x:{px}, y:{py}, sym_break:{sym_break}, vh_card:{vh_card}, vh_line:{vh_line}, antidiag:{antidiag}, cutoff:{cutoff}, boundary:{boundary_type}, solver:{use_KNF}, hybrid_mode: {use_hybrid}, encoding: {cnf_encoding}, seed:{solver_seed}, timeout:{solver_timeout}, lex:{use_lex}, filter_threshold:{filter_threshold} "

if px > 0 and py > 0:
    if px + py >= n:
        print("Invalid final point to solve for.")
        exit(-1)

if vh_line == 0 and vh_card == 0:
    print("Vertical/horizontal constraints required.")
    exit(-1)

run_ID = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
cwd=os.getcwd()

v = [[0 for _ in range(n)] for _ in range(n)]
lex_var = [0 for _ in range(n)]
right_step = [0 for _ in range(n)]
dimacs_buffer = []
num_vars = 0
var_cnt = 0
num_clauses = 0
num_card_clauses = 0

cwd_path = os.getcwd()
output_folder_path = os.path.join(cwd_path, 'output')
if not os.path.exists(output_folder_path):
    os.makedirs(output_folder_path, exist_ok=True)

result_folder_path = os.path.join(output_folder_path, results_folder_name)
if not os.path.exists(result_folder_path):
    os.makedirs(result_folder_path, exist_ok=True)

pysat_encode_path= f'{cwd_path}/solvers/Cardinality-CDCL/Tools/pysat_encode.py'
CDCL_path = f'{cwd_path}/solvers/cadical/build/cadical'
march_path= f'{cwd_path}/solvers/CnC/march_cu/march_cu'
knf2cnf_path = f'{cwd_path}/solvers/Cardinality-CDCL/Tools/knf2cnf'
konly_path = f'{cwd_path}/solvers/Cardinality-CDCL/Tools/konly' # For hybrid mode

icnf_filename = f'cubes.icnf'
icnf_filepath = f'{result_folder_path}/{icnf_filename}'

knf_dimacs_filename = f'dimacsFile.knf'
knf_dimacs_filepath = f'{result_folder_path}/{knf_dimacs_filename}'

cnf_encode_filename = f'encode.cnf'
cnf_encode_filepath = f'{result_folder_path}/{cnf_encode_filename}' 

full_knf_filename = f'full.knf'
full_knf_filepath = f'{result_folder_path}/{full_knf_filename}' 

cnf_dimacs_filename = f'dimacsFile.cnf'
cnf_dimacs_filepath = f'{result_folder_path}/{cnf_dimacs_filename}'

cnf_dimacs_simplified_filename = f'dimacsFile_simple.cnf'
cnf_dimacs_simplified_filepath = f'{result_folder_path}/{cnf_dimacs_simplified_filename}'

out_log_filename = f'logOutput.log'
out_log_filepath = f'{result_folder_path}/{out_log_filename}'
out_log_file = open(f'{out_log_filepath}', 'w+', buffering=1)


def new_var():
    global num_vars
    num_vars += 1
    return num_vars

def add_clause(*literals):
    res = to_clause(literals)
    dimacs_buffer.append(res)


def to_clause(*literals):
    global num_clauses
    tmpStr = []
    for lit in literals:
        for i in lit:
            tmpStr.append(str(i))
            tmpStr.append(" ")
    tmpStr.append("0")
    clauseStr = ''.join(tmpStr)
    num_clauses += 1
    return clauseStr


def define_path_variables():
    global var_cnt
    for b in range(n):        # Define vars diagonally: 
        for x in range(n):
            y = b-x
            if y >= 0:
                    v[x][y] = new_var()
                    var_cnt += 1
    
    
def block_extremal_points():    
    # Block points too close to the x or y axis that cannot avoid k-1 vertical/horizontal steps
    for x in range(n):
        for y in range(n):
            if x + y < n:
                if sym_break:
                    if not ((x < (k-2)*y+1) and (y < (k-2)*x+(k-1))): 
                        add_clause(-v[x][y])
                        #print(f"blocking ({x},{y})")
                else:
                    if not ((x < (k-2)*y+(k-1)) and (y < (k-2)*x+(k-1))): 
                        add_clause(-v[x][y])
                        #print(f"blocking ({x},{y})")


"""
Path Constraints
"""
def encode_path_constraints(): 
    add_clause(v[0][0])        # The origin is always on the path
    for x in range(0, n):      # Step constraint 1a
        for y in range(0, n):
            if y < n - x - 1:
                add_clause(-v[x][y], v[x + 1][y], v[x][y + 1])     # v(x, y) --> v(x + 1, y) or v(x, y + 1)
                add_clause(-v[x + 1][y], -v[x][y + 1])               # ~[v(x + 1, y) and v(x, y + 1)]

    for x in range(0, n):      # Step constraint 1b
        for y in range(0, n):
            if x > 0 and y == 0:
                add_clause(-v[x][y], v[x - 1][y])
            elif x == 0 and y > 0:
                add_clause(-v[x][y], v[x][y - 1])
            elif x > 0 and y > 0:
                if y < n - x:
                    add_clause(-v[x][y], v[x - 1][y], v[x][y - 1])      # v(x, y) --> v(x - 1, y) or v(x, y - 1)
                    #add_clause(-v[x - 1][y], -v[x][y - 1])                # ~[v(x - 1, y) and v(x, y - 1)]              # This was duplicate




"""
Cardinality Constraints

Slope(= m_p/m_q):                                         only positive slopes are considered
  + Vertical Check:           (k-1)*m_p <= n-1            ensures that y-coord still fits inside triangle (given by y=n-x-1) after k-1 steps of m_p (rise)
  + Horizontal Check:         (k-1)*m_q <= n-1            ensures that x-coord still fits after k-1 steps of m_q (run)
  + Valid Slope Check:        1/(k-2) < m_p/m_q < (k-2)   ensures only slopes that allow fewer than k horizontal/vertical steps are considered.
y-intercept(= b_p/b_q):
  + Lower bound intercept:    m_q*b_p >= -m_p*(n-1)*b_q   ensures the line is not below y=0 by the time x=n-1, so it enters the triangle
  + Upper bound intercept:    b_p <= (n-1)*b_q            ensures the line is not already above y=n-1 when x=0, so it enters the triangle  
Other:
  + Duplicate checks:         gcd(m_p,m_q), gcd(b_p,b_q), b_q|m_q              filter out duplicate lines and invalid lines that will not have integer points.
  + Reachability checks:      (x <= (k-2)*y+(k-1)) and (y <= (k-2)*x+(k-1))    ensure that the points on these lines can actually be reached from the origin
"""
dbg_card = False
extra_debug = False
def encode_cardinality_constraints_KNF():   # At most k constraint: (excluding vertical and horizontal lines)
    global num_clauses, num_card_clauses, filter_threshold

    if extra_debug:
        from collections import defaultdict #(Temporary)
        length_hist = defaultdict(int)
        total_added = 0

    # filter threshold: 0=no filter, block lines with k+0 or more points
    # lengths where a correct SAT/UNSAT was found (single-seed test)
    # k6: 8 works for n97 and n98; n50 =0
    # k7: 20 works for n180 and n261; n50 <=2; n100 <= 7; n120 <= 15;  n150 <= 14; n200 <= 19; n250 <= 21; n261 ~= 20

    if filter_threshold > 0:
        print(f"cardinality constraint: Line-length filter heuristic - only include length at least k+{filter_threshold}")
        out_log_file.write(f"cardinality constraint: Linelength filter heuristic - only include length at least k+{filter_threshold}\n")
    else:
        print("cardinality constraint: No heuristic")
        out_log_file.write("cardinality constraint: No heuristic\n")

    for m_p in range(0, n):
        if (k - 1) * m_p > (n - 1):         # ensure at least k points can span the triangle vertically 
            continue 

        m_q = 1
        while (k - 1) * m_q <= (n - 1):     # ensure at least k points can span the triangle horizontally
            if (m_p == 0 and m_q != 1) or (math.gcd(m_p, m_q) > 1):
                m_q += 1
                continue

            if (m_p * (k-2)) < m_q:             # Trying slope > (k-2) and slope < 1/(k-2) now instead of slope >= (k-1) and slope <= 1/(k-2)
                break
            if m_p > ((k-2) * m_q):     
                m_q += 1
                continue

            for b_q in range(1, m_q + 1):       # y = (m_p/m_q) x + (b_p/b_q); b_q must divide m_q         
                for b_p in range(-m_p * n, (n - 1) * b_q + 1):      # upper bound on b_p: b=b_p/b_q < n when x=0, so y <= n-x-1
                    
                    # lower bound on b_p: b >= -m(n-1) when x=n-1, so that y >=0
                    if m_q * b_p < - m_p * (n - 1) * b_q:
                        continue
                    
                    if (b_p == 0 and b_q != 1) or (math.gcd(b_p, b_q) > 1) or (m_q % b_q != 0):
                        continue
                    tmp_str = []
                    debug_str = []
                    x = 0
                    y_is_integer = False
                    denominator = m_q * b_q

                    while x < n:
                        # find first valid point on this line
                        numerator = m_p * x * b_q + b_p * m_q         # replaced y=(m_p/m_q)*x+(b_p/b_q) floating point calculation with this
                        y = numerator // denominator
                        if y >= n:
                            break
                        if numerator % denominator != 0:              # y is not an integer
                            x += 1
                            continue                                                    
                        y_is_integer = True
                        break

                    if y_is_integer:
                        # step along line until (x,y) is within triangle (y >= 0, x+y < n)
                        while y < 0 and x < n:
                            x += m_q
                            y += m_p
                        if x >= n:
                            continue

                        # ensure at least k points on the line can actually fit inside the triangle before making list
                        point_cnt = 0
                        px, py = x, y
                        while px < n and 0 <= py < n - px and point_cnt < k:
                            point_cnt += 1
                            px += m_q
                            py += m_p
                        if point_cnt < k:
                            continue
                        
                        # enumerate points on the line within the triangle
                        reachable_cnt = 0
                        while x < n:
                            if 0 <= y < n - x:
                                # exclude points that can't be reached from origin without k horizontal/vertical steps
                                if sym_break == 1:
                                    if not ((x < (k-2)*y+1) and (y < (k-2)*x+(k-1))): 
                                        x += m_q
                                        y += m_p
                                        continue
                                else:
                                    if not ((x < (k-2)*y+(k-1)) and (y < (k-2)*x+(k-1))): 
                                        x += m_q
                                        y += m_p
                                        continue
                                tmp_str.append(str(-v[x][y]))
                                tmp_str.append(" ")
                                reachable_cnt += 1
                                if dbg_card: debug_str.append(f"({x},{y})")
                            else:
                                break
                            x += m_q
                            y += m_p
                    
                    # add the line as KNF cardinality constraint
                    if tmp_str and reachable_cnt >= k+filter_threshold:
                        clause = f'k {reachable_cnt - k + 1} {"".join(tmp_str)}0'
                        num_clauses += 1
                        dimacs_buffer.append(clause)
                        num_card_clauses += 1
                        
                        if dbg_card: 
                            out_log_file.write(" ".join(debug_str) + "\n")

                        if extra_debug:
                            length_hist[reachable_cnt] += 1
                            total_added += 1
            m_q += 1

    if extra_debug:    
        if length_hist:
            print("Cardinality lines added by length:")
            for L in sorted(length_hist):
                #print(f"  length {L}: {length_hist[L]}")
               print(f"{length_hist[L]}")
            print(f"Total cardinality lines added: {total_added}")



def encode_cardinality_constraints_KNF_VH():
    global num_clauses
    if not vh_card:
        return
    print(f"V/H Cardinality constraints")
    out_log_file.write(f"V/H Cardinality constraints\n")
    for x in range(0, n):                    # At most k constraint: vertical lines
        tmp_str = []
        cnt = 0
        for y in range(0, n):
            if y < n - x:
                tmp_str.append(str(-v[x][y]))
                tmp_str.append(" ")
                cnt = cnt + 1
            else:
                break
        if len(tmp_str) > 0 and cnt >= k:
            clause = f'k {cnt - k + 1} {"".join(tmp_str)} 0'
            num_clauses += 1
            dimacs_buffer.append(clause)

    for y in range(0, n):                   # At most k constraint: horizontal lines
        tmp_str = []
        cnt = 0
        for x in range(0, n):
            if x < n - y:
                tmp_str.append(str(-v[x][y]))
                tmp_str.append(" ")
                cnt = cnt + 1
            else:
                break
        if len(tmp_str) > 0 and cnt >= k:
            clause = f'k {cnt - k + 1} {"".join(tmp_str)} 0'
            num_clauses += 1
            dimacs_buffer.append(clause)




"""
Boundary Constraints
"""
def encode_boundary_constraints():
    if boundary_type == 0:
        return
    print(f"Boundary constraints: {boundary_type}")
    out_log_file.write(f"Boundary constraints: {boundary_type}\n")

    points_k7_upper_bounds_symmetric = """
        (0,6),(1,11),(2,16),(3,21),(4,26),(5,31),(6,0),(6,30),                      (7,33),(8,37),(9,41),(10,44),(11,1),(11,45),(12,47),(13,49),
        (14,52),(15,55),(16,2),(16,58),(17,60),(18,63),(19,65),(20,67),             (21,3),(21,69),(22,70),(23,71),(24,73),(25,75),(26,4),(26,78),
        (27,80),(28,82),(29,83),(30,6),(30,86),(31,5),(31,86),(32,88),              (33,7),(33,88),(34,89),(35,91),(36,92),(37,8),(37,91),(38,90),
        (39,91),(40,93),(41,9),(41,95),(42,97),(43,99),(44,10),(44,101),            (45,11),(45,102),(46,104),(47,12),(47,106),(48,108),(49,13),(49,109),
        (50,111),(51,113),(52,14),(52,115),(53,117),(54,119),(55,15),(55,121),      (56,123),(57,125),(58,16),(58,126),(59,128),(60,17),(60,130),(61,131),
        (62,133),(63,18),(63,135),(64,136),(65,19),(65,138),(66,140),(67,20),       (67,141),(68,143),(69,21),(69,144),(70,22),(70,146),(71,23),(71,148),
        (72,149),(73,24),(73,151),(74,153),(75,25),(75,155),(76,156),(77,156),      (78,26),(78,157),(79,156),(80,27),(80,158),(81,159),(82,28),(82,162),
        (83,29),(83,163),(84,165),(85,166),(86,30),(86,31),(86,167),(87,168),       (88,32),(88,33),(88,170),(89,34),(89,171),(90,38),(91,35),(91,37),
        (91,39),(92,36),(93,40),(95,41),(97,42),(99,43),(101,44),(102,45),          (104,46),(106,47),(108,48),(109,49),(111,50),(113,51),(115,52),(117,53),
        (119,54),(121,55),(123,56),(125,57),(126,58),(128,59),(130,60),(131,61),    (133,62),(135,63),(136,64),(138,65),(140,66),(141,67),(143,68),(144,69),
        (146,70),(148,71),(149,72),(151,73),(153,74),(155,75),(156,76),(156,77),    (156,79),(157,78),(158,80),(159,81),(162,82),(163,83),(165,84),(166,85),
        (167,86),(168,87),(170,88),(171,89)
    """

    points_k7_upper_bounds = """
        (0,6),(1,11),(2,16),(3,21),(4,26),(5,31),(6,30),(7,33),(8,37),             (9,41),(10,44),(11,45),(12,47),(13,49),(14,52),(15,55),(16,58),
        (17,60),(18,63),(19,65),(20,67),(21,69),(22,70),(23,71),(24,73),           (25,75),(26,78),(27,80),(28,82),(29,83),(30,86),(31,86),(32,88),
        (33,88),(34,89),(35,91),(36,92),(37,91),(38,90),(39,91),(40,93),           (41,95),(42,97),(43,99),(44,101),(45,102),(46,104),(47,106),(48,108),
        (49,109),(50,111),(51,113),(52,115),(53,117),(54,119),(55,121),(56,123),   (57,125),(58,126),(59,128),(60,130),(61,131),(62,133),(63,135),(64,136),
        (65,138),(66,140),(67,141),(68,143),(69,144),(70,146),(71,148),(72,149),   (73,151),(74,153),(75,155),(76,156),(77,156),(78,157),(79,156),(80,158),
        (81,159),(82,162),(83,163),(84,165),(85,166),(86,167),(87,168),(88,170),   (89,171)
    """

    points_k7_lower_bounds = """
        (1,0),(6,1),(11,2),(16,3),(21,4),(26,5),(30,6),(30,7),            (33,8),(37,9),(41,10),(43,11),(45,12),(45,13),(48,14),
        (51,15),(54,16),(57,17),(59,18),(62,19),(64,20),(66,21),          (67,22),(69,23),(71,24),(73,25),(75,26),(78,27),(79,28),
        (82,29),(83,30),(86,31),(86,32),(88,33),(88,34),(89,35),          (89,38),(89,39),(90,36),(90,37),(90,40),(92,41),(94,42),
        (96,43),(98,44),(100,45),(102,46),(104,47),(105,48),(107,49),     (109,50),(111,51),(112,52),(115,53),(116,54),(118,55),(120,56),
        (122,57),(124,58),(126,59),(127,60),(129,61),(131,62),(132,63),   (134,64),(136,65),(137,66),(139,67),(141,68),(142,69),(144,70),
        (145,71),(147,72),(149,73),(151,74),(153,75),(154,76),(154,77),   (155,78),(156,79),(156,80),(158,81),(159,82),(160,83),(162,84),
        (165,85),(165,86),(166,87),(168,88),(169,89),(171,90),(172,91),   (174,92)
    """
    
    # k6 bounds don't include internal boundary points
    points_k6_upper_bounds_symmetric = """
        (0,5),(1,9),(2,13),(3,17),(4,21),(5,20),(6,22),(7,24),            (8,26),(9,28),(10,29),(11,29),(12,31),(13,33),(14,35),
        (15,36),(16,38),(17,39),(18,41),(19,41),(20,42),(21,43),          (22,45),(23,46),(24,48),(25,49),(26,51),(27,53),(28,55),
        (29,56),(30,57),(31,55),(32,57),(33,57),(34,59),(35,59),          (36,57),(37,58),(38,58),(39,57),(5,0),(9,1),(13,2),(17,3),
        (20,5),(21,4),(22,6),(24,7),(26,8),(28,9),(29,10),(29,11),        (31,12),(33,13),(35,14),(36,15),(38,16),(39,17),(41,18),(41,19),
        (42,20),(43,21),(45,22),(46,23),(48,24),(49,25),(51,26),(53,27),  (55,28),(55,31),(56,29),(57,30),(57,32),(57,33),(57,36),(57,39),
        (58,37),(58,38),(59,34),(59,35),
    """

    points_k6_upper_bounds = """
        (0,5),(1,9),(2,13),(3,17),(4,21),(5,20),(6,22),(7,24),    (8,26),(9,28),(10,29),(11,29),(12,31),(13,33),(14,35),
        (15,36),(16,38),(17,39),(18,41),(19,41),(20,42),(21,43),  (22,45),(23,46),(24,48),(25,49),(26,51),(27,53),(28,55),
        (29,56),(30,57),(31,55),(32,57),(33,57),(34,59),(35,59),  (36,57),(37,58),(38,58),(39,57)
    """

    points_k6_lower_bounds= """
        (1,0),(5,1),(9,2),(13,3),(17,4),(20,5),(20,6),(22,7),     (24,8),(26,9),(27,10),(27,11),(28,12),(30,13),(32,14),
        (34,15),(36,16),(37,17),(38,18),(39,19),(40,20),(41,21),  (42,22),(44,23),(45,24),(47,25),(49,26),(51,27),(52,28),
        (54,29),(55,30),(55,31),(55,32),(56,33),(56,34),(59,35),  (57,36),(57,37),(57,38),(57,39),(58,36),
    """

    if k == 7:
        sp_str, up_str, lo_str = points_k7_upper_bounds_symmetric, points_k7_upper_bounds, points_k7_lower_bounds
    elif k == 6:
        sp_str, up_str, lo_str = points_k6_upper_bounds_symmetric, points_k6_upper_bounds, points_k6_lower_bounds
    else:
        return

    pat = r'\((\d+),\s*(\d+)\)'
    symmetric_pts = re.findall(pat, sp_str)
    upper_pts = re.findall(pat, up_str)
    lower_pts = re.findall(pat, lo_str)

    for x in range(n):
        for y in range(n):
            if x == 0 and y == 0:                     # Block all unreachable from (0,0)
                for pts in (upper_pts, lower_pts):
                    for x_str, y_str in pts:
                        x2, y2 = int(x_str), int(y_str)
                        if x + x2 < n and y + y2 < n and y + y2 < n - (x + x2) and x2 + y2 + 1 < n:
                            add_clause(-v[x + x2][y + y2])
            elif boundary_type >= 2:                # Block unreachable from (x,y) within some distance of it
                for x_str, y_str in symmetric_pts:
                    x2, y2 = int(x_str), int(y_str)
                    if x2 + y2 + 1 < n and x + x2 < n and y + y2 < n and y + y2 < n - (x + x2):
                        add_clause(-v[x][y], -v[x + x2][y + y2])




"""
Structural Constraints
"""
def encode_VH_binary_constraints(cutoff):
    if not vh_line:
        return
    print(f"V/H Binary constraints: {cutoff+1} point cutoff")
    out_log_file.write(f"V/H Binary constraints: {cutoff+1} point cutoff\n")

    for x in range(n): 
        for y in range(n):
            if y < n - x:
                i = 0
                while y+(k-1)+i < n - x and y+(k-1)+i < n and i <= cutoff:
                    #print(f'x:{x},y:{y},y+k-1+i:{y+k-1+i}')
                    add_clause(-v[x][y],-v[x][y+(k-1)+i]) 
                    i += 1

    for y in range(n):
        for x in range(n):
            if x < n - y:        
                i = 0
                while x+(k-1)+i < n - y and x+(k-1)+i < n and i <= cutoff:
                    #print(f"({x},{y})|({x+k-1+i},{y})")
                    add_clause(-v[x][y],-v[x+(k-1)+i][y])         
                    i += 1


def encode_antidiagonal_constraints(cutoff):
    if not antidiag:
        return
    print(f"Antidiagonal constraints: {cutoff+1} point cutoff")
    out_log_file.write(f"Antidiagonal constraints: {cutoff+1} point cutoff\n")
    
    # constraint: if (x,y) is true then all upper/lower negative diagonal are false
    for x in range(n): 
        for y in range(n):
            if y < n - x:
                i = 1
                while x+i < n and y-i >=0 and i <= cutoff:
                    # print(f'x:{x},y:{y},-v[{x+i}][{y-i}]')
                    add_clause(-v[x][y],-v[x+i][y-i])             # right-down
                    i += 1

                i = 1 
                while x-i >= 0 and y+i < n and i <= cutoff:
                   # print(f'x:{x},y:{y},y+k-1+i:{y+k-1+i}')
                   add_clause(-v[x][y],-v[x-i][y+i])              # left-up
                   i += 1





"""
Symmetry Constraints
"""
def reflection_symmetry_break():
    if not sym_break:
        return
    print(f"Symmetry break (0,1)")
    out_log_file.write(f"Symmetry break (0,1)\n")
    if n > 1:
        add_clause(v[0][1])

lex_debug = False
def create_lexicographic_encoding(num_points):
    if not use_lex:
        return
    if n <= 3:
        return
    print(f"Symmetry break Lexicographic")
    out_log_file.write(f"Symmetry break Lexicographic\n")

    NP = n #min(num_points, n//2)  

    for i in range(1,n):
        right_step[i] = new_var()

    cells_per_step = [[] for _ in range(n)]
    for x in range(n):
        for y in range(n):
            step = x + y
            if step < n:
                cells_per_step[step].append((x, y))

    for i in range(1, n):
        for x, y in cells_per_step[i]:
            if x > 0:
                if lex_debug: print(f"step[{i}] RIGHT clause: -v[{x-1}][{y}], -v[{x}][{y}], r[{i}]")
                add_clause(-v[x-1][y], -v[x][y],  right_step[i])
                if lex_debug: print(f"step[{i}] RIGHT clause: -r[{i}], -v[{x}][{y}], v[{x-1}][{y}]")
                add_clause(-right_step[i],   -v[x][y],   v[x-1][y])
            if y > 0:
                if lex_debug: print(f"step[{i}] UP clause: -v[{x}][{y-1}], -v[{x}][{y}], -r[{i}]")
                add_clause(-v[x][y-1], -v[x][y], -right_step[i])
                if lex_debug: print(f"step[{i}] UP clause: r[{i}], -v[{x}][{y}], v[{x}][{y-1}]")
                add_clause( right_step[i],  -v[x][y],   v[x][y-1])

    # Rotation
    fwd_idx = list(range(1, NP))
    rev_idx = [n - i for i in fwd_idx]
    seq_A = [right_step[i] for i in fwd_idx]
    seq_B = [right_step[j] for j in rev_idx]

    if lex_debug: print(f"LEX reverse compare indices A{ fwd_idx } = {seq_A}  vs B{ rev_idx } = {seq_B}")
    lex_vars = encode_lexicographic_constraints(seq_A, seq_B)
    for k, lv in enumerate(lex_vars):
        lex_var[k] = lv
        if lex_debug: print(f"lexVar[{k}] = {lv}")

   # Rotation+Reflection
    rot_seq = []
    for i in fwd_idx:
        rev = n - i
        rot_seq.append(-right_step[rev])
    if lex_debug: print(f"LEX rot compare seqA={seq_A}  vs rot_seq={rot_seq}")
    rot_lex_vars = encode_lexicographic_constraints(seq_A, rot_seq)
    for k, rv in enumerate(rot_lex_vars):
        if lex_debug: print(f"rotLexVar[{k}] = {rv}")


def encode_lexicographic_constraints(seqA, seqB): # from knuth eq 169
    L = len(seqA)
    assert L == len(seqB), "string lengths must be equal"
    
    # Create L-1 lex variables
    lex_vars = [new_var() for _ in range(L-1)]

    # Base case at position 0:
    if lex_debug: print(f"lex[0] clause: -{seqA[0]}, {seqB[0]}")            # (~A0 ∨ B0)
    add_clause(-seqA[0], seqB[0])
    if lex_debug: print(f"lex[0] clause: -{seqA[0]}, {lex_vars[0]}")        # (~A0 ∨ lex0)
    add_clause(-seqA[0], lex_vars[0])
    if lex_debug: print(f"lex[0] clause: {seqB[0]}, {lex_vars[0]}")         # (B0 ∨ lex0)
    add_clause(seqB[0],  lex_vars[0])
    if lex_debug: print(f"lex[0] clause: {lex_vars[0]}")                    # (lex0)

    # Recurrence for positions 1..L-2:
    for i in range(1, L-1):
        a = seqA[i]
        b = seqB[i]
        prev = lex_vars[i-1]
        curr = lex_vars[i]

        if lex_debug: print(f"lex[{i}] clause: -{a}, {b}, -{prev}")          # (~Ai ∨ Bi ∨ ~prev)
        add_clause(-a, b,     -prev)
        if lex_debug: print(f"lex[{i}] clause: -{a}, {curr}, -{prev}")       # (~Ai ∨ curr ∨ ~prev)
        add_clause(-a, curr,  -prev)
        if lex_debug: print(f"lex[{i}] clause: {b}, {curr}, -{prev}")        # (Bi ∨ curr ∨ ~prev)
        add_clause(b,  curr,  -prev)

    # Final boundary at position L-1:
    a_last = seqA[L-1]
    b_last = seqB[L-1]
    prev   = lex_vars[L-2]

    if lex_debug: print(f"lex[final] clause: -{a_last}, {b_last}, -{prev}")  # (~A_last ∨ B_last ∨ ~prev)
    add_clause(-a_last, b_last, -prev)

    return lex_vars



def solve_single_point():
    if (px == 0 and py == 0):
        return
    print(f"Single point solve: ({px},{py}), v:{v[px][py]}")
    out_log_file.write(f"Single point solve: ({px},{py}), v:{v[px][py]}\n")
    add_clause(v[px][py])





"""
Generate icnf cubes (march/CnC)
"""
def generate_icnf():

    print(f"Simplifying dimacsFile.cnf with Cadical")
    out_log_file.write(f"Simplifying dimacsFile.cnf with Cadical\n")

    command = [CDCL_path, cnf_dimacs_filepath,"-o", cnf_dimacs_simplified_filepath, "-c", f"{march_cadical_conflict_value}"]
    proc = subprocess.Popen(command, stdout=out_log_file, stderr=subprocess.STDOUT)
    proc.wait()

    print(f"Generating cubes with params: m:{num_vars}, r:{march_free_var}, l:{march_cube_limit}")
    out_log_file.write(f"Generating cubes with params: m:{num_vars}, r:{march_free_var}, l:{march_cube_limit}\n")

    #command = [march_path, cnf_dimacs_simplified_filepath,"-o", icnf_filepath, "-m", str(num_vars), "-r", str(march_free_var), "-l", str(march_cube_limit)]
   #"--min_y", "67", "--max_y", "73", "--min_x", "62", "--max_x", "76"] #"--min_y", "63", "--max_y", "77", "--min_x", "62", "--max_x", "76"]# "--min_y", "55", "--max_y", "85", "--min_x", "55", "--max_x", "85"] #129 cubes max, but all left of midline 
   #"--min_y", "66", "--max_y", "106", "--min_x", "65", "--max_x", "105"
    command = [march_path, cnf_dimacs_simplified_filepath,"-o", icnf_filepath, "-m", 
               str(num_vars), "-r", str(march_free_var), "-l", str(march_cube_limit), "--min_y", "46", "--max_y", "106", "--min_x", "45", "--max_x", "105"]#"--min_y", "0", "--max_y", "0", "--min_x", "0", "--max_x", "0"]# "--min_y", "56", "--max_y", "96", "--min_x", "55", "--max_x", "95"]
    proc = subprocess.Popen(command, stdout=out_log_file, stderr=subprocess.STDOUT)
    proc.wait()
    time.sleep(1) 


"""
Convert KNF to CNF
"""
def knf2cnf():
    print("Converting to CNF file")
    mode = "KNF" if use_KNF == 1 else "CNF"

    if mode == "CNF":
        if cnf_encoding is not None:
            print(f"CNF Encode: {cnf_encoding}")
            out_log_file.write(f"CNF Encode: {cnf_encoding}\n")
        else:
            print("CNF Encode: knf2cnf (sequential counter, linear AMO)")
            out_log_file.write("CNF Encode: knf2cnf (sequential counter, linear AMO)\n")

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



"""
Generate hybrid dimacs file (HYBRID mode)
"""
def generate_hybrid_dimacs():
    print("Generating Hybrid Dimacs file")
    with open(cnf_encode_filepath) as f:
        cnf = f.readlines()
    with open(knf_dimacs_filepath) as f:
        knf = f.readlines()

    for l in cnf:
        if l.startswith("p cnf"):
            _, _, v1, c1 = l.split()[:4]
            break
    for l in knf:
        if l.startswith("p knf"):
            _, _, v2, c2 = l.split()[:4]
            break

    v = int(v1)
    cls = int(c1) + int(c2)
    body = [l for l in knf if not l.startswith("p ")] + [l for l in cnf if not l.startswith("p ")]

    with open(full_knf_filepath, "w") as out:
        out.write(f"p knf {v} {cls}\n")
        out.writelines(body)

    time.sleep(1) 

def konly(): # for HYBRID
    print("Creating k-encoded cnf file (konly)")

    cnf_encode_file = open(cnf_encode_filepath, 'w+')

    command = f'\'{konly_path}\' \'{knf_dimacs_filepath}\''
    result = subprocess.Popen(command, shell=True, stdout=cnf_encode_file, stderr=subprocess.PIPE, text=True)
    result.wait()

    cnf_encode_file.close()
    time.sleep(1) 

def block_midline_range(dist):
    print(f"Blocking points > {dist} points of midline")
    out_log_file.write(f"Blocking points > {dist} points of midline\n")

    for x in range(n):
        for y in range(n):
            if x+y < n:
                if y > x+dist*2+1 or x > y+dist*2-1:
                    #print(f"blocking({x},{y}): {-v[x][y]}")
                    add_clause(-v[x][y])



def main():
    start_time = time.time()

    print(result_folder_path)
    out_log_file.write(f"{result_folder_path}\n")

    print(f"k:{k}, n:{n}, x:{px}, y:{py}, sym_break:{sym_break}, vh_card:{vh_card}, vh_line:{vh_line}, antidiag:{antidiag}, cutoff:{cutoff}, boundary:{boundary_type}, solver:{use_KNF}, hybrid_mode: {use_hybrid}, encoding: {cnf_encoding}, seed:{solver_seed}, timeout:{solver_timeout}, lex:{use_lex}, (k+c):{filter_threshold} ")
    out_log_file.write(f"k:{k}, n:{n}, x:{px}, y:{py}, sym_break:{sym_break}, vh_card:{vh_card}, vh_line:{vh_line}, antidiag:{antidiag}, cutoff:{cutoff}, boundary:{boundary_type}, solver:{use_KNF}, hybrid_mode: {use_hybrid}, encoding: {cnf_encoding}, seed:{solver_seed}, timeout:{solver_timeout}, lex:{use_lex},  (k+c):{filter_threshold}\n")

    define_path_variables()

    # Mandatory constraints
    encode_path_constraints()
    encode_cardinality_constraints_KNF()

    # block unreachable extremal points
    block_extremal_points()

    # If solving for a specific final point
    solve_single_point()

    # Optional constraints
    reflection_symmetry_break()
    encode_cardinality_constraints_KNF_VH()
    encode_VH_binary_constraints(cutoff)         
    encode_antidiagonal_constraints(cutoff)
    encode_boundary_constraints()
    create_lexicographic_encoding(lex_len)

    CnC_test = False
    if CnC_test == True: # Specifically for generating cubes, and the knf file that the cubes will be added to.
        print("CnC Test - midline distance 25")
        if k == 7: 
            distance=25
            block_midline_range(distance) # Block points far from midline; heuristic from looking at known paths past n=300

    CnC_test2 = False
    if CnC_test2 == True: # Specifically for generating cubes, and the knf file that the cubes will be added to.
        print("CnC Test2 - midline pinch")
        if k == 7: 
            #print("blocking: ")
            for x in range(n):
                y = 136 - x
                if (x < 60 or x > 75) and y >= 0:
                    print(f"({x},{y}):{v[x][y]}, ", end="")
                    add_clause(-v[x][y])
            #print("\n")
    
    CnC_test3 = False
    if CnC_test3 == True:
        print("CnC Test 3: Path-only points")
        block_str = """
         (0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (2, 8), (2, 9), (2, 10), (2, 11), (2, 12), (2, 13), (2, 14), (2, 15), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (3, 7), (3, 8), (3, 9), (3, 10), (3, 11), (3, 12), (3, 13), (3, 14), (3, 15), (3, 16), (3, 17), (3, 18), (3, 19), (3, 20), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6), (4, 7), (4, 8), (4, 9), (4, 10), (4, 11), (4, 12), (4, 13), (4, 14), (4, 15), (4, 16), (4, 17), (4, 18), (4, 19), (4, 20), (4, 21), (4, 22), (4, 23), (4, 24), (4, 25), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7), (5, 8), (5, 9), (5, 10), (5, 11), (5, 12), (5, 13), (5, 14), (5, 15), (5, 16), (5, 17), (5, 18), (5, 19), (5, 20), (5, 21), (5, 22), (5, 23), (5, 24), (5, 25), (5, 26), (5, 27), (5, 28), (6, 2), (6, 3), (6, 4), (6, 5), (6, 6), (6, 7), (6, 8), (6, 9), (6, 10), (6, 11), (6, 12), (6, 13), (6, 14), (6, 15), (6, 16), (6, 17), (6, 18), (6, 19), (6, 20), (6, 21), (6, 22), (6, 23), (6, 24), (6, 28), (6, 29), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6), (7, 7), (7, 8), (7, 9), (7, 10), (7, 11), (7, 12), (7, 13), (7, 14), (7, 15), (7, 16), (7, 17), (7, 18), (7, 19), (7, 20), (7, 21), (7, 22), (7, 23), (7, 24), (7, 25), (7, 28), (7, 29), (8, 2), (8, 3), (8, 4), (8, 5), (8, 6), (8, 7), (8, 8), (8, 9), (8, 10), (8, 11), (8, 12), (8, 13), (8, 14), (8, 15), (8, 16), (8, 17), (8, 18), (8, 19), (8, 20), (8, 21), (8, 22), (8, 23), (8, 24), (8, 25), (8, 26), (8, 27), (8, 28), (8, 29), (9, 2), (9, 3), (9, 4), (9, 5), (9, 6), (9, 7), (9, 8), (9, 9), (9, 10), (9, 11), (9, 12), (9, 13), (9, 14), (9, 15), (9, 16), (9, 17), (9, 18), (9, 19), (9, 20), (9, 21), (9, 22), (9, 23), (9, 24), (9, 25), (9, 26), (9, 27), (9, 28), (9, 29), (9, 30), (10, 2), (10, 3), (10, 4), (10, 5), (10, 6), (10, 7), (10, 8), (10, 9), (10, 10), (10, 11), (10, 12), (10, 13), (10, 14), (10, 15), (10, 16), (10, 17), (10, 18), (10, 19), (10, 20), (10, 21), (10, 22), (10, 23), (10, 24), (10, 25), (10, 26), (10, 27), (10, 28), (10, 29), (10, 30), (10, 31), (10, 32), (10, 33), (10, 34), (11, 3), (11, 4), (11, 5), (11, 6), (11, 7), (11, 8), (11, 9), (11, 10), (11, 11), (11, 12), (11, 13), (11, 14), (11, 15), (11, 16), (11, 17), (11, 18), (11, 19), (11, 20), (11, 21), (11, 22), (11, 23), (11, 24), (11, 25), (11, 26), (11, 27), (11, 28), (11, 29), (11, 30), (11, 31), (11, 32), (11, 33), (11, 34), (11, 35), (11, 36), (12, 3), (12, 4), (12, 5), (12, 6), (12, 7), (12, 8), (12, 9), (12, 10), (12, 11), (12, 14), (12, 15), (12, 16), (12, 17), (12, 18), (12, 19), (12, 20), (12, 21), (12, 22), (12, 23), (12, 24), (12, 25), (12, 26), (12, 27), (12, 28), (12, 29), (12, 30), (12, 31), (12, 32), (12, 33), (12, 34), (12, 35), (12, 36), (12, 37), (13, 3), (13, 4), (13, 5), (13, 6), (13, 7), (13, 8), (13, 9), (13, 10), (13, 11), (13, 12), (13, 15), (13, 18), (13, 19), (13, 20), (13, 21), (13, 22), (13, 23), (13, 24), (13, 25), (13, 26), (13, 27), (13, 28), (13, 29), (13, 30), (13, 31), (13, 32), (13, 33), (13, 34), (13, 35), (13, 36), (13, 37), (13, 38), (13, 39), (13, 40), (13, 41), (14, 3), (14, 4), (14, 5), (14, 6), (14, 7), (14, 8), (14, 9), (14, 10), (14, 11), (14, 12), (14, 15), (14, 18), (14, 19), (14, 20), (14, 21), (14, 22), (14, 23), (14, 24), (14, 25), (14, 26), (14, 27), (14, 28), (14, 29), (14, 30), (14, 31), (14, 32), (14, 33), (14, 34), (14, 35), (14, 36), (14, 37), (14, 38), (14, 39), (14, 40), (14, 41), (14, 42), (15, 3), (15, 4), (15, 5), (15, 6), (15, 7), (15, 8), (15, 9), (15, 10), (15, 11), (15, 12), (15, 15), (15, 16), (15, 17), (15, 18), (15, 19), (15, 20), (15, 21), (15, 22), (15, 23), (15, 24), (15, 25), (15, 26), (15, 27), (15, 28), (15, 29), (15, 30), (15, 31), (15, 32), (15, 33), (15, 34), (15, 35), (15, 36), (15, 37), (15, 38), (15, 39), (15, 40), (15, 41), (15, 42), (15, 43), (15, 44), (15, 45), (15, 46), (16, 4), (16, 5), (16, 6), (16, 7), (16, 8), (16, 9), (16, 10), (16, 11), (16, 12), (16, 13), (16, 18), (16, 19), (16, 20), (16, 21), (16, 22), (16, 23), (16, 24), (16, 25), (16, 26), (16, 27), (16, 28), (16, 29), (16, 30), (16, 31), (16, 32), (16, 33), (16, 34), (16, 35), (16, 36), (16, 37), (16, 38), (16, 39), (16, 40), (16, 41), (16, 42), (16, 43), (16, 44), (16, 46), (16, 47), (17, 4), (17, 5), (17, 6), (17, 7), (17, 8), (17, 9), (17, 10), (17, 11), (17, 12), (17, 13), (17, 14), (17, 20), (17, 23), (17, 24), (17, 25), (17, 26), (17, 27), (17, 28), (17, 29), (17, 30), (17, 31), (17, 32), (17, 33), (17, 34), (17, 35), (17, 36), (17, 37), (17, 38), (17, 39), (17, 40), (17, 41), (17, 42), (17, 43), (17, 44), (17, 45), (17, 46), (17, 47), (17, 48), (18, 4), (18, 5), (18, 6), (18, 7), (18, 8), (18, 9), (18, 10), (18, 11), (18, 12), (18, 13), (18, 14), (18, 15), (18, 16), (18, 17), (18, 20), (18, 26), (18, 27), (18, 28), (18, 29), (18, 30), (18, 31), (18, 32), (18, 33), (18, 34), (18, 35), (18, 36), (18, 37), (18, 38), (18, 39), (18, 40), (18, 41), (18, 42), (18, 45), (18, 46), (18, 47), (18, 48), (18, 49), (19, 4), (19, 5), (19, 6), (19, 7), (19, 8), (19, 9), (19, 10), (19, 11), (19, 12), (19, 13), (19, 14), (19, 15), (19, 16), (19, 17), (19, 18), (19, 20), (19, 28), (19, 29), (19, 30), (19, 31), (19, 32), (19, 33), (19, 34), (19, 35), (19, 36), (19, 37), (19, 38), (19, 39), (19, 40), (19, 41), (19, 42), (19, 43), (19, 45), (19, 46), (19, 48), (19, 49), (20, 4), (20, 5), (20, 6), (20, 7), (20, 8), (20, 9), (20, 10), (20, 11), (20, 12), (20, 13), (20, 15), (20, 16), (20, 17), (20, 18), (20, 19), (20, 20), (20, 21), (20, 31), (20, 32), (20, 33), (20, 34), (20, 35), (20, 36), (20, 37), (20, 38), (20, 39), (20, 40), (20, 41), (20, 42), (20, 43), (20, 46), (20, 48), (20, 49), (21, 5), (21, 6), (21, 7), (21, 8), (21, 9), (21, 10), (21, 11), (21, 12), (21, 13), (21, 14), (21, 15), (21, 18), (21, 19), (21, 21), (21, 31), (21, 32), (21, 33), (21, 34), (21, 35), (21, 36), (21, 37), (21, 38), (21, 39), (21, 40), (21, 41), (21, 42), (21, 43), (21, 46), (21, 48), (21, 49), (22, 5), (22, 6), (22, 7), (22, 8), (22, 9), (22, 10), (22, 11), (22, 12), (22, 13), (22, 14), (22, 15), (22, 16), (22, 17), (22, 18), (22, 19), (22, 21), (22, 31), (22, 32), (22, 33), (22, 34), (22, 35), (22, 36), (22, 37), (22, 38), (22, 39), (22, 40), (22, 41), (22, 42), (22, 43), (22, 44), (22, 45), (22, 46), (22, 48), (22, 49), (23, 5), (23, 6), (23, 7), (23, 8), (23, 9), (23, 10), (23, 11), (23, 12), (23, 13), (23, 14), (23, 15), (23, 16), (23, 17), (23, 18), (23, 19), (23, 20), (23, 21), (23, 22), (23, 23), (23, 24), (23, 31), (23, 32), (23, 33), (23, 34), (23, 35), (23, 36), (23, 37), (23, 38), (23, 39), (23, 40), (23, 41), (23, 42), (23, 43), (23, 44), (23, 45), (23, 46), (23, 49), (23, 50), (24, 5), (24, 9), (24, 10), (24, 11), (24, 12), (24, 13), (24, 14), (24, 15), (24, 16), (24, 17), (24, 18), (24, 19), (24, 21), (24, 24), (24, 25), (24, 26), (24, 27), (24, 28), (24, 29), (24, 31), (24, 32), (24, 33), (24, 34), (24, 35), (24, 36), (24, 37), (24, 38), (24, 39), (24, 40), (24, 41), (24, 42), (24, 43), (24, 44), (24, 45), (24, 46), (24, 47), (24, 48), (24, 49), (24, 50), (25, 5), (25, 6), (25, 7), (25, 8), (25, 9), (25, 10), (25, 11), (25, 12), (25, 13), (25, 14), (25, 15), (25, 16), (25, 17), (25, 18), (25, 19), (25, 20), (25, 21), (25, 22), (25, 29), (25, 30), (25, 31), (25, 32), (25, 33), (25, 34), (25, 35), (25, 36), (25, 37), (25, 38), (25, 39), (25, 40), (25, 41), (25, 42), (25, 43), (25, 44), (25, 45), (25, 46), (25, 47), (25, 48), (25, 49), (25, 50), (26, 6), (26, 7), (26, 8), (26, 9), (26, 10), (26, 11), (26, 12), (26, 13), (26, 14), (26, 15), (26, 16), (26, 17), (26, 18), (26, 19), (26, 20), (26, 22), (26, 32), (26, 33), (26, 34), (26, 35), (26, 36), (26, 37), (26, 38), (26, 39), (26, 40), (26, 41), (26, 42), (26, 43), (26, 44), (26, 45), (26, 46), (26, 47), (26, 48), (26, 49), (26, 50), (26, 51), (27, 10), (27, 11), (27, 12), (27, 13), (27, 14), (27, 15), (27, 16), (27, 17), (27, 18), (27, 19), (27, 20), (27, 22), (27, 32), (27, 33), (27, 34), (27, 35), (27, 36), (27, 37), (27, 38), (27, 39), (27, 40), (27, 41), (27, 42), (27, 43), (27, 44), (27, 45), (27, 46), (27, 47), (27, 48), (27, 49), (27, 50), (27, 51), (27, 52), (27, 53), (28, 10), (28, 11), (28, 12), (28, 13), (28, 14), (28, 15), (28, 16), (28, 17), (28, 18), (28, 19), (28, 20), (28, 22), (28, 23), (28, 32), (28, 33), (28, 34), (28, 35), (28, 36), (28, 37), (28, 38), (28, 39), (28, 40), (28, 41), (28, 42), (28, 43), (28, 44), (28, 45), (28, 46), (28, 47), (28, 48), (28, 49), (28, 50), (28, 51), (28, 52), (28, 53), (28, 54), (28, 55), (28, 56), (29, 10), (29, 11), (29, 12), (29, 13), (29, 14), (29, 15), (29, 16), (29, 17), (29, 18), (29, 19), (29, 20), (29, 23), (29, 33), (29, 36), (29, 37), (29, 38), (29, 39), (29, 40), (29, 41), (29, 42), (29, 43), (29, 44), (29, 45), (29, 46), (29, 47), (29, 48), (29, 49), (29, 50), (29, 51), (29, 52), (29, 53), (29, 54), (29, 55), (29, 56), (30, 10), (30, 11), (30, 12), (30, 13), (30, 14), (30, 15), (30, 16), (30, 17), (30, 18), (30, 19), (30, 20), (30, 21), (30, 23), (30, 33), (30, 36), (30, 37), (30, 38), (30, 39), (30, 40), (30, 41), (30, 42), (30, 43), (30, 44), (30, 45), (30, 46), (30, 47), (30, 48), (30, 49), (30, 50), (30, 51), (30, 52), (30, 53), (30, 54), (30, 55), (30, 56), (30, 57), (30, 58), (31, 11), (31, 12), (31, 13), (31, 14), (31, 15), (31, 16), (31, 17), (31, 18), (31, 19), (31, 20), (31, 21), (31, 22), (31, 23), (31, 33), (31, 37), (31, 38), (31, 39), (31, 40), (31, 41), (31, 42), (31, 43), (31, 44), (31, 45), (31, 46), (31, 47), (31, 48), (31, 49), (31, 50), (31, 51), (31, 52), (31, 53), (31, 54), (31, 55), (31, 56), (31, 57), (31, 58), (32, 11), (32, 12), (32, 13), (32, 14), (32, 15), (32, 16), (32, 17), (32, 18), (32, 19), (32, 20), (32, 21), (32, 22), (32, 23), (32, 24), (32, 25), (32, 26), (32, 27), (32, 28), (32, 33), (32, 34), (32, 35), (32, 36), (32, 37), (32, 38), (32, 39), (32, 40), (32, 41), (32, 42), (32, 43), (32, 44), (32, 45), (32, 46), (32, 47), (32, 48), (32, 49), (32, 50), (32, 51), (32, 52), (32, 53), (32, 54), (32, 55), (32, 56), (32, 57), (32, 58), (32, 59), (32, 60), (33, 11), (33, 12), (33, 13), (33, 14), (33, 15), (33, 16), (33, 17), (33, 18), (33, 19), (33, 20), (33, 21), (33, 22), (33, 23), (33, 24), (33, 25), (33, 26), (33, 27), (33, 28), (33, 29), (33, 38), (33, 39), (33, 40), (33, 41), (33, 42), (33, 43), (33, 44), (33, 45), (33, 46), (33, 47), (33, 48), (33, 49), (33, 50), (33, 51), (33, 52), (33, 53), (33, 54), (33, 55), (33, 56), (33, 57), (33, 58), (33, 59), (33, 60), (33, 61), (33, 62), (34, 12), (34, 13), (34, 14), (34, 15), (34, 16), (34, 17), (34, 18), (34, 19), (34, 20), (34, 21), (34, 22), (34, 23), (34, 24), (34, 25), (34, 26), (34, 27), (34, 28), (34, 29), (34, 30), (34, 31), (34, 38), (34, 39), (34, 40), (34, 41), (34, 42), (34, 43), (34, 44), (34, 45), (34, 46), (34, 47), (34, 48), (34, 49), (34, 50), (34, 51), (34, 52), (34, 53), (34, 54), (34, 55), (34, 56), (34, 57), (34, 58), (34, 59), (34, 60), (34, 62), (35, 12), (35, 13), (35, 14), (35, 16), (35, 17), (35, 18), (35, 19), (35, 20), (35, 21), (35, 22), (35, 23), (35, 24), (35, 25), (35, 26), (35, 27), (35, 28), (35, 29), (35, 30), (35, 31), (35, 39), (35, 40), (35, 41), (35, 42), (35, 43), (35, 44), (35, 45), (35, 46), (35, 47), (35, 48), (35, 49), (35, 50), (35, 51), (35, 52), (35, 53), (35, 54), (35, 55), (35, 56), (35, 57), (35, 58), (35, 59), (35, 60), (35, 61), (35, 62), (36, 13), (36, 14), (36, 15), (36, 16), (36, 17), (36, 18), (36, 19), (36, 20), (36, 21), (36, 22), (36, 23), (36, 24), (36, 25), (36, 26), (36, 27), (36, 28), (36, 29), (36, 30), (36, 31), (36, 32), (36, 33), (36, 34), (36, 35), (36, 39), (36, 40), (36, 41), (36, 42), (36, 43), (36, 44), (36, 45), (36, 46), (36, 47), (36, 48), (36, 49), (36, 50), (36, 51), (36, 52), (36, 53), (36, 54), (36, 55), (36, 56), (36, 57), (36, 58), (36, 59), (36, 60), (36, 61), (36, 62), (37, 13), (37, 14), (37, 15), (37, 18), (37, 19), (37, 20), (37, 21), (37, 22), (37, 23), (37, 24), (37, 26), (37, 27), (37, 28), (37, 29), (37, 31), (37, 35), (37, 36), (37, 39), (37, 40), (37, 41), (37, 42), (37, 43), (37, 44), (37, 45), (37, 46), (37, 47), (37, 48), (37, 49), (37, 50), (37, 51), (37, 52), (37, 53), (37, 54), (37, 55), (37, 56), (37, 57), (37, 58), (37, 60), (37, 61), (37, 62), (38, 13), (38, 14), (38, 15), (38, 16), (38, 17), (38, 18), (38, 19), (38, 20), (38, 21), (38, 22), (38, 23), (38, 24), (38, 25), (38, 26), (38, 27), (38, 28), (38, 29), (38, 30), (38, 31), (38, 32), (38, 33), (38, 36), (38, 39), (38, 40), (38, 41), (38, 42), (38, 43), (38, 44), (38, 45), (38, 46), (38, 47), (38, 48), (38, 49), (38, 50), (38, 51), (38, 52), (38, 53), (38, 54), (38, 55), (38, 56), (38, 57), (38, 58), (38, 60), (38, 62), (38, 63), (39, 14), (39, 17), (39, 18), (39, 19), (39, 20), (39, 21), (39, 22), (39, 23), (39, 24), (39, 25), (39, 26), (39, 27), (39, 28), (39, 29), (39, 31), (39, 32), (39, 33), (39, 34), (39, 35), (39, 36), (39, 37), (39, 38), (39, 39), (39, 40), (39, 41), (39, 42), (39, 43), (39, 44), (39, 45), (39, 46), (39, 47), (39, 48), (39, 49), (39, 50), (39, 51), (39, 52), (39, 53), (39, 54), (39, 55), (39, 56), (39, 57), (39, 58), (39, 60), (39, 62), (39, 63), (40, 14), (40, 15), (40, 16), (40, 17), (40, 18), (40, 19), (40, 21), (40, 22), (40, 23), (40, 24), (40, 25), (40, 26), (40, 27), (40, 28), (40, 29), (40, 30), (40, 31), (40, 32), (40, 33), (40, 34), (40, 36), (40, 37), (40, 38), (40, 39), (40, 40), (40, 41), (40, 42), (40, 43), (40, 44), (40, 45), (40, 46), (40, 47), (40, 48), (40, 49), (40, 50), (40, 51), (40, 53), (40, 54), (40, 55), (40, 56), (40, 57), (40, 58), (40, 59), (40, 60), (40, 61), (40, 62), (40, 63), (41, 14), (41, 15), (41, 18), (41, 19), (41, 20), (41, 21), (41, 22), (41, 23), (41, 24), (41, 25), (41, 26), (41, 27), (41, 28), (41, 29), (41, 30), (41, 31), (41, 32), (41, 34), (41, 35), (41, 36), (41, 37), (41, 38), (41, 39), (41, 40), (41, 41), (41, 42), (41, 43), (41, 44), (41, 45), (41, 46), (41, 47), (41, 48), (41, 49), (41, 50), (41, 51), (41, 52), (41, 53), (41, 54), (41, 55), (41, 56), (41, 57), (41, 58), (41, 59), (41, 60), (41, 61), (41, 62), (41, 63), (42, 14), (42, 15), (42, 16), (42, 21), (42, 22), (42, 23), (42, 24), (42, 25), (42, 26), (42, 27), (42, 28), (42, 29), (42, 30), (42, 31), (42, 32), (42, 33), (42, 34), (42, 35), (42, 36), (42, 37), (42, 38), (42, 39), (42, 40), (42, 41), (42, 42), (42, 43), (42, 44), (42, 45), (42, 46), (42, 47), (42, 48), (42, 49), (42, 50), (42, 51), (42, 52), (42, 53), (42, 54), (42, 55), (42, 56), (42, 57), (42, 58), (42, 59), (42, 61), (42, 62), (42, 63), (43, 15), (43, 16), (43, 17), (43, 18), (43, 19), (43, 20), (43, 21), (43, 23), (43, 24), (43, 25), (43, 26), (43, 27), (43, 28), (43, 29), (43, 30), (43, 31), (43, 32), (43, 33), (43, 34), (43, 35), (43, 36), (43, 37), (43, 38), (43, 39), (43, 40), (43, 41), (43, 42), (43, 43), (43, 44), (43, 45), (43, 46), (43, 47), (43, 48), (43, 49), (43, 50), (43, 51), (43, 52), (43, 53), (43, 54), (43, 55), (43, 56), (43, 57), (43, 58), (43, 59), (43, 61), (43, 63), (43, 64), (44, 16), (44, 17), (44, 18), (44, 19), (44, 20), (44, 21), (44, 22), (44, 23), (44, 24), (44, 25), (44, 26), (44, 27), (44, 28), (44, 29), (44, 30), (44, 31), (44, 32), (44, 33), (44, 34), (44, 35), (44, 36), (44, 37), (44, 38), (44, 39), (44, 40), (44, 41), (44, 42), (44, 43), (44, 44), (44, 45), (44, 46), (44, 47), (44, 48), (44, 49), (44, 50), (44, 51), (44, 52), (44, 53), (44, 54), (44, 55), (44, 56), (44, 57), (44, 58), (44, 59), (44, 61), (44, 63), (44, 64), (45, 21), (45, 22), (45, 23), (45, 24), (45, 25), (45, 26), (45, 27), (45, 28), (45, 29), (45, 30), (45, 31), (45, 32), (45, 33), (45, 38), (45, 39), (45, 40), (45, 41), (45, 42), (45, 43), (45, 44), (45, 45), (45, 46), (45, 47), (45, 48), (45, 49), (45, 50), (45, 51), (45, 52), (45, 53), (45, 54), (45, 55), (45, 56), (45, 57), (45, 58), (45, 59), (45, 60), (45, 61), (45, 62), (45, 63), (45, 64), (46, 24), (46, 25), (46, 26), (46, 27), (46, 28), (46, 29), (46, 30), (46, 31), (46, 32), (46, 33), (46, 34), (46, 35), (46, 36), (46, 41), (46, 42), (46, 43), (46, 44), (46, 45), (46, 46), (46, 47), (46, 48), (46, 49), (46, 50), (46, 51), (46, 52), (46, 53), (46, 54), (46, 55), (46, 56), (46, 57), (46, 58), (46, 59), (46, 60), (46, 61), (46, 62), (46, 63), (46, 64), (47, 26), (47, 27), (47, 28), (47, 29), (47, 30), (47, 31), (47, 32), (47, 33), (47, 34), (47, 35), (47, 36), (47, 37), (47, 41), (47, 42), (47, 43), (47, 44), (47, 45), (47, 46), (47, 47), (47, 48), (47, 49), (47, 50), (47, 51), (47, 52), (47, 53), (47, 54), (47, 55), (47, 56), (47, 57), (47, 58), (47, 59), (47, 60), (47, 61), (47, 62), (47, 63), (47, 64), (48, 26), (48, 27), (48, 28), (48, 29), (48, 30), (48, 31), (48, 32), (48, 34), (48, 35), (48, 36), (48, 37), (48, 38), (48, 39), (48, 40), (48, 41), (48, 42), (48, 43), (48, 44), (48, 45), (48, 46), (48, 47), (48, 48), (48, 49), (48, 50), (48, 51), (48, 52), (48, 53), (48, 56), (48, 57), (48, 58), (48, 59), (48, 60), (48, 61), (48, 62), (48, 63), (48, 64), (48, 65), (48, 66), (49, 26), (49, 27), (49, 28), (49, 29), (49, 30), (49, 31), (49, 32), (49, 33), (49, 34), (49, 35), (49, 36), (49, 37), (49, 38), (49, 39), (49, 40), (49, 41), (49, 42), (49, 43), (49, 44), (49, 45), (49, 46), (49, 47), (49, 48), (49, 49), (49, 50), (49, 51), (49, 52), (49, 53), (49, 56), (49, 57), (49, 58), (49, 59), (49, 60), (49, 61), (49, 62), (49, 64), (49, 65), (49, 66), (50, 26), (50, 27), (50, 28), (50, 29), (50, 30), (50, 31), (50, 32), (50, 33), (50, 37), (50, 38), (50, 39), (50, 40), (50, 41), (50, 42), (50, 43), (50, 44), (50, 45), (50, 46), (50, 47), (50, 48), (50, 49), (50, 50), (50, 51), (50, 52), (50, 53), (50, 54), (50, 55), (50, 56), (50, 57), (50, 58), (50, 59), (50, 60), (50, 61), (50, 62), (50, 63), (50, 64), (50, 65), (50, 66), (50, 67), (51, 26), (51, 27), (51, 28), (51, 29), (51, 30), (51, 31), (51, 32), (51, 33), (51, 34), (51, 35), (51, 37), (51, 38), (51, 41), (51, 42), (51, 43), (51, 44), (51, 45), (51, 46), (51, 47), (51, 48), (51, 49), (51, 50), (51, 51), (51, 52), (51, 53), (51, 54), (51, 55), (51, 56), (51, 57), (51, 58), (51, 59), (51, 60), (51, 61), (51, 62), (51, 63), (51, 64), (51, 65), (51, 66), (51, 67), (51, 68), (51, 69), (51, 70), (52, 27), (52, 28), (52, 29), (52, 30), (52, 31), (52, 32), (52, 33), (52, 34), (52, 35), (52, 36), (52, 37), (52, 38), (52, 39), (52, 42), (52, 43), (52, 44), (52, 45), (52, 46), (52, 47), (52, 48), (52, 49), (52, 50), (52, 51), (52, 52), (52, 53), (52, 54), (52, 55), (52, 56), (52, 57), (52, 58), (52, 59), (52, 60), (52, 61), (52, 63), (52, 64), (52, 65), (52, 66), (52, 67), (52, 68), (52, 69), (52, 70), (52, 71), (52, 72), (53, 28), (53, 29), (53, 30), (53, 31), (53, 32), (53, 33), (53, 34), (53, 35), (53, 36), (53, 37), (53, 38), (53, 39), (53, 40), (53, 41), (53, 42), (53, 43), (53, 44), (53, 45), (53, 46), (53, 47), (53, 48), (53, 49), (53, 50), (53, 51), (53, 52), (53, 53), (53, 54), (53, 55), (53, 56), (53, 57), (53, 58), (53, 59), (53, 60), (53, 61), (53, 62), (53, 63), (53, 64), (53, 65), (53, 66), (53, 67), (53, 68), (53, 69), (53, 72), (54, 29), (54, 30), (54, 31), (54, 32), (54, 33), (54, 34), (54, 35), (54, 36), (54, 37), (54, 38), (54, 39), (54, 40), (54, 41), (54, 42), (54, 43), (54, 44), (54, 45), (54, 46), (54, 47), (54, 48), (54, 49), (54, 50), (54, 51), (54, 52), (54, 53), (54, 54), (54, 56), (54, 57), (54, 58), (54, 59), (54, 60), (54, 61), (54, 62), (54, 63), (54, 64), (54, 65), (54, 66), (54, 68), (54, 69), (54, 70), (54, 72), (55, 30), (55, 31), (55, 32), (55, 33), (55, 34), (55, 35), (55, 36), (55, 37), (55, 38), (55, 39), (55, 40), (55, 41), (55, 42), (55, 43), (55, 44), (55, 45), (55, 46), (55, 47), (55, 48), (55, 49), (55, 50), (55, 51), (55, 52), (55, 53), (55, 54), (55, 55), (55, 56), (55, 57), (55, 58), (55, 59), (55, 60), (55, 61), (55, 62), (55, 63), (55, 64), (55, 65), (55, 66), (55, 68), (55, 70), (55, 72), (55, 73), (56, 30), (56, 31), (56, 32), (56, 33), (56, 34), (56, 35), (56, 36), (56, 37), (56, 38), (56, 39), (56, 40), (56, 41), (56, 42), (56, 43), (56, 44), (56, 45), (56, 46), (56, 47), (56, 48), (56, 49), (56, 50), (56, 51), (56, 52), (56, 53), (56, 54), (56, 55), (56, 56), (56, 57), (56, 58), (56, 59), (56, 60), (56, 61), (56, 62), (56, 63), (56, 64), (56, 65), (56, 66), (56, 67), (56, 68), (56, 70), (56, 73), (57, 31), (57, 32), (57, 33), (57, 34), (57, 35), (57, 36), (57, 37), (57, 38), (57, 39), (57, 40), (57, 41), (57, 42), (57, 43), (57, 44), (57, 45), (57, 46), (57, 47), (57, 48), (57, 49), (57, 50), (57, 51), (57, 52), (57, 53), (57, 54), (57, 55), (57, 56), (57, 57), (57, 58), (57, 59), (57, 60), (57, 61), (57, 62), (57, 63), (57, 64), (57, 65), (57, 66), (57, 67), (57, 68), (57, 70), (57, 71), (57, 73), (58, 31), (58, 32), (58, 33), (58, 34), (58, 35), (58, 36), (58, 37), (58, 38), (58, 39), (58, 40), (58, 41), (58, 42), (58, 43), (58, 44), (58, 45), (58, 46), (58, 47), (58, 48), (58, 49), (58, 50), (58, 51), (58, 52), (58, 53), (58, 54), (58, 55), (58, 56), (58, 57), (58, 58), (58, 59), (58, 60), (58, 61), (58, 62), (58, 63), (58, 64), (58, 65), (58, 66), (58, 67), (58, 68), (58, 69), (58, 71), (58, 73), (59, 33), (59, 34), (59, 35), (59, 36), (59, 37), (59, 38), (59, 42), (59, 43), (59, 44), (59, 45), (59, 46), (59, 47), (59, 48), (59, 49), (59, 50), (59, 51), (59, 52), (59, 53), (59, 54), (59, 55), (59, 56), (59, 57), (59, 58), (59, 59), (59, 60), (59, 61), (59, 62), (59, 63), (59, 64), (59, 65), (59, 66), (59, 67), (59, 68), (59, 69), (59, 70), (59, 71), (59, 72), (59, 73), (60, 34), (60, 35), (60, 36), (60, 37), (60, 38), (60, 39), (60, 40), (60, 41), (60, 42), (60, 46), (60, 47), (60, 48), (60, 49), (60, 50), (60, 51), (60, 52), (60, 53), (60, 54), (60, 55), (60, 56), (60, 57), (60, 58), (60, 59), (60, 60), (60, 61), (60, 62), (60, 63), (60, 64), (60, 65), (60, 66), (60, 67), (60, 68), (60, 69), (60, 71), (60, 73), (60, 74), (61, 36), (61, 37), (61, 38), (61, 39), (61, 40), (61, 41), (61, 42), (61, 43), (61, 44), (61, 45), (61, 46), (61, 47), (61, 48), (61, 49), (61, 50), (61, 51), (61, 52), (61, 53), (61, 54), (61, 55), (61, 56), (61, 57), (61, 58), (61, 59), (61, 60), (61, 61), (61, 62), (61, 63), (61, 64), (61, 65), (61, 66), (61, 67), (61, 68), (61, 69), (61, 70), (61, 71), (61, 72), (61, 73), (61, 74), (62, 38), (62, 39), (62, 40), (62, 41), (62, 42), (62, 43), (62, 44), (62, 45), (62, 46), (62, 47), (62, 48), (62, 49), (62, 50), (62, 51), (62, 52), (62, 53), (62, 54), (62, 55), (62, 56), (62, 57), (62, 58), (62, 59), (62, 60), (62, 61), (62, 62), (62, 63), (62, 64), (62, 65), (62, 66), (62, 67), (62, 68), (62, 69), (62, 70), (62, 71), (62, 72), (62, 73), (62, 74), (63, 43), (63, 44), (63, 45), (63, 46), (63, 47), (63, 48), (63, 49), (63, 50), (63, 51), (63, 52), (63, 53), (63, 54), (63, 55), (63, 56), (63, 57), (63, 58), (63, 59), (63, 60), (63, 61), (63, 62), (63, 63), (63, 64), (63, 65), (63, 66), (63, 67), (63, 68), (63, 69), (63, 70), (63, 71), (63, 72), (63, 73), (63, 74), (63, 75), (63, 76), (63, 77), (63, 78), (64, 48), (64, 49), (64, 50), (64, 51), (64, 52), (64, 53), (64, 54), (64, 55), (64, 56), (64, 57), (64, 58), (64, 59), (64, 60), (64, 61), (64, 62), (64, 63), (64, 64), (64, 65), (64, 66), (64, 67), (64, 68), (64, 69), (64, 70), (64, 71), (64, 72), (64, 73), (64, 74), (64, 75), (64, 76), (64, 77), (64, 78), (64, 79), (64, 80), (64, 81), (64, 82), (64, 83), (65, 48), (65, 50), (65, 51), (65, 52), (65, 53), (65, 54), (65, 55), (65, 56), (65, 57), (65, 58), (65, 59), (65, 60), (65, 61), (65, 62), (65, 63), (65, 64), (65, 65), (65, 66), (65, 67), (65, 68), (65, 69), (65, 70), (65, 71), (65, 72), (65, 73), (65, 74), (65, 75), (65, 77), (65, 78), (65, 79), (65, 80), (65, 81), (65, 82), (65, 83), (65, 84), (65, 85), (65, 86), (65, 87), (65, 88), (66, 48), (66, 50), (66, 51), (66, 52), (66, 53), (66, 54), (66, 55), (66, 56), (66, 57), (66, 58), (66, 59), (66, 60), (66, 61), (66, 62), (66, 63), (66, 64), (66, 65), (66, 66), (66, 67), (66, 68), (66, 69), (66, 70), (66, 71), (66, 72), (66, 73), (66, 74), (66, 75), (66, 76), (66, 82), (66, 83), (66, 84), (66, 85), (66, 86), (66, 87), (66, 88), (67, 48), (67, 49), (67, 50), (67, 51), (67, 52), (67, 53), (67, 54), (67, 55), (67, 56), (67, 57), (67, 58), (67, 59), (67, 60), (67, 61), (67, 62), (67, 63), (67, 64), (67, 65), (67, 66), (67, 67), (67, 68), (67, 69), (67, 70), (67, 71), (67, 72), (67, 73), (67, 74), (67, 75), (67, 76), (67, 77), (67, 87), (67, 88), (67, 89), (67, 90), (67, 91), (67, 92), (68, 53), (68, 54), (68, 55), (68, 56), (68, 57), (68, 58), (68, 59), (68, 60), (68, 61), (68, 62), (68, 63), (68, 64), (68, 65), (68, 66), (68, 67), (68, 68), (68, 69), (68, 70), (68, 71), (68, 72), (68, 73), (68, 74), (68, 75), (68, 76), (68, 77), (68, 78), (68, 79), (68, 89), (68, 92), (68, 93), (68, 94), (69, 53), (69, 54), (69, 57), (69, 58), (69, 59), (69, 60), (69, 61), (69, 62), (69, 63), (69, 64), (69, 65), (69, 66), (69, 67), (69, 68), (69, 69), (69, 70), (69, 71), (69, 72), (69, 73), (69, 74), (69, 75), (69, 76), (69, 77), (69, 78), (69, 79), (69, 80), (69, 81), (69, 82), (69, 83), (69, 84), (69, 89), (69, 94), (69, 95), (70, 53), (70, 54), (70, 55), (70, 57), (70, 58), (70, 59), (70, 60), (70, 61), (70, 62), (70, 63), (70, 64), (70, 65), (70, 66), (70, 67), (70, 68), (70, 69), (70, 70), (70, 71), (70, 72), (70, 73), (70, 74), (70, 75), (70, 76), (70, 77), (70, 78), (70, 79), (70, 80), (70, 81), (70, 82), (70, 83), (70, 84), (70, 85), (70, 86), (70, 89), (70, 95), (71, 54), (71, 55), (71, 56), (71, 57), (71, 58), (71, 59), (71, 60), (71, 61), (71, 62), (71, 63), (71, 64), (71, 65), (71, 66), (71, 67), (71, 68), (71, 69), (71, 70), (71, 71), (71, 72), (71, 73), (71, 74), (71, 75), (71, 76), (71, 77), (71, 78), (71, 79), (71, 80), (71, 81), (71, 82), (71, 83), (71, 84), (71, 85), (71, 86), (71, 87), (71, 88), (71, 89), (71, 95), (72, 55), (72, 58), (72, 59), (72, 60), (72, 61), (72, 62), (72, 63), (72, 64), (72, 65), (72, 66), (72, 67), (72, 68), (72, 69), (72, 70), (72, 71), (72, 72), (72, 73), (72, 74), (72, 75), (72, 76), (72, 77), (72, 78), (72, 79), (72, 80), (72, 81), (72, 82), (72, 83), (72, 84), (72, 85), (72, 86), (72, 87), (72, 88), (72, 89), (72, 90), (72, 91), (72, 92), (72, 93), (72, 94), (72, 95), (73, 55), (73, 63), (73, 64), (73, 65), (73, 66), (73, 67), (73, 68), (73, 69), (73, 70), (73, 71), (73, 72), (73, 73), (73, 74), (73, 75), (73, 76), (73, 77), (73, 78), (73, 79), (73, 80), (73, 81), (73, 82), (73, 83), (73, 84), (73, 85), (73, 86), (73, 87), (73, 88), (73, 89), (73, 90), (73, 91), (73, 92), (73, 93), (73, 94), (73, 95), (73, 96), (74, 55), (74, 63), (74, 66), (74, 67), (74, 68), (74, 69), (74, 70), (74, 71), (74, 72), (74, 73), (74, 74), (74, 75), (74, 76), (74, 77), (74, 78), (74, 79), (74, 80), (74, 81), (74, 82), (74, 83), (74, 84), (74, 85), (74, 86), (74, 87), (74, 88), (74, 89), (74, 90), (74, 91), (74, 92), (74, 93), (74, 94), (74, 95), (74, 96), (75, 55), (75, 63), (75, 67), (75, 68), (75, 69), (75, 70), (75, 71), (75, 72), (75, 73), (75, 74), (75, 75), (75, 76), (75, 77), (75, 78), (75, 79), (75, 80), (75, 81), (75, 82), (75, 83), (75, 84), (75, 85), (75, 86), (75, 87), (75, 88), (75, 89), (75, 90), (75, 91), (75, 92), (75, 93), (75, 94), (75, 95), (75, 96), (75, 97), (75, 98), (76, 55), (76, 56), (76, 57), (76, 58), (76, 63), (76, 67), (76, 68), (76, 69), (76, 70), (76, 71), (76, 72), (76, 73), (76, 74), (76, 75), (76, 76), (76, 77), (76, 78), (76, 79), (76, 80), (76, 81), (76, 82), (76, 83), (76, 84), (76, 85), (76, 86), (76, 87), (76, 88), (76, 89), (76, 90), (76, 91), (76, 92), (76, 93), (76, 94), (76, 95), (76, 96), (76, 97), (76, 98), (77, 58), (77, 63), (77, 64), (77, 65), (77, 66), (77, 67), (77, 68), (77, 69), (77, 70), (77, 71), (77, 72), (77, 73), (77, 74), (77, 75), (77, 76), (77, 77), (77, 78), (77, 79), (77, 80), (77, 81), (77, 82), (77, 83), (77, 84), (77, 85), (77, 86), (77, 87), (77, 88), (77, 89), (77, 90), (77, 91), (77, 92), (77, 93), (77, 94), (77, 95), (77, 96), (77, 97), (77, 98), (77, 99), (78, 58), (78, 64), (78, 66), (78, 68), (78, 69), (78, 70), (78, 71), (78, 72), (78, 73), (78, 74), (78, 75), (78, 76), (78, 77), (78, 78), (78, 79), (78, 80), (78, 81), (78, 82), (78, 83), (78, 84), (78, 85), (78, 86), (78, 87), (78, 88), (78, 89), (78, 90), (78, 91), (78, 92), (78, 93), (78, 94), (78, 95), (78, 96), (78, 97), (78, 98), (78, 99), (78, 100), (78, 101), (78, 102), (78, 103), (78, 104), (79, 58), (79, 59), (79, 60), (79, 61), (79, 62), (79, 64), (79, 66), (79, 68), (79, 69), (79, 70), (79, 71), (79, 72), (79, 73), (79, 74), (79, 75), (79, 76), (79, 77), (79, 78), (79, 79), (79, 80), (79, 81), (79, 82), (79, 83), (79, 84), (79, 85), (79, 86), (79, 87), (79, 88), (79, 89), (79, 90), (79, 91), (79, 92), (79, 93), (79, 94), (79, 95), (79, 96), (79, 97), (79, 98), (79, 99), (79, 100), (79, 104), (79, 105), (79, 106), (80, 62), (80, 63), (80, 64), (80, 65), (80, 66), (80, 67), (80, 69), (80, 70), (80, 71), (80, 72), (80, 73), (80, 74), (80, 75), (80, 76), (80, 77), (80, 78), (80, 79), (80, 80), (80, 81), (80, 82), (80, 83), (80, 84), (80, 85), (80, 86), (80, 87), (80, 88), (80, 89), (80, 90), (80, 91), (80, 92), (80, 93), (80, 94), (80, 95), (80, 96), (80, 97), (80, 98), (80, 99), (80, 100), (80, 106), (81, 64), (81, 66), (81, 67), (81, 68), (81, 69), (81, 70), (81, 71), (81, 72), (81, 73), (81, 74), (81, 75), (81, 76), (81, 77), (81, 78), (81, 79), (81, 80), (81, 81), (81, 82), (81, 83), (81, 85), (81, 87), (81, 88), (81, 89), (81, 90), (81, 91), (81, 92), (81, 93), (81, 94), (81, 95), (81, 96), (81, 97), (81, 98), (81, 99), (81, 100), (81, 101), (81, 102), (81, 103), (81, 104), (81, 106), (82, 64), (82, 65), (82, 66), (82, 67), (82, 68), (82, 69), (82, 70), (82, 71), (82, 72), (82, 73), (82, 74), (82, 75), (82, 76), (82, 77), (82, 78), (82, 79), (82, 80), (82, 81), (82, 82), (82, 83), (82, 84), (82, 85), (82, 87), (82, 88), (82, 90), (82, 91), (82, 92), (82, 93), (82, 94), (82, 95), (82, 96), (82, 97), (82, 98), (82, 99), (82, 100), (82, 101), (82, 102), (82, 103), (82, 104), (82, 105), (82, 106), (82, 107), (82, 108), (82, 109), (83, 65), (83, 68), (83, 69), (83, 70), (83, 71), (83, 72), (83, 73), (83, 74), (83, 75), (83, 76), (83, 77), (83, 78), (83, 79), (83, 80), (83, 81), (83, 82), (83, 83), (83, 85), (83, 86), (83, 87), (83, 88), (83, 89), (83, 90), (83, 92), (83, 93), (83, 94), (83, 95), (83, 96), (83, 97), (83, 98), (83, 99), (83, 100), (83, 101), (83, 102), (83, 103), (83, 104), (83, 105), (83, 106), (83, 107), (83, 108), (83, 109), (83, 110), (83, 111), (83, 112), (83, 113), (83, 114), (84, 65), (84, 68), (84, 70), (84, 71), (84, 72), (84, 73), (84, 74), (84, 75), (84, 76), (84, 77), (84, 78), (84, 79), (84, 80), (84, 81), (84, 82), (84, 83), (84, 85), (84, 88), (84, 89), (84, 90), (84, 91), (84, 92), (84, 93), (84, 94), (84, 95), (84, 96), (84, 97), (84, 98), (84, 99), (84, 100), (84, 101), (84, 106), (84, 107), (84, 108), (84, 109), (84, 110), (84, 111), (84, 112), (84, 113), (84, 114), (84, 115), (84, 116), (84, 117), (84, 118), (84, 119), (85, 65), (85, 68), (85, 69), (85, 70), (85, 71), (85, 72), (85, 73), (85, 74), (85, 75), (85, 76), (85, 77), (85, 78), (85, 79), (85, 80), (85, 81), (85, 82), (85, 83), (85, 84), (85, 85), (85, 86), (85, 88), (85, 89), (85, 91), (85, 92), (85, 93), (85, 94), (85, 95), (85, 96), (85, 97), (85, 98), (85, 99), (85, 100), (85, 101), (85, 102), (85, 103), (85, 107), (85, 111), (85, 112), (85, 113), (85, 114), (85, 115), (85, 116), (85, 117), (85, 118), (85, 119), (85, 120), (85, 121), (85, 122), (85, 123), (85, 124), (86, 65), (86, 70), (86, 71), (86, 72), (86, 73), (86, 74), (86, 75), (86, 76), (86, 77), (86, 78), (86, 79), (86, 80), (86, 81), (86, 82), (86, 83), (86, 84), (86, 86), (86, 87), (86, 88), (86, 89), (86, 90), (86, 91), (86, 92), (86, 93), (86, 94), (86, 95), (86, 96), (86, 97), (86, 98), (86, 99), (86, 100), (86, 101), (86, 102), (86, 103), (86, 104), (86, 105), (86, 106), (86, 107), (86, 108), (86, 109), (86, 116), (86, 117), (86, 118), (86, 119), (86, 120), (86, 121), (86, 122), (86, 123), (86, 124), (86, 125), (86, 126), (87, 65), (87, 66), (87, 70), (87, 71), (87, 72), (87, 73), (87, 74), (87, 75), (87, 76), (87, 77), (87, 78), (87, 79), (87, 80), (87, 81), (87, 82), (87, 83), (87, 84), (87, 85), (87, 86), (87, 87), (87, 88), (87, 89), (87, 90), (87, 91), (87, 92), (87, 93), (87, 94), (87, 95), (87, 96), (87, 97), (87, 98), (87, 99), (87, 100), (87, 101), (87, 102), (87, 103), (87, 104), (87, 105), (87, 106), (87, 107), (87, 108), (87, 109), (87, 110), (87, 111), (87, 112), (87, 113), (87, 114), (87, 121), (87, 122), (87, 123), (87, 124), (87, 125), (87, 126), (88, 66), (88, 70), (88, 71), (88, 72), (88, 73), (88, 74), (88, 75), (88, 76), (88, 77), (88, 78), (88, 79), (88, 80), (88, 81), (88, 82), (88, 83), (88, 84), (88, 85), (88, 86), (88, 88), (88, 89), (88, 90), (88, 91), (88, 92), (88, 93), (88, 94), (88, 95), (88, 96), (88, 97), (88, 98), (88, 99), (88, 100), (88, 101), (88, 102), (88, 107), (88, 108), (88, 109), (88, 110), (88, 111), (88, 112), (88, 113), (88, 114), (88, 115), (88, 116), (88, 117), (88, 118), (88, 119), (88, 124), (88, 125), (88, 126), (88, 127), (88, 128), (88, 129), (89, 66), (89, 71), (89, 72), (89, 73), (89, 74), (89, 75), (89, 76), (89, 77), (89, 78), (89, 79), (89, 80), (89, 81), (89, 82), (89, 83), (89, 84), (89, 85), (89, 86), (89, 87), (89, 89), (89, 90), (89, 91), (89, 92), (89, 93), (89, 94), (89, 95), (89, 96), (89, 97), (89, 98), (89, 99), (89, 100), (89, 101), (89, 102), (89, 103), (89, 104), (89, 105), (89, 106), (89, 107), (89, 112), (89, 113), (89, 114), (89, 115), (89, 116), (89, 117), (89, 118), (89, 119), (89, 120), (89, 121), (89, 122), (89, 123), (89, 124), (89, 125), (89, 126), (89, 127), (89, 128), (89, 129), (89, 130), (89, 131), (90, 66), (90, 71), (90, 72), (90, 73), (90, 74), (90, 75), (90, 76), (90, 77), (90, 78), (90, 79), (90, 80), (90, 81), (90, 82), (90, 83), (90, 84), (90, 85), (90, 86), (90, 87), (90, 88), (90, 89), (90, 90), (90, 92), (90, 93), (90, 94), (90, 95), (90, 96), (90, 97), (90, 98), (90, 99), (90, 100), (90, 101), (90, 102), (90, 103), (90, 104), (90, 105), (90, 106), (90, 107), (90, 108), (90, 109), (90, 110), (90, 111), (90, 112), (90, 117), (90, 118), (90, 119), (90, 120), (90, 121), (90, 122), (90, 123), (90, 124), (90, 125), (90, 126), (90, 127), (90, 128), (90, 129), (90, 130), (90, 131), (91, 66), (91, 72), (91, 73), (91, 74), (91, 75), (91, 76), (91, 77), (91, 78), (91, 79), (91, 80), (91, 81), (91, 82), (91, 83), (91, 84), (91, 85), (91, 86), (91, 87), (91, 88), (91, 89), (91, 90), (91, 92), (91, 93), (91, 94), (91, 95), (91, 96), (91, 97), (91, 98), (91, 99), (91, 100), (91, 103), (91, 104), (91, 105), (91, 106), (91, 107), (91, 108), (91, 109), (91, 110), (91, 111), (91, 112), (91, 113), (91, 114), (91, 115), (91, 116), (91, 117), (91, 122), (91, 123), (91, 124), (91, 126), (91, 127), (91, 128), (91, 129), (91, 130), (91, 131), (91, 132), (91, 133), (91, 134), (92, 66), (92, 67), (92, 68), (92, 72), (92, 73), (92, 74), (92, 75), (92, 76), (92, 77), (92, 78), (92, 79), (92, 80), (92, 81), (92, 82), (92, 83), (92, 84), (92, 85), (92, 86), (92, 87), (92, 88), (92, 89), (92, 90), (92, 91), (92, 92), (92, 93), (92, 94), (92, 95), (92, 96), (92, 97), (92, 98), (92, 99), (92, 100), (92, 101), (92, 102), (92, 103), (92, 105), (92, 106), (92, 107), (92, 108), (92, 109), (92, 110), (92, 111), (92, 112), (92, 113), (92, 114), (92, 115), (92, 116), (92, 117), (92, 118), (92, 119), (92, 120), (92, 121), (92, 122), (92, 124), (92, 128), (92, 129), (92, 130), (92, 131), (92, 132), (92, 133), (92, 134), (92, 135), (92, 136), (93, 68), (93, 69), (93, 70), (93, 72), (93, 73), (93, 74), (93, 75), (93, 76), (93, 77), (93, 78), (93, 79), (93, 80), (93, 81), (93, 82), (93, 83), (93, 84), (93, 85), (93, 86), (93, 87), (93, 88), (93, 89), (93, 90), (93, 91), (93, 92), (93, 93), (93, 94), (93, 95), (93, 96), (93, 97), (93, 98), (93, 99), (93, 100), (93, 101), (93, 102), (93, 103), (93, 104), (93, 105), (93, 106), (93, 107), (93, 108), (93, 111), (93, 112), (93, 113), (93, 114), (93, 115), (93, 116), (93, 117), (93, 118), (93, 119), (93, 120), (93, 121), (93, 122), (93, 123), (93, 124), (93, 125), (93, 126), (93, 127), (93, 128), (93, 129), (93, 130), (93, 131), (93, 132), (93, 135), (93, 136), (94, 70), (94, 71), (94, 72), (94, 73), (94, 74), (94, 75), (94, 77), (94, 78), (94, 79), (94, 80), (94, 81), (94, 82), (94, 83), (94, 84), (94, 85), (94, 86), (94, 87), (94, 88), (94, 89), (94, 90), (94, 91), (94, 92), (94, 93), (94, 94), (94, 95), (94, 96), (94, 97), (94, 98), (94, 99), (94, 100), (94, 101), (94, 102), (94, 103), (94, 104), (94, 105), (94, 106), (94, 108), (94, 109), (94, 110), (94, 111), (94, 112), (94, 113), (94, 116), (94, 117), (94, 118), (94, 119), (94, 120), (94, 121), (94, 122), (94, 123), (94, 124), (94, 125), (94, 126), (94, 127), (94, 128), (94, 130), (94, 131), (94, 132), (94, 133), (94, 134), (94, 135), (94, 136), (94, 137), (94, 138), (94, 139), (95, 73), (95, 74), (95, 75), (95, 76), (95, 77), (95, 78), (95, 79), (95, 80), (95, 81), (95, 82), (95, 83), (95, 84), (95, 85), (95, 86), (95, 87), (95, 88), (95, 89), (95, 90), (95, 91), (95, 92), (95, 93), (95, 94), (95, 95), (95, 96), (95, 97), (95, 98), (95, 99), (95, 100), (95, 101), (95, 102), (95, 103), (95, 105), (95, 106), (95, 113), (95, 114), (95, 115), (95, 116), (95, 117), (95, 118), (95, 121), (95, 122), (95, 123), (95, 124), (95, 125), (95, 126), (95, 127), (95, 128), (95, 129), (95, 130), (95, 131), (95, 132), (95, 133), (95, 135), (95, 136), (95, 137), (95, 139), (95, 140), (95, 141), (96, 73), (96, 74), (96, 75), (96, 76), (96, 77), (96, 78), (96, 79), (96, 80), (96, 81), (96, 82), (96, 83), (96, 84), (96, 85), (96, 86), (96, 87), (96, 88), (96, 89), (96, 90), (96, 91), (96, 92), (96, 93), (96, 94), (96, 95), (96, 96), (96, 97), (96, 98), (96, 99), (96, 100), (96, 101), (96, 102), (96, 103), (96, 104), (96, 105), (96, 106), (96, 107), (96, 108), (96, 118), (96, 119), (96, 120), (96, 121), (96, 122), (96, 123), (96, 124), (96, 125), (96, 126), (96, 127), (96, 128), (96, 129), (96, 130), (96, 131), (96, 132), (96, 133), (96, 135), (96, 137), (96, 141), (97, 73), (97, 76), (97, 77), (97, 78), (97, 79), (97, 80), (97, 81), (97, 82), (97, 83), (97, 84), (97, 85), (97, 86), (97, 87), (97, 88), (97, 89), (97, 90), (97, 91), (97, 92), (97, 93), (97, 94), (97, 95), (97, 96), (97, 97), (97, 98), (97, 99), (97, 100), (97, 101), (97, 102), (97, 103), (97, 104), (97, 105), (97, 106), (97, 107), (97, 108), (97, 109), (97, 110), (97, 111), (97, 112), (97, 113), (97, 123), (97, 124), (97, 125), (97, 126), (97, 127), (97, 129), (97, 130), (97, 131), (97, 132), (97, 133), (97, 135), (97, 136), (97, 137), (97, 141), (98, 73), (98, 74), (98, 79), (98, 80), (98, 81), (98, 82), (98, 83), (98, 84), (98, 85), (98, 86), (98, 87), (98, 88), (98, 89), (98, 90), (98, 91), (98, 92), (98, 93), (98, 94), (98, 95), (98, 96), (98, 97), (98, 98), (98, 99), (98, 100), (98, 101), (98, 102), (98, 103), (98, 104), (98, 105), (98, 106), (98, 107), (98, 108), (98, 109), (98, 110), (98, 111), (98, 112), (98, 113), (98, 114), (98, 115), (98, 116), (98, 117), (98, 118), (98, 125), (98, 127), (98, 128), (98, 129), (98, 130), (98, 131), (98, 132), (98, 133), (98, 136), (98, 137), (98, 141), (98, 142), (99, 74), (99, 79), (99, 80), (99, 81), (99, 82), (99, 83), (99, 84), (99, 85), (99, 86), (99, 87), (99, 88), (99, 89), (99, 90), (99, 91), (99, 92), (99, 93), (99, 94), (99, 95), (99, 96), (99, 97), (99, 98), (99, 99), (99, 100), (99, 101), (99, 102), (99, 103), (99, 104), (99, 105), (99, 106), (99, 107), (99, 108), (99, 109), (99, 110), (99, 111), (99, 112), (99, 113), (99, 114), (99, 115), (99, 116), (99, 117), (99, 118), (99, 119), (99, 120), (99, 121), (99, 122), (99, 123), (99, 125), (99, 126), (99, 127), (99, 128), (99, 129), (99, 130), (99, 131), (99, 133), (99, 134), (99, 135), (99, 136), (99, 137), (99, 138), (99, 142), (100, 74), (100, 75), (100, 76), (100, 77), (100, 79), (100, 80), (100, 81), (100, 82), (100, 83), (100, 85), (100, 86), (100, 87), (100, 88), (100, 89), (100, 90), (100, 91), (100, 92), (100, 93), (100, 94), (100, 95), (100, 96), (100, 97), (100, 98), (100, 99), (100, 100), (100, 101), (100, 102), (100, 103), (100, 104), (100, 105), (100, 106), (100, 107), (100, 108), (100, 109), (100, 110), (100, 111), (100, 112), (100, 113), (100, 114), (100, 115), (100, 116), (100, 117), (100, 118), (100, 119), (100, 120), (100, 121), (100, 122), (100, 123), (100, 124), (100, 125), (100, 126), (100, 127), (100, 128), (100, 129), (100, 130), (100, 131), (100, 132), (100, 133), (100, 134), (100, 135), (100, 136), (100, 138), (100, 142), (101, 77), (101, 78), (101, 79), (101, 80), (101, 81), (101, 82), (101, 83), (101, 84), (101, 85), (101, 86), (101, 87), (101, 88), (101, 89), (101, 90), (101, 91), (101, 92), (101, 93), (101, 94), (101, 95), (101, 96), (101, 97), (101, 98), (101, 99), (101, 100), (101, 101), (101, 102), (101, 103), (101, 104), (101, 105), (101, 106), (101, 107), (101, 108), (101, 109), (101, 110), (101, 111), (101, 112), (101, 113), (101, 114), (101, 115), (101, 116), (101, 117), (101, 118), (101, 119), (101, 120), (101, 121), (101, 122), (101, 123), (101, 124), (101, 125), (101, 126), (101, 127), (101, 128), (101, 129), (101, 130), (101, 131), (101, 132), (101, 133), (101, 134), (101, 135), (101, 136), (101, 137), (101, 138), (101, 142), (102, 81), (102, 82), (102, 83), (102, 84), (102, 85), (102, 86), (102, 87), (102, 88), (102, 89), (102, 90), (102, 91), (102, 92), (102, 93), (102, 94), (102, 95), (102, 96), (102, 97), (102, 98), (102, 99), (102, 100), (102, 101), (102, 102), (102, 106), (102, 107), (102, 108), (102, 111), (102, 112), (102, 113), (102, 114), (102, 115), (102, 116), (102, 117), (102, 118), (102, 119), (102, 120), (102, 121), (102, 122), (102, 123), (102, 124), (102, 125), (102, 126), (102, 127), (102, 128), (102, 129), (102, 130), (102, 131), (102, 132), (102, 133), (102, 134), (102, 135), (102, 136), (102, 137), (102, 138), (102, 139), (102, 140), (102, 142), (103, 81), (103, 82), (103, 83), (103, 84), (103, 86), (103, 87), (103, 88), (103, 89), (103, 90), (103, 91), (103, 92), (103, 93), (103, 94), (103, 95), (103, 96), (103, 97), (103, 98), (103, 99), (103, 100), (103, 101), (103, 102), (103, 103), (103, 106), (103, 107), (103, 108), (103, 109), (103, 110), (103, 111), (103, 112), (103, 113), (103, 116), (103, 117), (103, 118), (103, 119), (103, 120), (103, 121), (103, 122), (103, 123), (103, 124), (103, 125), (103, 126), (103, 127), (103, 128), (103, 129), (103, 130), (103, 131), (103, 132), (103, 133), (103, 134), (103, 135), (103, 136), (103, 137), (103, 138), (103, 139), (103, 140), (103, 141), (103, 142), (103, 143), (104, 81), (104, 82), (104, 83), (104, 84), (104, 86), (104, 87), (104, 88), (104, 89), (104, 90), (104, 91), (104, 92), (104, 93), (104, 94), (104, 95), (104, 96), (104, 97), (104, 98), (104, 99), (104, 100), (104, 101), (104, 102), (104, 103), (104, 106), (104, 107), (104, 108), (104, 109), (104, 110), (104, 111), (104, 112), (104, 113), (104, 114), (104, 115), (104, 116), (104, 117), (104, 118), (104, 121), (104, 122), (104, 123), (104, 124), (104, 125), (104, 126), (104, 127), (104, 128), (104, 129), (104, 130), (104, 131), (104, 132), (104, 133), (104, 134), (104, 135), (104, 136), (104, 137), (104, 138), (104, 139), (104, 140), (104, 141), (104, 142), (104, 143), (104, 144), (104, 145), (104, 146), (104, 147), (105, 82), (105, 83), (105, 84), (105, 86), (105, 87), (105, 88), (105, 89), (105, 90), (105, 91), (105, 92), (105, 93), (105, 94), (105, 95), (105, 96), (105, 97), (105, 98), (105, 99), (105, 100), (105, 101), (105, 102), (105, 103), (105, 111), (105, 112), (105, 113), (105, 114), (105, 115), (105, 116), (105, 117), (105, 118), (105, 119), (105, 120), (105, 121), (105, 122), (105, 123), (105, 126), (105, 127), (105, 128), (105, 129), (105, 130), (105, 131), (105, 132), (105, 133), (105, 134), (105, 135), (105, 136), (105, 139), (105, 140), (105, 141), (105, 142), (105, 143), (105, 145), (105, 146), (105, 147), (105, 148), (106, 82), (106, 83), (106, 84), (106, 85), (106, 86), (106, 87), (106, 88), (106, 89), (106, 90), (106, 91), (106, 92), (106, 93), (106, 94), (106, 95), (106, 96), (106, 97), (106, 98), (106, 99), (106, 100), (106, 101), (106, 102), (106, 103), (106, 104), (106, 116), (106, 117), (106, 118), (106, 119), (106, 120), (106, 121), (106, 122), (106, 123), (106, 124), (106, 125), (106, 126), (106, 127), (106, 128), (106, 129), (106, 130), (106, 131), (106, 132), (106, 133), (106, 134), (106, 135), (106, 136), (106, 137), (106, 138), (106, 139), (106, 140), (106, 141), (106, 142), (106, 143), (106, 147), (106, 148), (107, 82), (107, 83), (107, 84), (107, 85), (107, 86), (107, 87), (107, 88), (107, 89), (107, 90), (107, 91), (107, 92), (107, 93), (107, 94), (107, 95), (107, 96), (107, 97), (107, 98), (107, 99), (107, 100), (107, 101), (107, 102), (107, 103), (107, 104), (107, 105), (107, 106), (107, 121), (107, 122), (107, 123), (107, 124), (107, 125), (107, 126), (107, 127), (107, 128), (107, 129), (107, 130), (107, 131), (107, 132), (107, 133), (107, 134), (107, 135), (107, 136), (107, 137), (107, 138), (107, 139), (107, 140), (107, 141), (107, 142), (107, 143), (107, 144), (107, 145), (107, 146), (107, 147), (107, 148), (108, 82), (108, 83), (108, 84), (108, 85), (108, 87), (108, 88), (108, 89), (108, 90), (108, 91), (108, 92), (108, 93), (108, 94), (108, 95), (108, 96), (108, 97), (108, 98), (108, 99), (108, 100), (108, 102), (108, 103), (108, 104), (108, 105), (108, 106), (108, 126), (108, 127), (108, 128), (108, 129), (108, 130), (108, 131), (108, 132), (108, 133), (108, 134), (108, 135), (108, 136), (108, 137), (108, 138), (108, 139), (108, 140), (108, 141), (108, 142), (108, 143), (108, 147), (108, 148), (108, 149), (109, 82), (109, 83), (109, 84), (109, 85), (109, 86), (109, 87), (109, 88), (109, 89), (109, 90), (109, 91), (109, 92), (109, 93), (109, 94), (109, 95), (109, 96), (109, 97), (109, 98), (109, 99), (109, 100), (109, 102), (109, 103), (109, 104), (109, 105), (109, 106), (109, 129), (109, 130), (109, 131), (109, 132), (109, 133), (109, 134), (109, 135), (109, 136), (109, 137), (109, 138), (109, 139), (109, 140), (109, 141), (109, 142), (109, 143), (109, 144), (109, 145), (109, 146), (109, 147), (109, 148), (109, 149), (110, 83), (110, 84), (110, 85), (110, 87), (110, 88), (110, 89), (110, 90), (110, 91), (110, 92), (110, 93), (110, 94), (110, 95), (110, 96), (110, 97), (110, 98), (110, 99), (110, 100), (110, 101), (110, 102), (110, 103), (110, 104), (110, 106), (110, 132), (110, 133), (110, 134), (110, 135), (110, 136), (110, 137), (110, 138), (110, 139), (110, 140), (110, 141), (110, 142), (110, 143), (110, 144), (110, 145), (110, 146), (110, 147), (110, 148), (110, 149), (111, 83), (111, 84), (111, 85), (111, 86), (111, 87), (111, 88), (111, 89), (111, 90), (111, 91), (111, 92), (111, 93), (111, 94), (111, 95), (111, 96), (111, 97), (111, 98), (111, 99), (111, 100), (111, 101), (111, 103), (111, 104), (111, 105), (111, 106), (111, 132), (111, 133), (111, 134), (111, 135), (111, 136), (111, 137), (111, 138), (111, 139), (111, 140), (111, 141), (111, 142), (111, 143), (111, 144), (111, 145), (111, 146), (111, 147), (111, 148), (111, 149), (111, 150), (112, 83), (112, 84), (112, 85), (112, 86), (112, 87), (112, 88), (112, 89), (112, 90), (112, 91), (112, 92), (112, 93), (112, 94), (112, 95), (112, 96), (112, 97), (112, 99), (112, 100), (112, 101), (112, 103), (112, 104), (112, 105), (112, 106), (112, 107), (112, 132), (112, 133), (112, 134), (112, 135), (112, 136), (112, 138), (112, 139), (112, 140), (112, 141), (112, 142), (112, 143), (112, 144), (112, 145), (112, 146), (112, 148), (112, 149), (112, 150), (113, 83), (113, 84), (113, 85), (113, 86), (113, 88), (113, 89), (113, 90), (113, 91), (113, 92), (113, 93), (113, 94), (113, 95), (113, 96), (113, 97), (113, 98), (113, 99), (113, 100), (113, 101), (113, 103), (113, 104), (113, 105), (113, 106), (113, 107), (113, 133), (113, 134), (113, 135), (113, 136), (113, 137), (113, 138), (113, 139), (113, 140), (113, 141), (113, 142), (113, 143), (113, 144), (113, 145), (113, 146), (113, 148), (113, 149), (113, 150), (114, 83), (114, 84), (114, 85), (114, 86), (114, 88), (114, 89), (114, 90), (114, 91), (114, 92), (114, 93), (114, 94), (114, 95), (114, 96), (114, 97), (114, 98), (114, 99), (114, 100), (114, 101), (114, 103), (114, 104), (114, 105), (114, 106), (114, 107), (114, 133), (114, 134), (114, 135), (114, 136), (114, 137), (114, 138), (114, 139), (114, 140), (114, 141), (114, 142), (114, 143), (114, 144), (114, 145), (114, 146), (114, 147), (114, 148), (114, 149), (114, 150), (115, 84), (115, 85), (115, 86), (115, 88), (115, 89), (115, 90), (115, 91), (115, 92), (115, 93), (115, 94), (115, 95), (115, 96), (115, 97), (115, 98), (115, 99), (115, 100), (115, 101), (115, 102), (115, 103), (115, 104), (115, 105), (115, 107), (115, 134), (115, 136), (115, 137), (115, 138), (115, 139), (115, 140), (115, 141), (115, 142), (115, 143), (115, 144), (115, 145), (115, 146), (115, 147), (115, 148), (115, 149), (115, 150), (116, 84), (116, 85), (116, 86), (116, 87), (116, 88), (116, 89), (116, 90), (116, 91), (116, 92), (116, 93), (116, 94), (116, 95), (116, 96), (116, 97), (116, 98), (116, 99), (116, 100), (116, 101), (116, 102), (116, 104), (116, 105), (116, 106), (116, 107), (116, 134), (116, 137), (116, 139), (116, 140), (116, 141), (116, 142), (116, 143), (116, 144), (116, 145), (116, 146), (116, 147), (116, 148), (116, 149), (116, 150), (116, 151), (117, 84), (117, 85), (117, 86), (117, 87), (117, 88), (117, 89), (117, 90), (117, 91), (117, 92), (117, 93), (117, 94), (117, 95), (117, 96), (117, 97), (117, 98), (117, 100), (117, 101), (117, 102), (117, 104), (117, 105), (117, 106), (117, 107), (117, 108), (117, 134), (117, 135), (117, 137), (117, 139), (117, 140), (117, 141), (117, 142), (117, 143), (117, 144), (117, 145), (117, 146), (117, 147), (117, 148), (117, 149), (117, 150), (117, 151), (118, 84), (118, 85), (118, 86), (118, 87), (118, 89), (118, 90), (118, 91), (118, 92), (118, 93), (118, 94), (118, 95), (118, 96), (118, 97), (118, 98), (118, 99), (118, 100), (118, 101), (118, 102), (118, 104), (118, 105), (118, 106), (118, 107), (118, 108), (118, 135), (118, 137), (118, 138), (118, 139), (118, 140), (118, 141), (118, 142), (118, 143), (118, 144), (118, 145), (118, 146), (118, 147), (118, 148), (118, 149), (118, 150), (118, 151), (119, 84), (119, 85), (119, 86), (119, 87), (119, 89), (119, 90), (119, 91), (119, 92), (119, 93), (119, 94), (119, 95), (119, 96), (119, 97), (119, 98), (119, 99), (119, 100), (119, 101), (119, 102), (119, 104), (119, 105), (119, 106), (119, 107), (119, 108), (119, 135), (119, 137), (119, 138), (119, 140), (119, 141), (119, 142), (119, 143), (119, 144), (119, 145), (119, 146), (119, 147), (119, 148), (119, 149), (119, 150), (119, 151), (120, 85), (120, 86), (120, 87), (120, 89), (120, 90), (120, 91), (120, 92), (120, 93), (120, 94), (120, 95), (120, 96), (120, 97), (120, 98), (120, 99), (120, 100), (120, 101), (120, 102), (120, 103), (120, 104), (120, 105), (120, 106), (120, 108), (120, 135), (120, 137), (120, 138), (120, 140), (120, 141), (120, 142), (120, 143), (120, 144), (120, 145), (120, 146), (120, 147), (120, 148), (120, 149), (120, 150), (120, 151), (121, 85), (121, 86), (121, 87), (121, 88), (121, 89), (121, 90), (121, 91), (121, 92), (121, 93), (121, 94), (121, 95), (121, 96), (121, 97), (121, 98), (121, 99), (121, 100), (121, 101), (121, 102), (121, 103), (121, 105), (121, 106), (121, 107), (121, 108), (121, 135), (121, 138), (121, 141), (121, 142), (121, 143), (121, 144), (121, 145), (121, 146), (121, 147), (121, 148), (121, 149), (121, 150), (121, 151), (121, 152), (121, 153), (122, 85), (122, 86), (122, 87), (122, 88), (122, 89), (122, 90), (122, 91), (122, 92), (122, 93), (122, 94), (122, 95), (122, 96), (122, 97), (122, 98), (122, 99), (122, 101), (122, 102), (122, 103), (122, 105), (122, 106), (122, 107), (122, 108), (122, 109), (122, 135), (122, 136), (122, 138), (122, 141), (122, 142), (122, 143), (122, 144), (122, 145), (122, 146), (122, 147), (122, 148), (122, 149), (122, 150), (122, 151), (122, 152), (122, 153), (122, 154), (122, 155), (123, 85), (123, 86), (123, 87), (123, 88), (123, 89), (123, 90), (123, 91), (123, 92), (123, 93), (123, 94), (123, 95), (123, 96), (123, 97), (123, 98), (123, 99), (123, 100), (123, 101), (123, 102), (123, 103), (123, 105), (123, 106), (123, 107), (123, 108), (123, 109), (123, 136), (123, 138), (123, 139), (123, 140), (123, 141), (123, 142), (123, 143), (123, 144), (123, 145), (123, 146), (123, 147), (123, 148), (123, 149), (123, 150), (123, 151), (123, 152), (123, 153), (123, 154), (123, 155), (124, 85), (124, 86), (124, 87), (124, 88), (124, 90), (124, 91), (124, 92), (124, 93), (124, 94), (124, 95), (124, 96), (124, 97), (124, 98), (124, 99), (124, 100), (124, 101), (124, 102), (124, 103), (124, 105), (124, 106), (124, 107), (124, 108), (124, 109), (124, 136), (124, 139), (124, 140), (124, 141), (124, 142), (124, 143), (124, 144), (124, 145), (124, 146), (124, 147), (124, 148), (124, 149), (124, 150), (124, 151), (124, 152), (124, 153), (124, 154), (124, 155), (124, 156), (124, 157), (125, 86), (125, 87), (125, 88), (125, 89), (125, 90), (125, 91), (125, 92), (125, 93), (125, 94), (125, 95), (125, 96), (125, 97), (125, 98), (125, 99), (125, 100), (125, 101), (125, 102), (125, 103), (125, 104), (125, 105), (125, 106), (125, 107), (125, 109), (125, 136), (125, 139), (125, 141), (125, 142), (125, 143), (125, 144), (125, 145), (125, 146), (125, 147), (125, 148), (125, 149), (125, 150), (125, 151), (125, 152), (125, 153), (125, 154), (125, 155), (125, 156), (125, 157), (125, 158), (125, 159), (125, 160), (125, 161), (125, 162), (126, 86), (126, 87), (126, 88), (126, 89), (126, 90), (126, 91), (126, 92), (126, 93), (126, 94), (126, 95), (126, 96), (126, 97), (126, 98), (126, 99), (126, 100), (126, 101), (126, 102), (126, 103), (126, 104), (126, 105), (126, 106), (126, 107), (126, 108), (126, 109), (126, 136), (126, 139), (126, 140), (126, 141), (126, 142), (126, 143), (126, 145), (126, 147), (126, 148), (126, 149), (126, 150), (126, 151), (126, 152), (126, 153), (126, 154), (126, 155), (126, 156), (126, 157), (126, 162), (127, 86), (127, 88), (127, 89), (127, 90), (127, 91), (127, 92), (127, 93), (127, 94), (127, 95), (127, 96), (127, 97), (127, 98), (127, 99), (127, 100), (127, 102), (127, 103), (127, 104), (127, 105), (127, 106), (127, 107), (127, 108), (127, 109), (127, 110), (127, 136), (127, 137), (127, 138), (127, 139), (127, 140), (127, 141), (127, 142), (127, 143), (127, 144), (127, 145), (127, 146), (127, 147), (127, 148), (127, 149), (127, 150), (127, 151), (127, 152), (127, 153), (127, 154), (127, 155), (127, 156), (127, 157), (127, 162), (127, 163), (128, 86), (128, 87), (128, 88), (128, 89), (128, 90), (128, 91), (128, 92), (128, 93), (128, 94), (128, 95), (128, 96), (128, 97), (128, 98), (128, 99), (128, 100), (128, 101), (128, 102), (128, 103), (128, 104), (128, 105), (128, 106), (128, 107), (128, 108), (128, 109), (128, 110), (128, 140), (128, 142), (128, 143), (128, 144), (128, 145), (128, 146), (128, 147), (128, 148), (128, 149), (128, 150), (128, 151), (128, 152), (128, 153), (128, 154), (128, 155), (128, 156), (128, 157), (128, 163), (129, 87), (129, 88), (129, 89), (129, 90), (129, 91), (129, 92), (129, 93), (129, 94), (129, 95), (129, 96), (129, 97), (129, 98), (129, 99), (129, 100), (129, 101), (129, 102), (129, 103), (129, 104), (129, 105), (129, 106), (129, 107), (129, 108), (129, 109), (129, 110), (129, 140), (129, 141), (129, 142), (129, 143), (129, 144), (129, 145), (129, 146), (129, 147), (129, 148), (129, 149), (129, 150), (129, 151), (129, 152), (129, 153), (129, 154), (129, 155), (129, 156), (129, 157), (129, 158), (129, 163), (130, 87), (130, 88), (130, 89), (130, 91), (130, 92), (130, 93), (130, 94), (130, 95), (130, 96), (130, 97), (130, 98), (130, 99), (130, 100), (130, 101), (130, 102), (130, 103), (130, 104), (130, 105), (130, 106), (130, 107), (130, 108), (130, 109), (130, 110), (130, 144), (130, 145), (130, 146), (130, 147), (130, 148), (130, 149), (130, 150), (130, 151), (130, 152), (130, 153), (130, 154), (130, 155), (130, 156), (130, 157), (130, 158), (130, 163), (131, 89), (131, 90), (131, 91), (131, 92), (131, 93), (131, 94), (131, 95), (131, 96), (131, 97), (131, 98), (131, 99), (131, 100), (131, 101), (131, 102), (131, 103), (131, 104), (131, 105), (131, 106), (131, 107), (131, 108), (131, 109), (131, 110), (131, 111), (131, 112), (131, 149), (131, 150), (131, 151), (131, 152), (131, 153), (131, 154), (131, 155), (131, 156), (131, 157), (131, 158), (131, 159), (131, 160), (131, 161), (131, 163), (132, 89), (132, 92), (132, 93), (132, 94), (132, 95), (132, 96), (132, 97), (132, 98), (132, 99), (132, 100), (132, 101), (132, 102), (132, 103), (132, 104), (132, 105), (132, 106), (132, 107), (132, 108), (132, 109), (132, 110), (132, 111), (132, 112), (132, 113), (132, 149), (132, 150), (132, 151), (132, 152), (132, 153), (132, 154), (132, 155), (132, 156), (132, 157), (132, 158), (132, 161), (132, 163), (132, 164), (133, 89), (133, 90), (133, 92), (133, 93), (133, 94), (133, 95), (133, 96), (133, 97), (133, 98), (133, 99), (133, 100), (133, 101), (133, 102), (133, 103), (133, 104), (133, 105), (133, 106), (133, 107), (133, 108), (133, 109), (133, 110), (133, 111), (133, 112), (133, 113), (133, 114), (133, 115), (133, 116), (133, 117), (133, 149), (133, 150), (133, 151), (133, 152), (133, 153), (133, 154), (133, 155), (133, 156), (133, 157), (133, 158), (133, 159), (133, 160), (133, 161), (133, 162), (133, 163), (133, 164), (133, 165), (133, 166), (134, 90), (134, 91), (134, 94), (134, 95), (134, 96), (134, 97), (134, 98), (134, 99), (134, 100), (134, 101), (134, 102), (134, 103), (134, 104), (134, 105), (134, 106), (134, 107), (134, 108), (134, 109), (134, 110), (134, 111), (134, 112), (134, 113), (134, 114), (134, 115), (134, 116), (134, 117), (134, 118), (134, 119), (134, 120), (134, 121), (134, 122), (134, 150), (134, 151), (134, 152), (134, 153), (134, 154), (134, 155), (134, 156), (134, 157), (134, 158), (134, 159), (134, 160), (134, 161), (134, 164), (134, 166), (135, 91), (135, 92), (135, 93), (135, 94), (135, 95), (135, 96), (135, 97), (135, 98), (135, 99), (135, 100), (135, 101), (135, 102), (135, 103), (135, 104), (135, 105), (135, 106), (135, 107), (135, 108), (135, 109), (135, 110), (135, 111), (135, 112), (135, 113), (135, 114), (135, 115), (135, 116), (135, 117), (135, 118), (135, 119), (135, 120), (135, 121), (135, 122), (135, 123), (135, 124), (135, 150), (135, 151), (135, 152), (135, 153), (135, 154), (135, 155), (135, 156), (135, 157), (135, 158), (135, 159), (135, 160), (135, 161), (135, 164), (135, 166), (135, 167), (136, 95), (136, 96), (136, 97), (136, 98), (136, 99), (136, 100), (136, 101), (136, 102), (136, 103), (136, 104), (136, 105), (136, 106), (136, 107), (136, 108), (136, 109), (136, 110), (136, 111), (136, 112), (136, 113), (136, 114), (136, 115), (136, 116), (136, 117), (136, 118), (136, 119), (136, 120), (136, 121), (136, 122), (136, 123), (136, 124), (136, 150), (136, 151), (136, 152), (136, 153), (136, 154), (136, 155), (136, 156), (136, 157), (136, 158), (136, 159), (136, 160), (136, 161), (136, 162), (136, 164), (136, 167), (137, 96), (137, 97), (137, 101), (137, 102), (137, 103), (137, 104), (137, 105), (137, 106), (137, 107), (137, 108), (137, 109), (137, 110), (137, 111), (137, 112), (137, 113), (137, 114), (137, 115), (137, 116), (137, 117), (137, 118), (137, 119), (137, 120), (137, 121), (137, 122), (137, 123), (137, 124), (137, 125), (137, 152), (137, 153), (137, 154), (137, 155), (137, 156), (137, 157), (137, 158), (137, 159), (137, 160), (137, 161), (137, 162), (137, 164), (137, 165), (137, 167), (138, 96), (138, 97), (138, 98), (138, 99), (138, 100), (138, 101), (138, 102), (138, 103), (138, 104), (138, 105), (138, 106), (138, 107), (138, 108), (138, 109), (138, 110), (138, 111), (138, 112), (138, 113), (138, 114), (138, 115), (138, 116), (138, 117), (138, 118), (138, 119), (138, 120), (138, 121), (138, 122), (138, 123), (138, 124), (138, 125), (138, 126), (138, 127), (138, 152), (138, 153), (138, 154), (138, 155), (138, 156), (138, 157), (138, 158), (138, 159), (138, 160), (138, 161), (138, 162), (138, 163), (138, 164), (138, 165), (138, 166), (139, 97), (139, 100), (139, 101), (139, 102), (139, 103), (139, 104), (139, 105), (139, 106), (139, 107), (139, 108), (139, 109), (139, 110), (139, 111), (139, 112), (139, 113), (139, 114), (139, 115), (139, 116), (139, 117), (139, 118), (139, 119), (139, 120), (139, 121), (139, 122), (139, 123), (139, 124), (139, 125), (139, 126), (139, 127), (139, 128), (139, 129), (139, 130), (139, 152), (139, 153), (139, 154), (139, 155), (139, 156), (139, 157), (139, 158), (139, 159), (139, 160), (139, 161), (139, 162), (139, 165), (140, 97), (140, 98), (140, 99), (140, 102), (140, 103), (140, 104), (140, 105), (140, 106), (140, 107), (140, 108), (140, 109), (140, 110), (140, 111), (140, 112), (140, 113), (140, 114), (140, 115), (140, 116), (140, 117), (140, 118), (140, 119), (140, 120), (140, 121), (140, 122), (140, 123), (140, 124), (140, 125), (140, 126), (140, 127), (140, 128), (140, 130), (140, 153), (140, 154), (140, 155), (140, 156), (140, 157), (140, 158), (140, 159), (140, 160), (140, 161), (140, 162), (140, 163), (140, 164), (140, 165), (141, 99), (141, 102), (141, 103), (141, 104), (141, 105), (141, 106), (141, 107), (141, 108), (141, 109), (141, 110), (141, 111), (141, 112), (141, 113), (141, 114), (141, 115), (141, 116), (141, 117), (141, 118), (141, 119), (141, 120), (141, 121), (141, 122), (141, 123), (141, 124), (141, 125), (141, 126), (141, 127), (141, 128), (141, 129), (141, 130), (141, 153), (141, 154), (141, 155), (141, 156), (141, 157), (141, 158), (141, 159), (141, 160), (141, 161), (141, 162), (141, 163), (141, 165), (142, 99), (142, 100), (142, 101), (142, 102), (142, 103), (142, 104), (142, 105), (142, 108), (142, 109), (142, 110), (142, 111), (142, 112), (142, 113), (142, 114), (142, 115), (142, 116), (142, 117), (142, 118), (142, 119), (142, 120), (142, 121), (142, 122), (142, 123), (142, 124), (142, 125), (142, 126), (142, 127), (142, 128), (142, 129), (142, 130), (142, 153), (142, 154), (142, 155), (142, 156), (142, 157), (142, 158), (142, 159), (142, 160), (142, 161), (142, 162), (142, 163), (142, 164), (142, 165), (142, 166), (143, 103), (143, 104), (143, 105), (143, 106), (143, 107), (143, 108), (143, 109), (143, 110), (143, 111), (143, 112), (143, 113), (143, 114), (143, 115), (143, 116), (143, 117), (143, 118), (143, 119), (143, 120), (143, 121), (143, 122), (143, 123), (143, 124), (143, 125), (143, 126), (143, 127), (143, 128), (143, 129), (143, 130), (143, 131), (143, 154), (143, 155), (143, 157), (143, 158), (143, 159), (143, 160), (143, 161), (143, 162), (143, 163), (143, 166), (144, 103), (144, 104), (144, 105), (144, 106), (144, 107), (144, 108), (144, 109), (144, 110), (144, 111), (144, 112), (144, 113), (144, 114), (144, 115), (144, 116), (144, 117), (144, 118), (144, 119), (144, 120), (144, 121), (144, 122), (144, 123), (144, 124), (144, 125), (144, 126), (144, 127), (144, 128), (144, 129), (144, 130), (144, 131), (144, 132), (144, 154), (144, 155), (144, 156), (144, 158), (144, 159), (144, 160), (144, 161), (144, 162), (144, 163), (144, 164), (144, 165), (144, 166), (145, 105), (145, 108), (145, 109), (145, 110), (145, 111), (145, 112), (145, 113), (145, 114), (145, 115), (145, 116), (145, 117), (145, 118), (145, 119), (145, 120), (145, 121), (145, 122), (145, 123), (145, 124), (145, 125), (145, 126), (145, 127), (145, 128), (145, 129), (145, 131), (145, 132), (145, 154), (145, 155), (145, 156), (145, 158), (145, 159), (145, 161), (145, 162), (145, 163), (145, 164), (145, 166), (146, 105), (146, 108), (146, 109), (146, 110), (146, 111), (146, 112), (146, 113), (146, 114), (146, 115), (146, 116), (146, 117), (146, 118), (146, 119), (146, 120), (146, 121), (146, 122), (146, 123), (146, 124), (146, 125), (146, 126), (146, 127), (146, 128), (146, 129), (146, 130), (146, 131), (146, 132), (146, 133), (146, 154), (146, 155), (146, 156), (146, 158), (146, 159), (146, 161), (146, 166), (146, 167), (147, 105), (147, 113), (147, 114), (147, 115), (147, 116), (147, 117), (147, 118), (147, 119), (147, 120), (147, 121), (147, 122), (147, 123), (147, 124), (147, 125), (147, 126), (147, 127), (147, 128), (147, 129), (147, 130), (147, 131), (147, 132), (147, 133), (147, 134), (147, 135), (147, 155), (147, 156), (147, 159), (147, 161), (147, 167), (147, 168), (148, 105), (148, 113), (148, 114), (148, 115), (148, 116), (148, 117), (148, 118), (148, 119), (148, 120), (148, 121), (148, 122), (148, 123), (148, 124), (148, 125), (148, 126), (148, 127), (148, 128), (148, 129), (148, 130), (148, 131), (148, 132), (148, 133), (148, 134), (148, 135), (148, 136), (148, 155), (148, 156), (148, 157), (148, 159), (148, 161), (148, 162), (148, 168), (149, 105), (149, 106), (149, 115), (149, 116), (149, 117), (149, 118), (149, 119), (149, 120), (149, 121), (149, 122), (149, 123), (149, 124), (149, 125), (149, 126), (149, 127), (149, 128), (149, 129), (149, 130), (149, 131), (149, 132), (149, 133), (149, 134), (149, 135), (149, 136), (149, 137), (149, 157), (149, 159), (149, 162), (150, 106), (150, 117), (150, 118), (150, 119), (150, 120), (150, 121), (150, 122), (150, 123), (150, 124), (150, 125), (150, 126), (150, 127), (150, 128), (150, 129), (150, 130), (150, 131), (150, 132), (150, 133), (150, 134), (150, 135), (150, 136), (150, 137), (150, 138), (150, 157), (150, 158), (150, 159), (150, 162), (151, 106), (151, 107), (151, 108), (151, 109), (151, 110), (151, 111), (151, 119), (151, 120), (151, 121), (151, 122), (151, 123), (151, 124), (151, 125), (151, 126), (151, 127), (151, 128), (151, 129), (151, 130), (151, 131), (151, 132), (151, 133), (151, 134), (151, 135), (151, 136), (151, 137), (151, 138), (151, 139), (151, 158), (151, 162), (152, 111), (152, 112), (152, 113), (152, 114), (152, 115), (152, 116), (152, 120), (152, 121), (152, 122), (152, 123), (152, 124), (152, 125), (152, 126), (152, 127), (152, 128), (152, 129), (152, 130), (152, 131), (152, 132), (152, 133), (152, 134), (152, 135), (152, 136), (152, 137), (152, 138), (152, 139), (152, 140), (152, 141), (152, 142), (152, 143), (152, 144), (152, 162), (153, 116), (153, 117), (153, 118), (153, 119), (153, 120), (153, 121), (153, 122), (153, 123), (153, 124), (153, 125), (153, 126), (153, 127), (153, 128), (153, 129), (153, 130), (153, 131), (153, 132), (153, 133), (153, 134), (153, 135), (153, 136), (153, 137), (153, 138), (153, 139), (153, 140), (153, 141), (153, 142), (153, 143), (153, 144), (153, 145), (153, 162), (154, 121), (154, 122), (154, 123), (154, 124), (154, 125), (154, 126), (154, 127), (154, 128), (154, 129), (154, 130), (154, 131), (154, 132), (154, 133), (154, 134), (154, 135), (154, 136), (154, 137), (154, 138), (154, 139), (154, 140), (154, 141), (154, 142), (154, 143), (154, 144), (154, 145), (154, 146), (154, 147), (154, 148), (155, 122), (155, 123), (155, 124), (155, 125), (155, 126), (155, 127), (155, 128), (155, 129), (155, 130), (155, 131), (155, 132), (155, 133), (155, 134), (155, 135), (155, 136), (155, 137), (155, 138), (155, 139), (155, 140), (155, 141), (155, 142), (155, 143), (155, 144), (155, 145), (155, 146), (155, 147), (155, 148), (155, 149), (156, 122), (156, 124), (156, 125), (156, 126), (156, 127), (156, 128), (156, 129), (156, 130), (156, 131), (156, 132), (156, 133), (156, 134), (156, 135), (156, 136), (156, 137), (156, 138), (156, 139), (156, 140), (156, 141), (156, 142), (156, 143), (156, 144), (156, 145), (156, 146), (156, 147), (156, 148), (157, 122), (157, 123), (157, 125), (157, 126), (157, 127), (157, 128), (157, 129), (157, 130), (157, 131), (157, 132), (157, 133), (157, 134), (157, 135), (157, 136), (157, 137), (157, 138), (157, 139), (157, 140), (157, 141), (157, 142), (157, 143), (157, 144), (157, 145), (157, 146), (157, 147), (158, 123), (158, 124), (158, 125), (158, 126), (158, 127), (158, 128), (158, 129), (158, 130), (158, 131), (158, 132), (158, 133), (158, 134), (158, 135), (158, 136), (158, 137), (158, 138), (158, 139), (158, 140), (158, 141), (158, 142), (158, 143), (158, 144), (158, 145), (158, 146), (158, 147), (159, 125), (159, 126), (159, 127), (159, 128), (159, 129), (159, 130), (159, 131), (159, 132), (159, 133), (159, 134), (159, 135), (159, 136), (159, 137), (159, 138), (159, 139), (159, 140), (159, 141), (159, 142), (159, 143), (159, 144), (159, 145), (159, 146), (159, 147), (159, 148), (159, 149), (159, 150), (159, 151), (160, 125), (160, 126), (160, 130), (160, 132), (160, 133), (160, 134), (160, 135), (160, 136), (160, 137), (160, 138), (160, 139), (160, 140), (160, 141), (160, 142), (160, 143), (160, 144), (160, 145), (160, 146), (160, 147), (160, 148), (160, 149), (160, 150), (160, 151), (160, 152), (160, 153), (160, 154), (160, 155), (161, 125), (161, 126), (161, 127), (161, 130), (161, 131), (161, 132), (161, 133), (161, 134), (161, 135), (161, 136), (161, 137), (161, 138), (161, 139), (161, 140), (161, 141), (161, 142), (161, 143), (161, 144), (161, 145), (161, 146), (161, 147), (161, 148), (161, 149), (161, 150), (161, 152), (161, 153), (161, 154), (161, 155), (162, 126), (162, 127), (162, 134), (162, 135), (162, 136), (162, 137), (162, 138), (162, 139), (162, 140), (162, 141), (162, 142), (162, 143), (162, 144), (162, 146), (162, 147), (162, 148), (162, 149), (162, 150), (162, 151), (162, 152), (162, 153), (162, 154), (163, 126), (163, 127), (163, 137), (163, 138), (163, 139), (163, 140), (163, 141), (163, 142), (163, 144), (163, 147), (163, 148), (163, 149), (163, 150), (163, 151), (163, 152), (164, 126), (164, 127), (164, 138), (164, 139), (164, 140), (164, 142), (164, 143), (164, 144), (164, 145), (164, 148), (164, 152), (164, 153), (164, 154), (164, 155), (165, 126), (165, 127), (165, 143), (165, 144), (165, 145), (165, 146), (165, 148), (166, 126), (166, 127), (166, 128), (166, 146), (166, 147), (166, 148), (166, 149), (166, 150), (167, 127), (167, 128), (167, 129), (167, 130), (167, 148), (167, 149), (168, 127), (168, 130), (168, 131), (168, 132), (168, 133), (168, 134), (168, 135), (168, 149), (169, 127), (169, 135), (169, 149), (170, 127), (170, 149), (170, 150), (170, 151), (170, 152), (170, 153), (170, 154), (171, 127), (171, 128), (172, 128), (172, 129), (172, 130), (172, 131), (172, 132)    
         """
        pat = re.compile(r"\((\d+),\s*(\d+)\)")
        allowed = {(int(x), int(y)) for x, y in pat.findall(block_str)}
        for x in range(n):
            for y in range(n - x):
                if (x, y) not in allowed:
                    #print(f"({x},{y})")
                    add_clause(-v[x][y])
        #print("\n")

    out_log_file.write(f"numVars: {var_cnt}, numClauses: {num_clauses}, numCardClauses: {num_card_clauses}\n")
    # Write KNF dimacs file
    f = open(f'{result_folder_path}/{knf_dimacs_filename}', "w+")
    f.write(f"p knf {num_vars} {num_clauses}\n")
    for lines in dimacs_buffer:
        f.write(lines + "\n")
    f.flush()
    f.close()
    time.sleep(1) 
    print("dimacsFile created: ", time.time() - start_time, "seconds")

    # Optionally modify dimacs file further
    if not use_KNF or march_generate_cubes:
        knf2cnf()

    if march_generate_cubes:
        generate_icnf()
        print("cubes.icnf created: ", time.time() - start_time, "seconds")
    
    if use_hybrid:
        konly()
        generate_hybrid_dimacs()
        print("full.knf created: ", time.time() - start_time, "seconds")

    out_log_file.close()


if __name__ == "__main__":
    main()