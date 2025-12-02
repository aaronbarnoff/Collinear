#!/usr/bin/env python3
import argparse
import os
import re

start_color = 0.125
var_cnt = 1

def parse_arguments():
    p = argparse.ArgumentParser()
    p.add_argument("-f", required=True,                     help="results folder name in output directory")
    p.add_argument("-i", default="fixed_assignments.txt",   help="fixed assignments file name")
    p.add_argument("-p", type=int, default=0,               help="p=0 plot to stdout; p=1 matplotlib pdf")
    return vars(p.parse_args())

args = parse_arguments()
folder = args["f"]
fa_file_name = args["i"]
print_pdf = args["p"]

cwd_path = os.getcwd()
parent = os.path.dirname(cwd_path)
FA_file = os.path.join(parent, "output", folder, fa_file_name)


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


def build_boundary_set(n):
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
    return lb, ub


def build_FA_list(var_map):
    seen_lits = set()
    FA_list = []
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
    return FA_list
    

def plot_path_pdf(FA_file, n, fx=None, fy=None):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.patches import Rectangle

    outdir = os.path.dirname(FA_file)
    pdf_path = os.path.join(outdir, f'FA_plot.pdf')
    var_path = os.path.join(outdir, f'var_map.txt')

    def draw_cell(ax, x, y, face, z=0, alpha=1.0):
        ax.add_patch(Rectangle((x, y), 1.0, 1.0,
                            facecolor=face, edgecolor='none',
                            zorder=z, alpha=alpha))

    def draw_cell_inner_outline(ax, x, y, edge='black', lw=0.8, inset=0.08, z=0):
        ax.add_patch(Rectangle((x + inset, y + inset),
                            1.0 - 2*inset, 1.0 - 2*inset,
                            facecolor='none', edgecolor=edge,
                            linewidth=lw, zorder=z))
        
    fig, ax = plt.subplots(figsize=(10, 10), dpi=300)
    ax.tick_params(axis='x', rotation=90)

    var_map = build_var_map(n)
    FA_list = build_FA_list(var_map)
    lb,ub = build_boundary_set(n)

    ymax_ub_list = [y for (_, y) in ub]
    xmax_lb_list = [x for (x, _) in lb]
    if fy is not None:
        ymax_ub_list.append(fy)
    if fx is not None:
        xmax_lb_list.append(fx)
    ymax_ub = max(ymax_ub_list) if ymax_ub_list else n - 1
    xmax_lb = max(xmax_lb_list) if xmax_lb_list else n - 1

    x_extent = xmax_lb + 1
    y_extent = ymax_ub + 1

    for xg in range(x_extent + 1):
        ax.axvline(xg, color='lightgrey', linestyle='--', linewidth=0.125, zorder=100)
    for yg in range(y_extent + 1):
        ax.axhline(yg, color='lightgrey', linestyle='--', linewidth=0.125, zorder=100)

    x_line_max = min(x_extent, y_extent - 1)
    if x_line_max > 0:
        x_vals_line = np.linspace(0, x_line_max, 200)
        ax.plot(x_vals_line, x_vals_line + 1, color='gray', linestyle='--', linewidth=0.25, zorder=100)

    cmap = plt.cm.viridis
    color_by_idx = {}

    if FA_list:
        conflicts = [c for (_, _, _, c) in FA_list]
        cmin = min(conflicts)
        cmax = max(conflicts)
        for i, (_, _, _, c) in enumerate(FA_list):
            if cmax == cmin:
                t = 0.0
            else:
                t = (c - cmin) / (cmax - cmin)
            color_by_idx[i] = cmap(t)

    for i, (sign, xy, _, _) in enumerate(FA_list):
        c = color_by_idx.get(i, cmap(0.0))
        if sign == 'neg':
            draw_cell(ax, xy[0], xy[1], c, z=2)
        else:
            draw_cell(ax, xy[0], xy[1], c, z=3)
            draw_cell_inner_outline(ax, xy[0], xy[1], edge='black', lw=0.8, inset=0.08, z=3.1)

    for (x, y) in ub: 
        ax.add_patch(Rectangle((x, y), 1.0, 1.0, facecolor='red', edgecolor='none', zorder=15)) 
    
    for (x, y) in lb: 
        if (x == fx and y == fy): continue 
        ax.add_patch(Rectangle((x, y), 1.0, 1.0, facecolor='red', edgecolor='none', zorder=15))

    ax.set_xlim(0, x_extent)
    ax.set_ylim(0, y_extent)
    xticks = list(range(0, x_extent + 1, 5))
    yticks = list(range(0, y_extent + 1, 5))
    ax.set_xticks([v + 0.5 for v in xticks])
    ax.set_yticks([v + 0.5 for v in yticks])
    ax.set_xticklabels([str(v) for v in xticks], fontsize=6)
    ax.set_yticklabels([str(v) for v in yticks], fontsize=6)

    fig.savefig(pdf_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved plot: {pdf_path}")

    m = open(os.path.join(outdir, "var_to_xy.txt"), "w")
    for v,(x,y) in var_map.items():
        m.write(f"{v}=({x},{y})\n")
    print(f"Saved var map to: {var_path}")


def plot_path_stdout(FA_file, n, fx=None, fy=None):
    outdir = os.path.dirname(FA_file)           
    plot_path = os.path.join(outdir, "FA_plot.txt")
    var_path = os.path.join(outdir, f'var_map.txt')

    var_map = build_var_map(n)
    FA_list = build_FA_list(var_map)
    lb,ub = build_boundary_set(n)

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
         
    plot_file = open(plot_path, "w")
    skip=False
    for y in range(n-1,-1,-1):
        for x in range(0,n):
            if y > fy:
                skip=True
                continue
            if x > fx:
                break
            skip=False
            print(f"{charmap[x][y]}",end="")
            plot_file.write(f"{charmap[x][y]}")
        if not skip:
            print("")
            plot_file.write(f"\n")
    print(f"Saved plot to: {plot_path}")

    m = open(var_path, "w")
    for v,(x,y) in var_map.items():
        m.write(f"{v}=({x},{y})\n")       
    print(f"Saved var map to: {var_path}")

def main():
    n = get_n_value(folder)
    fx, fy = get_xy(folder)

    if print_pdf:
        plot_path_pdf(FA_file, n, fx, fy)
    else:
        plot_path_stdout(FA_file, n, fx, fy)

if __name__ == '__main__':
    main()
