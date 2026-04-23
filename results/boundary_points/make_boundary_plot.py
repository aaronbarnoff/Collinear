#!/usr/bin/env python3
import ast
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Rectangle, RegularPolygon

# plot the boundary points (upper, lower, diagonal) from the trimmed logs
# the final unsat point on diagonal is hard-coded

K = 7
INPUT_FILE = "bounds.txt"
OUTPUT_FILE = "boundary_plot.pdf"

ALL_LABELS = [
    "Upper-bound SAT points:",
    "Upper-bound UNSAT points:",
    "Lower-bound SAT points:",
    "Lower-bound UNSAT points:",
    "Combined UNSAT boundary points:",
    "Diagonal SAT points:",
    "Total CPU time:",
    "Upper CPU time:",
    "Lower CPU time:",
    "Diagonal CPU time:",
    "upper bounds:",
    "lower bounds:",
    "Combined upper-bound UNSAT points (+ reflection):",
    "Saved PDF:",
]

WANTED_LABELS = {
    "Upper-bound SAT points:": "upper_sat",
    "Upper-bound UNSAT points:": "upper_unsat",
    "Lower-bound SAT points:": "lower_sat",
    "Lower-bound UNSAT points:": "lower_unsat",
    "Diagonal SAT points:": "diag_sat",
}


def extract_list(text, label):
    start = text.find(label)
    if start == -1:
        return []

    start += len(label)
    end = len(text)

    for other in ALL_LABELS:
        if other == label:
            continue
        pos = text.find(other, start)
        if pos != -1 and pos < end:
            end = pos

    block = text[start:end].strip()
    if not block:
        return []

    return ast.literal_eval(block)


def read_bounds(path):
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    data = {}

    for label, key in WANTED_LABELS.items():
        data[key] = extract_list(text, label)

    return data


def infer_n(*point_lists):
    pts = []
    for lst in point_lists:
        pts.extend(lst)
    return max((x + y + 1 for x, y in pts), default=1)


def main():
    data = read_bounds(INPUT_FILE)

    upper_sat = data["upper_sat"]
    upper_unsat = data["upper_unsat"]
    lower_sat = data["lower_sat"]
    lower_unsat = data["lower_unsat"]
    diag_sat = data["diag_sat"]

    reflect_unsat = sorted(set(upper_unsat) | {(y, x) for x, y in upper_unsat})
    n = infer_n(upper_sat, upper_unsat, lower_sat, lower_unsat, diag_sat)

    fig, ax = plt.subplots(figsize=(20, 20))

    for x in range(n):
        for y in range(n):
            if x + y < n and ((x == (K - 2) * y + 1) or (y == (K - 2) * x + (K - 1))):
                ax.add_patch(
                    Circle((x, y), 0.3, facecolor="grey", edgecolor="grey", linewidth=1.25, zorder=10)
                )

    for x, y in reflect_unsat:
        if x >= y:
            ax.add_patch(
                RegularPolygon(
                    (x, y - 0.125),
                    numVertices=3,
                    radius=0.5,
                    orientation=0,
                    facecolor="black",
                    edgecolor="none",
                    zorder=10,
                )
            )

    for pts in (upper_unsat, lower_unsat):
        for x, y in pts:
            ax.plot([x - 0.3, x + 0.3], [y - 0.3, y + 0.3], color="red", linewidth=1, zorder=10)
            ax.plot([x - 0.3, x + 0.3], [y + 0.3, y - 0.3], color="red", linewidth=1, zorder=10)

    for pts in (upper_sat, lower_sat, diag_sat):
        for x, y in pts:
            ax.add_patch(
                Rectangle((x - 0.5, y - 0.5), 1, 1, facecolor="blue", edgecolor="none", zorder=3)
            )

    # n=294 (146,147) UNSAT point
    ax.plot([146 - 0.3, 146 + 0.3], [147 - 0.3, 147 + 0.3], color="red", linewidth=1, zorder=10)
    ax.plot([146 - 0.3, 146 + 0.3], [147 + 0.3, 147 - 0.3], color="red", linewidth=1, zorder=10)

    all_points = upper_sat + upper_unsat + lower_sat + lower_unsat + diag_sat + reflect_unsat
    max_x = max((x for x, _ in all_points), default=0)
    max_y = max((y for _, y in all_points), default=0)

    ax.set_xlim(-0.5, max_x + 2.5)
    ax.set_ylim(-0.5, max_y + 2.5)
    ax.set_xticks(range(0, max_x + 2, 5))
    ax.set_yticks(range(0, max_y + 2, 5))

    for lbl in ax.get_xticklabels():
        lbl.set_rotation(90)

    x_vals = np.linspace(-0.5, n - 0.5, 200)
    #ax.plot(x_vals, x_vals, color="gray", linestyle="--", linewidth=0.5, zorder=10)

    for xi in range(n + 1):
        ax.axvline(xi - 0.5, color="lightgrey", linestyle="--", linewidth=0.125, zorder=9)
    for yi in range(n + 1):
        ax.axhline(yi - 0.5, color="lightgrey", linestyle="--", linewidth=0.125, zorder=9)

    ax.tick_params(axis="both", which="major", labelsize=16)
    ax.set_aspect("equal")

    fig.savefig(OUTPUT_FILE, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()