#!/usr/bin/env python3
import os
import re
from pathlib import Path

POINT_MAPS = None
CURRENT_N = None
CURRENT_K = None
POINT_MAP = None
SOLN = "c New solution:"
VIOLATIONS_LOG_PATH = Path("violations.log")


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
    return collinear_list


def build_point_maps(max_n=330):
    maps = {}
    for n in range(1, max_n + 1):
        v = [[0 for _ in range(n)] for _ in range(n)]
        counter = 0
        for b in range(n):
            for x in range(n):
                y = b - x
                if 0 <= y < n:
                    counter += 1
                    v[x][y] = counter
        inv = {}
        for x in range(n):
            for y in range(n):
                if v[x][y] > 0:
                    inv[v[x][y]] = (x, y)
        maps[n] = inv
    return maps


def parse_kn_from_folder(folder):
    m = re.search(r"res_k(\d+)_n(\d+)_", folder)
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))


def parse_solution_vars(line):
    parts = line.split(":", 1)[1].strip().split()
    out = []
    for p in parts:
        v = int(p)
        if v == 0:
            break
        if v > 0:
            out.append(v)
    return out


def vars_to_points(var_list):
    seen = set()
    pts = []
    for v in var_list:
        xy = POINT_MAP.get(v)
        if xy is None:
            continue
        x, y = xy
        if y < CURRENT_N - x and xy not in seen:
            seen.add(xy)
            pts.append(xy)
    pts.sort()
    return pts


def format_collinear_for_log(collinear_list):
    lines = []
    for line_pts in collinear_list:
        (a1, b1) = line_pts[0]
        (a2, b2) = line_pts[1]
        if (a2 - a1) == 0:
            header = "vline. points:"
        elif (b2 - b1) == 0:
            header = "hline. points:"
        else:
            slope = (b2 - b1) / (a2 - a1)
            header = f"slope: {slope:.2g}; m_p: {(b2 - b1)}, m_q: {(a2 - a1)}; points:"
        pts_str = " ".join(f"({x},{y})" for (x, y) in line_pts)
        lines.append(f"{header} {pts_str}")
    return lines


def main():
    global CURRENT_N, CURRENT_K, POINT_MAP
    with open(VIOLATIONS_LOG_PATH, "a", encoding="utf-8") as vout:
        cwd = Path(".").resolve()
        for root, dirs, files in os.walk(cwd):
            print(f"Scanning folder: {root}")
            if "satOutput.log" not in files:
                continue

            k, n = parse_kn_from_folder(str(root))
            if not k or not n:
                continue

            CURRENT_N, CURRENT_K, POINT_MAP = n, k, POINT_MAPS[n]
            log_path = Path(root) / "satOutput.log"

            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not line.startswith(SOLN):
                        continue
                    var_list = parse_solution_vars(line)
                    if not var_list:
                        continue
                    pts = vars_to_points(var_list)
                    collinear = verify_solution(CURRENT_N, CURRENT_K, pts)
                    if collinear:
                        vout.write(f"[VIOLATION]\n")
                        vout.write(f"folder: {root}\n")
                        vout.write(f"k: {CURRENT_K}, n: {CURRENT_N}\n")
                        vout.write("solution_vars: " + " ".join(str(v) for v in var_list) + "\n")
                        for ln in format_collinear_for_log(collinear):
                            vout.write(ln + "\n")
                        vout.write("\n")
                        vout.flush()


if __name__ == "__main__":
    POINT_MAPS = build_point_maps(330)
    main()
