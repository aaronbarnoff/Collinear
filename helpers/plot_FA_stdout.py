#!/usr/bin/env python3
import argparse
import os
import re
#import matplotlib
#matplotlib.use('Agg')

#import matplotlib.pyplot as plt
#import numpy as np
#from matplotlib.patches import Rectangle

start_color = 0.125
var_cnt = 1

def parse_arguments():
    p = argparse.ArgumentParser()
    p.add_argument("-f", required=True)
    p.add_argument("-i", required=True)
    return vars(p.parse_args())

def get_n_value(folder_name):
    m = re.search(r"n(\d+)", folder_name)
    if m:
        return int(m.group(1))
    mx = re.search(r"x(\d+)", folder_name)
    my = re.search(r"y(\d+)", folder_name)
    return int(mx.group(1)) + int(my.group(1)) + 1

def get_xy(folder_name):
    mx = re.search(r"x(\d+)", folder_name)
    my = re.search(r"y(\d+)", folder_name)
    fx = int(mx.group(1)) if mx else None
    fy = int(my.group(1)) if my else None
    return fx, fy

def build_var_map(n):
    global var_cnt
    var_map = {}
    for b in range(n):
        for x in range(n):
            y = b - x
            if 0 <= y < n and x + y < n:
                var_map[var_cnt] = (x, y)
                var_cnt += 1
    return var_map

def plot_path(FA_file, n, fx=None, fy=None):

    k7_upper_bounds = """
    (0, 6), (1, 11), (2, 16), (3, 21), (4, 26), (5, 31), (6, 30), (7, 33), (8, 37), (9, 41), (10, 44), (11, 45), (12, 47), (13, 49), (14, 52), (15, 55), (16, 58), (17, 60), (18, 63), (19, 65), (20, 67), (21, 69), (22, 70), (23, 71), (24, 73), (25, 75), (26, 78), (27, 80), (28, 82), (29, 83), (30, 86), (31, 86), (32, 88), (33, 88), (34, 89), (35, 91), (36, 92), (37, 91), (38, 90), (39, 91), (40, 93), (41, 95), (42, 97), (43, 99), (44, 101), (45, 102), (46, 104), (47, 106), (48, 108), (49, 109), (50, 111), (51, 113), (52, 115), (53, 117), (54, 119), (55, 121), (56, 123), (57, 125), (58, 126), (59, 128), (60, 130), (61, 131), (62, 133), (63, 135), (64, 136), (65, 138), (66, 140), (67, 141), (68, 143), (69, 144), (70, 146), (71, 148), (72, 149), (73, 151), (74, 153), (75, 155), (76, 156), (77, 156), (78, 157), (79, 156), (80, 158), (81, 159), (82, 162), (83, 163), (84, 165), (85, 166), (86, 167), (87, 168), (88, 170), (89, 171)
    """
    k7_lower_bounds = """
    (1, 0), (6, 1), (11, 2), (16, 3), (21, 4), (26, 5), (30, 6), (30, 7), (33, 8), (37, 9), (41, 10), (43, 11), (45, 12), (45, 13), (48, 14), (51, 15), (54, 16), (57, 17), (59, 18), (62, 19), (64, 20), (66, 21), (67, 22), (69, 23), (71, 24), (73, 25), (75, 26), (78, 27), (79, 28), (82, 29), (83, 30), (86, 31), (86, 32), (88, 33), (88, 34), (89, 35), (89, 38), (89, 39), (90, 36), (90, 37), (90, 40), (92, 41), (94, 42), (96, 43), (98, 44), (100, 45), (102, 46), (104, 47), (105, 48), (107, 49), (109, 50), (111, 51), (112, 52), (115, 53), (116, 54), (118, 55), (120, 56), (122, 57), (124, 58), (126, 59), (127, 60), (129, 61), (131, 62), (132, 63), (134, 64), (136, 65), (137, 66), (139, 67), (141, 68), (142, 69), (144, 70), (145, 71), (147, 72), (149, 73), (151, 74), (153, 75), (154, 76), (154, 77), (155, 78), (156, 79), (156, 80), (158, 81), (159, 82), (160, 83), (162, 84), (165, 85), (165, 86), (166, 87), (168, 88), (169, 89), (171, 90), (172, 91), (174, 92)
    """

    ub_all = [(int(a), int(b)) for a, b in re.findall(r'\((\d+),\s*(\d+)\)', k7_upper_bounds)]
    lb_all = [(int(a), int(b)) for a, b in re.findall(r'\((\d+),\s*(\d+)\)', k7_lower_bounds)]
    ub = [(x, y) for (x, y) in ub_all if x + y + 1 < n]
    lb = [(x, y) for (x, y) in lb_all if x + y + 1 < n]

    var_map = build_var_map(n)

    outdir = os.path.dirname(FA_file)
    with open(os.path.join(outdir, "var_to_xy.txt"), "w") as m:
        for v,(x,y) in var_map.items():
            m.write(f"{v}=({x},{y})\n")

    seen_lits = set()
    FA_list = []
    m = open(os.path.join(outdir, "var_to_xy.txt"), "a")
    m.write(f"plot: \n")
    with open(FA_file, 'r') as f:
        for line in f:
            if not line.startswith('z'): # z <lit> <#conflicts>
                continue
            toks = line.split()
            v = int(toks[1])
            conflicts = int(toks[2]) if len(toks) > 2 else 0
            if abs(v) > var_cnt:
                continue
            if v in seen_lits:
                continue
            seen_lits.add(v)
            xy = var_map.get(abs(v))
            if not xy:
                continue
            sign = 'pos' if v > 0 else 'neg'
            FA_list.append((sign, xy, v, conflicts))

    charmap=[[0 for x in range(n)] for y in range(n)]

    for i, (sign, xy, _, _) in enumerate(FA_list):
        if sign == 'neg':
            charmap[xy[0]][xy[1]] = ' '
        else:
            charmap[xy[0]][xy[1]] = '+'

    for (x, y) in ub: 
        if (x == fx and y == fy): 
            continue 
        charmap[x][y] = 'x'
    
    for (x, y) in lb: 
        if (x == fx and y == fy): 
            continue 
        charmap[x][y] = 'x'

    charmap[fx][fy] = 'e'
    charmap[0][0] = 's'

    for x in range(0,n):
        for y in range(0,n):
            if charmap[x][y] == 0:
                charmap[x][y] = '.'

    for y in range(n-1,-1,-1):
        for x in range(0,n):
            if x > fx:
                continue
            if y > fy:
                continue
            if x+y >= n:
                continue
            print(f"{charmap[x][y]}",end="")
            m.write(f"{charmap[x][y]}")
        print("")
        m.write(f"\n")

def main():
    args = parse_arguments()
    cwd_path = os.getcwd()
    parent = os.path.dirname(cwd_path)
    folder = args["f"]
    fa_file_name = args["i"]
    FA_file = os.path.join(parent, "output", folder, fa_file_name)
    n = get_n_value(folder)
    fx, fy = get_xy(folder)
    plot_path(FA_file, n, fx, fy)

if __name__ == '__main__':
    main()
