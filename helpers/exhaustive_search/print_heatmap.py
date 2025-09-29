#!/usr/bin/env python3
import argparse
import os
import re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("-k", type=int, required=True)
    ap.add_argument("-n", type=int, required=True)
    ap.add_argument("-m", type=int, required=True)
    return ap.parse_args()

def extract_xy_from_folder(name: str):
    m = re.search(r"_x(\d+)_y(\d+)_", name)
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))

def extract_num_solutions(log_path: Path):
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith("c Number of solutions:"):
                    return int(line.strip().split()[-1])
    except Exception:
        return 0
    return 0

def plot_heatmap(heatmap: np.ndarray, k: int, n: int, m: int, max_x: int, max_y: int):
    fig, ax = plt.subplots(figsize=(8, 8), facecolor="white")
    ax.set_facecolor("white")

    masked = np.ma.masked_where(heatmap == 0, heatmap)
    cmap = matplotlib.colormaps.get_cmap("coolwarm").copy()
    cmap.set_bad(color="white")

    im = ax.imshow(masked, origin="lower", cmap=cmap, interpolation="none", vmin=1)

    label_fontsize = max(4, int(200 / max(1, n)))

    for x in range(heatmap.shape[1]):
        for y in range(heatmap.shape[0]):
            if heatmap[y, x] > 0 and heatmap[y, x] < 100:
                ax.text(x, y, str(heatmap[y, x]),
                        ha="center", va="center",
                        color="black", fontsize=label_fontsize)

    ax.set_xlim(-0.5, max_x + 1.5)
    ax.set_ylim(-0.5, max_y + 1.5)

    ax.set_xticks(range(0, max_x + 2))
    ax.set_yticks(range(0, max_y + 2))
    ax.tick_params(axis="both", which="major", labelsize=label_fontsize)

    for x in range(max_x + 2):
        ax.axvline(x - 0.5, color="lightgrey", linestyle="--", linewidth=0.125)
    for y in range(max_y + 2):
        ax.axhline(y - 0.5, color="lightgrey", linestyle="--", linewidth=0.125)

    ax.set_title("")
    try:
        plt.colorbar(im, ax=ax).remove()
    except Exception:
        pass

    pdf_name = Path(f"heatmap_k{k}_n{n}_m{m}.pdf")
    fig.savefig(pdf_name, format="pdf", bbox_inches="tight", facecolor="white")
    print(f"Saved: {pdf_name}")

def main():
    args = parse_args()
    k, n, m = args.k, args.n, args.m

    base = Path("../output/ex") / f"k{k}_n{n}_m{m}"
    if not base.exists():
        print(f"Base folder not found: {base}")
        return

    print(f"Using base: {base}")
    heatmap = np.zeros((n, n), dtype=int)
    max_x, max_y = 0, 0

    res_folders = [f for f in os.listdir(base) if f.startswith("res_")]
    print(f"Found {len(res_folders)} res_* folders")

    for folder in res_folders:
        x, y = extract_xy_from_folder(folder)
        if x is None or y is None:
            continue
        if not (0 <= x < n and 0 <= y < n):
            continue
        if x + y >= n:
            continue

        log_path = base / folder / "satOutput.log"
        if not log_path.exists():
            continue

        num_solutions = extract_num_solutions(log_path)
        heatmap[y, x] = num_solutions
        if num_solutions > 0:
            if x > max_x: max_x = x
            if y > max_y: max_y = y

    heatmap[0, 0] = max(1, heatmap[0, 0])
    if max_x < 0: max_x = 0
    if max_y < 0: max_y = 0

    filled = np.count_nonzero(heatmap)
    print(f"Filled {filled} cells")

    max_solutions = int(heatmap.max())
    print(f"Max solutions in any cell: {max_solutions}")

    plot_heatmap(heatmap, k, n, m, max_x, max_y)

if __name__ == "__main__":
    main()
