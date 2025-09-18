#!/usr/bin/env python3
import argparse
import os
import re
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap, BoundaryNorm

def parse_arguments():
    parser = argparse.ArgumentParser(description="e.g. python3 printSolution.py -k 6 -n 90 -f output/res_k6_n90_x0_y0_s1_c0_v1_a0_l0_b0.0_f0_r0_2025-09-18_17-43-04/satOutput_k.log")
    parser.add_argument("-f",  required=True, help="SAT log file location")
    parser.add_argument("-n",  required=True, type=int)
    parser.add_argument("-k",  required=True, type=int)
    return vars(parser.parse_args())

def define_vars(n, v):
    counter = 0
    for b in range(n):
        for x in range(n):
            y = b - x
            if 0 <= y < n:
                counter += 1
                v[x][y] = counter
    #print("max cubing var:", counter)

def read_vars(dimacs_file):
    varList = []
    with open(dimacs_file, 'r') as f:
        for line in f:
            if line.startswith('v '):
                lit_str = line.split('v ', 1)[1].rsplit(' ', 1)[0]
                for w in lit_str.split():
                    if int(w) > 0:
                        varList.append(int(w))
    return varList

def plot_combined(points, collinearList, n, k, dimacs_file):
    fig, ax = plt.subplots(figsize=(50, 50))
    ax.tick_params(axis='x', rotation=90)

    x_vals = np.linspace(-0.5, n - 0.5, 200)
    ax.plot(x_vals, n - x_vals, color='gray', linestyle='--', linewidth=1)
    ax.plot(x_vals, x_vals + 1, color='gray', linestyle='--', linewidth=1)

    Z = np.zeros((n, n), dtype=np.int16)
    Z = np.ma.array(Z, mask=np.fromfunction(lambda yy, xx: (xx + yy) >= n, (n, n), dtype=int))

    used_max_x = -1
    used_max_y = -1
    def bump_bounds(x, y):
        nonlocal used_max_x, used_max_y
        if x > used_max_x: used_max_x = x
        if y > used_max_y: used_max_y = y

    def set_cell(x, y, code):
        if 0 <= x < n and 0 <= y < n and (x + y) < n:
            if code >= Z[y, x]:
                Z[y, x] = code
            bump_bounds(x, y)

    for x in range(n):
        y0, cnt = (k - 2) * x + (k - 1), 0
        while y0 < n - x and cnt < k:
            set_cell(x, y0, 2); y0 += 1; cnt += 1
    for y in range(n):
        x0, cnt = (k - 2) * y + 1, 0
        while x0 < n - y and cnt < k:
            set_cell(x0, y, 2); x0 += 1; cnt += 1

    for (px, py) in points:
        set_cell(px, py, 1)

    points_stringk7uplow = """
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
    (89,171)
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
    points_stringk6uplow = """
    (0,5),(1,9),(2,13),(3,17),(4,21),(5,20),(6,22),(7,24),
    (8,26),(9,28),(10,29),(11,29),(12,31),(13,33),(14,35),
    (15,36),(16,38),(17,39),(18,41),(19,41),(20,42),(21,43),
    (22,45),(23,46),(24,48),(25,49),(26,51),(27,53),(28,55),
    (29,56),(30,57),(31,55),(32,57),(33,57),(34,59),(35,59),
    (36,57),(37,58),(38,58),(39,57)
    (1,0),(5,1),(9,2),(13,3),(17,4),(20,5),(20,6),(22,7),
    (24,8),(26,9),(27,10),(27,11),(28,12),(30,13),(32,14),
    (34,15),(36,16),(37,17),(38,18),(39,19),(40,20),(41,21),
    (42,22),(44,23),(45,24),(47,25),(49,26),(51,27),(52,28),
    (54,29),(55,30),(55,31),(55,32),(56,33),(56,34),(59,35),
    (57,36),(57,37),(57,38),(57,39),(58,36),
    """

    pts_src = points_stringk7uplow if k == 7 else points_stringk6uplow
    for x_str, y_str in re.findall(r'\((\d+),\s*(\d+)\)', pts_src):
        x2, y2 = int(x_str), int(y_str)
        set_cell(x2, y2, 3)

    edges = np.arange(-0.5, n + 0.5, 1)
    cmap = ListedColormap(['white', 'blue', 'grey', 'black'])
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], cmap.N)
    mesh = ax.pcolormesh(edges, edges, Z, cmap=cmap, norm=norm, shading='flat')
    mesh.set_rasterized(False)  # keep vector in PDF

    for gline in edges:
        ax.axvline(gline, color='black', linestyle='-', linewidth=0.25)
        ax.axhline(gline, color='black', linestyle='-', linewidth=0.25)

    if len(points) >= 2:
        xs = [p[0] for p in points]; ys = [p[1] for p in points]
        ax.plot(xs, ys, color='b', linestyle='-', linewidth=1.5)
        for x, y in zip(xs, ys):
            bump_bounds(x, y)
    for px, py in points:
        ax.plot(px, py, marker='o', markersize=5, color='b')
        bump_bounds(px, py)

    for lst in collinearList:
        (x1, y1), (x2, y2) = lst[0], lst[1]
        if (x2 - x1) and (y2 - y1) != 0:
            ax.axline(lst[0], slope=(y2 - y1) / (x2 - x1), linestyle='--', linewidth=0.5, color='red')
        elif (y2 - y1) == 0:
            ax.axhline(y1, linestyle='--', linewidth=0.5, color='purple')
        elif (x2 - x1) == 0:
            ax.axvline(x1, linestyle='--', linewidth=0.5, color='purple')

    if used_max_x >= 0 and used_max_y >= 0:
        ax.set_xlim(-0.5, min(n - 0.5, used_max_x + 1.5))
        ax.set_ylim(-0.5, min(n - 0.5, used_max_y + 1.5))
    else:
        ax.set_xlim(-0.5, n - 0.5)
        ax.set_ylim(-0.5, n - 0.5)

    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_aspect('equal')
    ax.set_title('Combined Cubes', fontsize=16)

    outdir = os.path.dirname(dimacs_file)
    stem = os.path.splitext(os.path.basename(dimacs_file))[0]
    pdf_path = os.path.join(outdir, f"solution_plot_{stem}.pdf")
    fig.savefig(pdf_path, bbox_inches='tight')
    # png_path = os.path.join(outdir, f"solution_plot_{stem}.png")
    # fig.savefig(png_path, bbox_inches='tight', dpi=300)
    plt.close(fig)
    print(f"Saved {pdf_path}")

def extractModel(v, n, k, logFileN):
    with open(logFileN, 'r') as logFile:
        lines = logFile.readlines()

    model = []
    for line in lines:
        if line.startswith('v '):
            numbers = list(map(int, line[2:].strip().split()))
            model.extend([num for num in numbers if num > 0])

    pointList = []
    for x in range(n):
        for y in range(n):
            if y < n - x:
                if v[x][y] in model:
                    pointList.append((x, y))
    return pointList

def checkCollinearK(n, k, pointList):
    collinearList = []
    S = set(pointList)
    for (x1, y1) in pointList:
        for (x2, y2) in pointList:
            if (x1, y1) == (x2, y2):
                continue
            if (x2 < x1) or (y2 < y1):
                continue
            m_p = x2 - x1
            m_q = y2 - y1
            tmpPointsList = [(x1, y1), (x2, y2)]
            count = 2
            x, y = x2, y2
            while (x < n) and (y < n - x):
                x += m_p
                y += m_q
                if (x, y) in S:
                    count += 1
                    tmpPointsList.append((x, y))
            if count >= k:
                collinearList.append(tmpPointsList)

    if collinearList:
        print(f"Failure: {k} or more points found on the same line.")
        for line in collinearList:
            (a1, b1) = line[0]
            (a2, b2) = line[1]
            if (a2 - a1) == 0:
                print('vline. points: ', end="")
            elif (b2 - b1) == 0:
                print('hline. points: ', end="")
            else:
                print(f'slope: {((b2 - b1) / (a2 - a1)):.2g}; m_p: {(b2 - b1)}, m_q: {(a2 - a1)}; points: ', end="")
            for pt in line:
                (x, y) = pt
                print(f'({x},{y}) ', end="")
            print("")
    return collinearList

def main():
    args = parse_arguments()
    dimacs_file = args["f"]
    n = int(args["n"])
    k = int(args["k"])
    if not os.path.isfile(dimacs_file):
        raise FileNotFoundError(f"Could not find '{dimacs_file}'")
    v = [[0 for _ in range(n)] for _ in range(n)]
    define_vars(n, v)

    pointsList = extractModel(v, n, k, dimacs_file)
    collinearList = checkCollinearK(n, k, pointsList)
    plot_combined(pointsList, collinearList, n, k, dimacs_file)

if __name__ == '__main__':
    main()
