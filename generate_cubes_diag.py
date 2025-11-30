import os
import shutil
import argparse
import re

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", required=True, help="results folder containing the dimacsfile")
    parser.add_argument("-n", required=True, help="n")
    parser.add_argument("-s", required=True, help="create cubes for 1: CNF, 2: KNF file")
    parser.add_argument("-i", default="", help="cubes source file to branch on")
    parser.add_argument("-o", required=True, help="cubes dest file name")
    parser.add_argument("-fx", required=True, help="final x")
    parser.add_argument("-fy", required=True, help="final y")
    parser.add_argument("-t", required=True, help="t=1: split on n/3 and 2n/3; t=2: split on n/2; ")
    return vars(parser.parse_args())

args = parse_arguments()

results_folder = args["f"]
n = int(args["n"])
solver_type = int(args["s"])
cubes_src_filename = args["i"]
cubes_dest_filename = args["o"]
fx = int(args["fx"])
fy = int(args["fy"])
split_type = int(args["t"])

cwd_path = os.getcwd()
results_folder_path = os.path.join(cwd_path, f"output/{results_folder}")

cubes_src_path   = os.path.join(results_folder_path, cubes_src_filename)
cubes_dest_path  = os.path.join(results_folder_path, cubes_dest_filename)

template_file = ""
if solver_type == 1:
    template_file = "dimacsFile.cnf"
    print("Cubing with CNF files")
elif solver_type == 2:
    template_file = "dimacsFile.knf"
    print("Cubing with KNF files")
else:
    print("-s must be 1 (CNF) or 2 (KNF)")
    exit(-1)

template_file_path = os.path.join(results_folder_path, template_file)

src_cubes = []
dest_cubes = []

# variable map
var_cnt = 1
v = [[0 for _ in range(n)] for _ in range(n)]
v_map = {}
for x in range(n):
    for y in range(n):
        if x + y < n:
            v[x][y] = var_cnt
            v_map[var_cnt] = (x, y)
            var_cnt += 1

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

pat = r'\((\d+),\s*(\d+)\)'
upper_pts = [(int(a), int(b)) for (a, b) in re.findall(pat, points_k7_upper_bounds)]
lower_pts = [(int(a), int(b)) for (a, b) in re.findall(pat, points_k7_lower_bounds)]

def upper_lower_bounds_origin(x, y):
    if y < 0:
        return False
    if x < 0 or x >= n or y >= n:
        return False
    if x + y >= n:
        return False

    for px, py in upper_pts:
        if x <= px and y >= py:
            # print(f"({x},{y}), ", end="")
            return False
    for px, py in lower_pts:
        if x >= px and y <= py:
            # print(f"({x},{y}), ", end="")
            return False
    return True

def upper_sym_bounds(dx, dy):
    # dx,dy are the displacement from the starting point
    if dx < 0 or dy < 0:
        return False
    for px, py in upper_pts:
        if dx <= px and dy >= py:
            return False
    for px, py in upper_pts:
        if dy <= px and dx >= py:  # reflected
            return False
    return True

def upper_reflected_bounds_final(x, y):
    dx = fx - x
    dy = fy - y
    ok = upper_sym_bounds(dx, dy)
    # if not ok:
    #     print(f"({x},{y}), ", end="")
    return ok

def line1_line2_reachable(x1, y1, x2, y2):
    dx = x2 - x1  # get displacement so can compare against boundary points relative to (0,0)
    dy = y2 - y1
    return upper_sym_bounds(dx, dy)  # from point on line 1

