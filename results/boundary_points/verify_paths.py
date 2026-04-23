#!/usr/bin/env python3

import math
import re
from pathlib import Path

PATH_RE = re.compile(r"^[01]+$")

# Check all trimmed .log files for the binary string and verifies < 7 collinear points 
# python3 verify_paths.py

def read_path_bits(path):
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                s = line.strip()
                if PATH_RE.fullmatch(s):
                    return s
    except OSError:
        return None
    return None


def bits_to_points(bits):
    x = 0
    y = 0
    pts = [(x, y)]

    for ch in bits:
        if ch == "0":
            y += 1
        else:
            x += 1
        pts.append((x, y))

    return pts


def line_key(p, q):
    x1, y1 = p
    x2, y2 = q

    a = y2 - y1
    b = x1 - x2
    g = math.gcd(abs(a), abs(b))
    a //= g
    b //= g
    c = a * x1 + b * y1

    if a < 0 or (a == 0 and b < 0):
        a = -a
        b = -b
        c = -c

    return (a, b, c)


def first_bad_line(points, k):
    lines = {}
    n = len(points)

    for i in range(n):
        for j in range(i + 1, n):
            key = line_key(points[i], points[j])

            if key not in lines:
                lines[key] = {i, j}
            else:
                lines[key].add(i)
                lines[key].add(j)

            if len(lines[key]) >= k:
                idxs = sorted(lines[key])
                bad_points = [points[t] for t in idxs]
                return key, bad_points

    return None, None


def main():
    for path in Path.cwd().rglob("*.log"):
        bits = read_path_bits(path)
        if bits is None:
            continue

        points = bits_to_points(bits)
        key, bad_points = first_bad_line(points, 7)

        if bad_points is not None:
            print(path)
            print(key)
            print(bad_points)


if __name__ == "__main__":
    main()