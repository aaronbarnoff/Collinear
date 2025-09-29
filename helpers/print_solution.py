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


def plot_solution(points, collinear_list, n, k, dimacs_file):
    fig, ax = plt.subplots(figsize=(50, 50))
    ax.tick_params(axis="x", rotation=90)

    x_vals = np.linspace(-0.5, n - 0.5, 200)
    ax.plot(x_vals, n - x_vals, color="gray", linestyle="--", linewidth=1)
    ax.plot(x_vals, x_vals + 1, color="gray", linestyle="--", linewidth=1)

    used_max_x = -1
    used_max_y = -1

    for (x, y) in points:
        ax.add_patch(plt.Rectangle((x - 0.5, y - 0.5), 1, 1, facecolor="black", edgecolor="none"))
        if x > used_max_x: used_max_x = x
        if y > used_max_y: used_max_y = y

    #for bx, by in [(14, 15), (15, 14)]:
    #    ax.add_patch(plt.Rectangle((bx - 0.5, by - 0.5), 1, 1, facecolor="blue", edgecolor="none"))
    #    if bx > used_max_x: used_max_x = bx
    #    if by > used_max_y: used_max_y = by

    for gline in range(n + 1):
        ax.axvline(gline - 0.5, color="lightgrey", linestyle="--", linewidth=0.125)
        ax.axhline(gline - 0.5, color="lightgrey", linestyle="--", linewidth=0.125)

    for lst in collinear_list:
        (x1, y1), (x2, y2) = lst[0], lst[1]
        if (x2 - x1) and (y2 - y1) != 0:
            ax.axline(lst[0], slope=(y2 - y1) / (x2 - x1), linestyle="--", linewidth=3, color="red")
        elif (y2 - y1) == 0:
            ax.axhline(y1, linestyle="--", linewidth=3, color="red")
        elif (x2 - x1) == 0:
            ax.axvline(x1, linestyle="--", linewidth=3, color="red")

    col_pts = {pt for line in collinear_list for pt in line}
    for (cx, cy) in col_pts:
        ax.plot(cx, cy, marker='o', markersize=12, color='red', zorder=5)

    font_size = 18
    xmax = (used_max_x if used_max_x >= 0 else n - 1)
    ymax = (used_max_y if used_max_y >= 0 else n - 1)

    import matplotlib as mpl
    mpl.rcParams['xtick.labelsize'] = font_size
    mpl.rcParams['ytick.labelsize'] = font_size

    ax.set_xlim(-0.5, xmax + 1.5)
    ax.set_ylim(-0.5, ymax + 1.5)
    ax.set_xticks(range(xmax + 2))
    ax.set_yticks(range(ymax + 2))

    # now apply fontsize once
    ax.tick_params(axis="both", which="major", labelsize=font_size)

    outdir = os.path.dirname(dimacs_file)
    stem = os.path.splitext(os.path.basename(dimacs_file))[0]
    pdf_path = os.path.join(outdir, f"solution_plot_{stem}.pdf")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {pdf_path}")


def extract_solution(v, n, k, sat_log_file_path):
    with open(sat_log_file_path, 'r') as log_file:
        lines = log_file.readlines()

    model = []
    for line in lines:
        if line.startswith('v '):
            numbers = list(map(int, line[2:].strip().split()))
            model.extend([num for num in numbers if num > 0])

    points_list = []
    for x in range(n):
        for y in range(n):
            if y < n - x:
                if v[x][y] in model:
                    points_list.append((x, y))
    return points_list


def verify_solution(n, k, points_list):
    collinear_list = []
    S = set(points_list)
    for (x1, y1) in points_list:
        for (x2, y2) in points_list:
            if (x1, y1) == (x2, y2):
                continue
            if (x2 < x1) or (y2 < y1):
                continue
            m_p = x2 - x1
            m_q = y2 - y1
            tmp_points_list = [(x1, y1), (x2, y2)]
            count = 2
            x, y = x2, y2
            while (x < n) and (y < n - x):
                x += m_p
                y += m_q
                if (x, y) in S:
                    count += 1
                    tmp_points_list.append((x, y))
            if count >= k:
                collinear_list.append(tmp_points_list)

    if collinear_list:
        print(f"Failure: {k} or more points found on the same line.")
        for line in collinear_list:
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
    return collinear_list


def main():
    args = parse_arguments()
    dimacs_file = args["f"]
    n = int(args["n"])
    k = int(args["k"])
    if not os.path.isfile(dimacs_file):
        raise FileNotFoundError(f"Could not find '{dimacs_file}'")
    v = [[0 for _ in range(n)] for _ in range(n)]
    define_vars(n, v)

    points_list = extract_solution(v, n, k, dimacs_file)
    #points_list.append((15,14))
    #points_list.append((14,15))
    collinear_list = verify_solution(n, k, points_list)
    plot_solution(points_list, collinear_list, n, k, dimacs_file)

if __name__ == '__main__':
    main()
