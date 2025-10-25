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
    parser.add_argument("--flip", default=0, help="flip the step sequence (0=steps off, 1=normal, 2=flipped)")
    parser.add_argument("--trim", default=0, help="trim the step sequence at both ends")
    
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

flip_steps=int(args["flip"])
trim_steps=int(args["trim"])

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



def encode_steps(): # from lex constraints
    global right_step

    for i in range(1, n):
        if right_step[i] == 0:
            right_step[i] = new_var()

    cells_per_step = [[] for _ in range(n)]
    for x in range(n):
        for y in range(n):
            step = x + y
            if step < n:
                cells_per_step[step].append((x, y))

    for i in range(1, n):
        r = right_step[i]
        for (x, y) in cells_per_step[i]:
            if x > 0:
                # (~v[x-1][y] or ~v[x][y] or  r)
                add_clause(-v[x-1][y], -v[x][y],  r)
                # (~r or ~v[x][y] or v[x-1][y])
                add_clause(-r,         -v[x][y],  v[x-1][y])
            if y > 0:
                # (~v[x][y-1] or ~v[x][y] or ~r)
                add_clause(-v[x][y-1], -v[x][y], -r)
                # ( r or ~v[x][y] or v[x][y-1])
                add_clause( r,         -v[x][y],  v[x][y-1])


def encode_step_sequence():
    if not flip_steps:
        return
    # Original (up=1, right=0):     "100100000111101111101110010001100100000100000100000100000100000100111101110010000010000010000010000010000010111101111101101111101110110001000001110010000010000010000010000010000010011111000"
    step_sequence = "100100000111101111101110010001100100000100000100000100000100000100111101110010000010000010000010000010000010111101111101101111101110110001000001110010000010000010000010000010000010011111000"

    if trim_steps:
        trimmed_step_sequence = step_sequence[trim_steps:-trim_steps]
    else:
        trimmed_step_sequence = step_sequence

    #trimmed_step_sequence = trimmed_step_sequence[::-1] 
    #print(f"encoding REVERSE step sequence: trim:{trim_steps}, orientation:{'regular' if flip_steps == 1 else 'flipped'}")
    #out_log_file.write(f"encoding REVERSE step sequence: trim:{trim_steps}, orientation:{'regular' if flip_steps == 1 else 'flipped'}\n")

    print(f"encoding FWD step sequence: trim:{trim_steps}, orientation:{'regular' if flip_steps == 1 else 'flipped'}")
    out_log_file.write(f"encoding FWD step sequence: trim:{trim_steps}, orientation:{'regular' if flip_steps == 1 else 'flipped'}\n")

    print(trimmed_step_sequence)
    steps = [c for c in trimmed_step_sequence.strip() if c in ('0','1')]
    num_steps = len(steps)
    total_steps = n - 1
    if num_steps == 0:
        return
    if num_steps > total_steps:
        print("invalid bit path")
        exit(-1)
    
    encode_steps()

    step_orientation = "0" if flip_steps == 1 else "1"  
    path_range = total_steps - num_steps + 1
    start_vars = []
    for start_step in range(1, path_range + 1):
        path_start_var = new_var()  
        start_vars.append(path_start_var)

        for j in range(num_steps):
            step_var = right_step[start_step + j] 
            if steps[j] == step_orientation:         
                add_clause(-path_start_var, step_var) # right (up=0, right=1; opposite of binary path format)
            else:
                add_clause(-path_start_var, -step_var) # up

    add_clause(*start_vars) # step sequence starts on at least one antidiagonal from y=0 to y=n-path_range-1

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

    encode_step_sequence() # for forcing the sequence of steps seen with n=323 and n=325 solutions

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