# Create a cubed dimacs file: split on n/3 and 2n/3
def create_cubes_file():

    if cubes_src_filename != "": # not using for initial split
        cubes_src_file = open(cubes_src_path, "r")
        print(f"Opening clause file {cubes_src_path}")
        for line in cubes_src_file:
            if line.startswith('a '):
                trim_line = line.split('a ')[1].split('# ')[0]
                cube = trim_line.rsplit(' ', 1)[0]
                src_cubes.append(cube)

    cube_dest_file = open(cubes_dest_path, "w+")

    line_list_1 = []
    line_list_2 = []

    for x in range(n):
        y1 = (n // 3) - x
        y2 = (2 * n // 3) - x

        for y, which in ((y1, 1), (y2, 2)):
            if not upper_lower_bounds_origin(x, y):
                continue
            if not upper_reflected_bounds_final(x, y):
                continue

            if which == 1:
                line_list_1.append((x, y))
            else:
                line_list_2.append((x, y))

    line_pair_list = []
    for (x1, y1) in line_list_1:
        for (x2, y2) in line_list_2:
            if line1_line2_reachable(x1, y1, x2, y2):
                line_pair_list.append(((x1, y1), (x2, y2)))

    for (x1, y1), (x2, y2) in line_pair_list:
        if src_cubes:
            for src_cube in src_cubes:
                comment = []
                cube_dest_file.write(f"a {v[x1][y1]} {v[x2][y2]} ")
                comment.append(f"# ({x1},{y1}) ({x2},{y2}) ")

                for lit in src_cube.split():
                    cube_dest_file.write(f"{lit} ")
                    vx, vy = v_map[abs(int(lit))]
                    comment.append(f"({vx}, {vy}) ")

                cube_dest_file.write(f'0 {"".join(comment)}\n')
        else:
            comment_str = f"# ({x1},{y1}) ({x2},{y2}) "
            cube_dest_file.write(f"a {v[x1][y1]} {v[x2][y2]} 0 {comment_str}\n")

# Create a cubed dimacs file: split on n/2 using existing cubes as input (-i)
def create_cubes_file_2():

    if cubes_src_filename == "":
        print("Error: -i cubes source file is required for split_type=2")
        return

    print(f"Opening cubes source file {cubes_src_path}")
    with open(cubes_src_path, "r") as cubes_src_file, \
         open(cubes_dest_path, "w+") as cube_dest_file:

        for line in cubes_src_file:
            if not line.startswith("a "):
                continue

            parts = line.strip().split("#", 1)
            lhs = parts[0].strip()        
            rhs = parts[1] if len(parts) > 1 else ""

            tokens = lhs.split()
            lits = [int(tok) for tok in tokens[1:] if tok != "0"]

            coords = re.findall(r'\((\d+),\s*(\d+)\)', rhs)
            if len(coords) < 2:
                continue

            x1, y1 = map(int, coords[0])
            x2, y2 = map(int, coords[1])

            for xm in range(n):
                ym = (n // 2) - xm
                if ym < 0:
                    continue
                if xm < 0 or xm >= n or ym >= n:
                    continue
                if xm + ym >= n:
                    continue
                if v[xm][ym] == 0:
                    continue

                dx1 = xm - x1
                dy1 = ym - y1
                if not upper_sym_bounds(dx1, dy1):
                    continue

                dx2 = x2 - xm
                dy2 = y2 - ym
                if not upper_sym_bounds(dx2, dy2):
                    continue

                new_lits = lits + [v[xm][ym]]

                comment_str = f"# ({x1},{y1}) ({x2},{y2}) ({xm},{ym}) "
                cube_dest_file.write(
                    "a " + " ".join(str(l) for l in new_lits) + f" 0 {comment_str}\n"
                )

# Create a <num>_dimacsFile for each cube
def create_cubed_dimacs():
    cubes = []

    with open(cubes_dest_path) as cube_file:
        print(f"Opening cubes file {cubes_dest_path}")
        for line in cube_file:
            if line.startswith('a '):
                cubes.append(line.split('a ')[1].split('# ')[0].rsplit(' ', 1)[0])

    print(f"Number of cubes found: {len(cubes)}. Creating cubed dimacsFiles.")

    for i, cube in enumerate(cubes):
        dest = os.path.join(results_folder_path, f"{i}_{template_file}")

        shutil.copyfile(template_file_path, dest)

        with open(dest, 'a') as out:
            for lit in cube.split():
                if int(lit) != 0:
                    out.write(f"{lit} 0\n")

        lines = open(dest).read().splitlines()
        cnf_header   = lines[0].split()   # ["p","knf","<vars>","<clauses>"]
        original_clause_cnt = int(cnf_header[3])
        new_clause_cnt = original_clause_cnt + len(cube.split()) - 1
        lines[0] = f"{cnf_header[0]} {cnf_header[1]} {cnf_header[2]} {new_clause_cnt}"
        open(dest, 'w').write('\n'.join(lines))

if __name__ == "__main__":
    if split_type == 1:
        create_cubes_file()   # n/3 and 2n/3
    if split_type == 2:
        create_cubes_file_2() # n/2 using trimmed cube input file -i
    # create_cubed_dimacs()  # now streaming in place to avoid creating too many files
