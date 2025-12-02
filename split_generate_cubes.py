import os
import argparse
import re

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", required=True, help="source/output folder")
    parser.add_argument("-n", required=True, type=int, help="n")
    parser.add_argument("-i", default="", help="cubes source file to branch on")
    parser.add_argument("-o", required=True, help="output cubes file name")
    parser.add_argument("-m", default=1, type=int, help="numerator in line y = floor((m/d)n) - x")
    parser.add_argument("-d", default=1, type=int, help="denominator in line y = floor((m/d)n) - x")
    parser.add_argument("-fx", type=int, default=None, help="optional final x for reachability check")
    parser.add_argument("-fy", type=int, default=None, help="optional final y for reachability check")
    return vars(parser.parse_args())

args = parse_arguments()

results_folder = args["r"]
cubes_src_filename = args["i"]
cubes_dest_filename = args["o"]
n = args["n"]
m = args["m"]
d = args["d"]
fx = args["fx"]
fy = args["fy"]

if (fx is None) != (fy is None):
    print("invalid final point")
    exit(-1)

if d < 0 or m < 0:
    print("invalid m or d")
    exit(-1)

line_pos = (m * n) // d
print(f"Creating cubes on the line y = {line_pos} - x. (floor[{m}/{d}]*{n})")

if fx is not None and fy is not None:
    print(f"Using final point ({fx},{fy})")
else:
    print("No final point given")

cwd_path = os.getcwd()
results_folder_path = os.path.join(cwd_path, f"output/{results_folder}")

cubes_src_path  = os.path.join(results_folder_path, cubes_src_filename) if cubes_src_filename else ""
cubes_dest_path = os.path.join(results_folder_path, cubes_dest_filename)
if os.path.exists(cubes_dest_path):
    print(f"Error: dest cube file already exists: {cubes_dest_path}")
    exit(-1)

src_cubes = []

init_cube_cnt = 0
final_cube_cnt = 0

var_cnt = 1
v = [[0 for _ in range(n)] for _ in range(n)]
v_map = {}
for b in range(n):
    for x in range(n):
        y = b - x
        if 0 <= y < n and x + y < n:
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
    if y < 0 or y >= n:
        return False
    if x < 0 or x >= n:
        return False
    if x + y >= n:
        return False

    for px, py in upper_pts:
        if x <= px and y >= py:
            return False
    for px, py in lower_pts:
        if x >= px and y <= py:
            return False
    return True

def upper_sym_bounds(dx, dy):
    if dx < 0 or dy < 0:
        return False
    for px, py in upper_pts:
        if dx <= px and dy >= py:
            return False
    for px, py in upper_pts:
        if dy <= px and dx >= py:
            return False
    return True

def upper_reflected_bounds_final(x, y):
    if fx is None or fy is None:
        return True
    dx = fx - x
    dy = fy - y
    return upper_sym_bounds(dx, dy)

# ensure point on new line can reach or be reached by the original points in the cube
def points_compatible(x1, y1, x2, y2):
    if x1 <= x2 and y1 <= y2:
        dx = x2 - x1
        dy = y2 - y1
        return upper_sym_bounds(dx, dy)
    if x2 <= x1 and y2 <= y1:
        dx = x1 - x2
        dy = y1 - y2
        return upper_sym_bounds(dx, dy)
    return False

def load_src_cubes():
    global init_cube_cnt
    if cubes_src_filename == "":
        return
    print(f"Opening cubes source file {cubes_src_path}")
    with open(cubes_src_path, "r") as cubes_src_file:
        for line in cubes_src_file:
            if line.startswith("a "):
                trim_line = line.split("a ")[1].split("# ")[0]
                cube = trim_line.rsplit(" ", 1)[0]
                src_cubes.append(cube)
                init_cube_cnt += 1
    print(f"Read {init_cube_cnt} cubes from {cubes_src_filename}.")

def create_line_cubes():
    global final_cube_cnt
    load_src_cubes()

    with open(cubes_dest_path, "w+") as cube_dest_file:
        line_points = []

        for x in range(n):
            y = line_pos - x

            if not upper_lower_bounds_origin(x, y):
                continue

            if not upper_reflected_bounds_final(x, y):
                continue

            if v[x][y] == 0:
                continue

            line_points.append((x, y))

        print(f"Number of valid points on line y = {line_pos} - x: {len(line_points)}")

        for (x_new, y_new) in line_points:
            if src_cubes:
                for src_cube in src_cubes:
                    lits = [int(tok) for tok in src_cube.split() if tok != "0"]

                    # check reachability of each point in cube with the new point 
                    compatible_with_all = True
                    for lit in lits:
                        vx, vy = v_map[abs(lit)]
                        if not points_compatible(x_new, y_new, vx, vy):
                            compatible_with_all = False
                            break

                    if not compatible_with_all:
                        continue

                    comment_parts = [f"# ({x_new},{y_new}) "]
                    cube_dest_file.write(f"a {v[x_new][y_new]} ")
                    for lit in lits:
                        cube_dest_file.write(f"{lit} ")
                        vx, vy = v_map[abs(lit)]
                        comment_parts.append(f"({vx}, {vy}) ")

                    cube_dest_file.write(f"0 {''.join(comment_parts)}\n")
                    final_cube_cnt +=1
            else:
                comment_str = f"# ({x_new},{y_new}) "
                cube_dest_file.write(f"a {v[x_new][y_new]} 0 {comment_str}\n")
                final_cube_cnt +=1

if __name__ == "__main__":
    create_line_cubes()
    print(f"Wrote {final_cube_cnt} cubes to {cubes_dest_filename}.")
