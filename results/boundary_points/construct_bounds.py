#!/usr/bin/env python3
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle, Circle, RegularPolygon

Point = Tuple[int, int]

# Construct and verify the boundary data (upper/lower path) from the trimmed logs (which are in pwd/folders)
# python3 construct_bounds.py > bounds.txt


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', type=int, default=7)
    parser.add_argument('-n', type=int, default=300, help='')
    parser.add_argument('-o', default='boundary_plot_from_logs', help='')
    parser.add_argument('-c', type=int, default=None, help='cutoff n_val')
    return parser.parse_args()


def parse_trimmed_log(path: Path) -> Optional[Dict]:
    x = None
    y = None
    cpu_time = 0.0
    status = None
    has_failure = False

    try:
        text = path.read_text(encoding='utf-8', errors='ignore')
    except OSError:
        return None

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if line.startswith('x='):
            try:
                x = int(line.split('=', 1)[1])
            except ValueError:
                return None

        elif line.startswith('y='):
            try:
                y = int(line.split('=', 1)[1])
            except ValueError:
                return None

        elif line.startswith('cpu_time='):
            val = line.split('=', 1)[1].strip()
            if val != 'None':
                try:
                    cpu_time = float(val)
                except ValueError:
                    cpu_time = 0.0

        elif line == 'SATISFIABLE':
            status = 'SATISFIABLE'

        elif line == 'UNSATISFIABLE':
            status = 'UNSATISFIABLE'

        elif line.startswith('Failure:'):
            has_failure = True

    if x is None or y is None:
        return None

    if status is None and not has_failure:
        return None

    n = x + y + 1

    if has_failure:
        verdict = 'UNSAT'
    elif status == 'SATISFIABLE':
        verdict = 'SAT'
    else:
        verdict = 'UNSAT'

    return {
        'path': path,
        'x': x,
        'y': y,
        'n': n,
        'cpu_time': cpu_time,
        'verdict': verdict,
        'has_failure': has_failure,
        'skip_plot': path.name.endswith('_fail.log'),
        'mtime': path.stat().st_mtime,
    }


def collect_points(root: Path) -> List[Dict]:
    best_by_point: Dict[Point, Dict] = {}

    for path in root.rglob('*.log'):
        rec = parse_trimmed_log(path)
        if rec is None:
            continue

        key = (rec['x'], rec['y'])
        prev = best_by_point.get(key)

        if prev is None or rec['mtime'] > prev['mtime']:
            best_by_point[key] = rec

    return list(best_by_point.values())


def classify_points(records: List[Dict], cutoff: Optional[int]):
    upper_sat: List[Point] = []
    upper_unsat: List[Point] = []
    lower_sat: List[Point] = []
    lower_unsat: List[Point] = []
    diagonal_sat: List[Point] = []

    total_cpu_time = 0.0
    upper_cpu_time = 0.0
    lower_cpu_time = 0.0
    diagonal_cpu_time = 0.0

    cutoff_total_cpu_time = 0.0
    cutoff_upper_cpu_time = 0.0
    cutoff_lower_cpu_time = 0.0
    cutoff_diagonal_cpu_time = 0.0

    for rec in records:
        x = rec['x']
        y = rec['y']
        n = rec['n']
        verdict = rec['verdict']
        cpu_time = rec['cpu_time']

        total_cpu_time += cpu_time

        in_cutoff = (cutoff is not None and n <= cutoff)
        if in_cutoff:
            cutoff_total_cpu_time += cpu_time

        p = (x, y)
        diagonal = (y == x + 1) or (p == (1, 1))
        upper = (y > x + 1) or (p == (0, 1))
        lower = (y < x + 1) or (p in {(0, 1), (1, 1)})

        if diagonal:
            if not rec['skip_plot'] and verdict == 'SAT':
                diagonal_sat.append((x, y))

            diagonal_cpu_time += cpu_time
            if in_cutoff:
                cutoff_diagonal_cpu_time += cpu_time

        if upper:
            upper_cpu_time += cpu_time
            if in_cutoff:
                cutoff_upper_cpu_time += cpu_time

            if not rec['skip_plot']:
                if verdict == 'SAT':
                    upper_sat.append((x, y))
                else:
                    upper_unsat.append((x, y))

        if lower:
            lower_cpu_time += cpu_time
            if in_cutoff:
                cutoff_lower_cpu_time += cpu_time

            if not rec['skip_plot']:
                if verdict == 'SAT':
                    lower_sat.append((x, y))
                else:
                    lower_unsat.append((x, y))

    upper_sat = sorted(set(upper_sat))
    upper_unsat = sorted(set(upper_unsat))
    lower_sat = sorted(set(lower_sat))
    lower_unsat = sorted(set(lower_unsat))
    diagonal_sat = sorted(set(diagonal_sat))
    return (
        upper_sat,
        upper_unsat,
        lower_sat,
        lower_unsat,
        diagonal_sat,
        total_cpu_time,
        upper_cpu_time,
        lower_cpu_time,
        diagonal_cpu_time,
        cutoff_total_cpu_time,
        cutoff_upper_cpu_time,
        cutoff_lower_cpu_time,
        cutoff_diagonal_cpu_time
    )


def print_tables(
    upper_sat: List[Point],
    upper_unsat: List[Point],
    lower_sat: List[Point],
    lower_unsat: List[Point],
    diagonal_sat: List[Point],
    total_cpu_time: float,
    upper_cpu_time: float,
    lower_cpu_time: float,
    diagonal_cpu_time: float,
    cutoff: Optional[int],
    cutoff_total_cpu_time: float,
    cutoff_upper_cpu_time: float,
    cutoff_lower_cpu_time: float,
    cutoff_diagonal_cpu_time: float
):
    combined_unsat = upper_unsat + lower_unsat

    print('Upper-bound SAT points:')
    print(sorted(upper_sat), '\n')

    print('Upper-bound UNSAT points:')
    print(sorted(upper_unsat), '\n')

    print('Lower-bound SAT points:')
    print(sorted(lower_sat), '\n')

    print('Lower-bound UNSAT points:')
    print(sorted(lower_unsat), '\n')

    print('Combined UNSAT boundary points:')
    print(sorted(combined_unsat), '\n')

    print('Diagonal SAT points:')
    print(sorted(diagonal_sat), '\n')

    print(f'Total CPU time: {total_cpu_time:.2f} seconds')
    print(f'Upper CPU time: {upper_cpu_time:.2f} seconds')
    print(f'Lower CPU time: {lower_cpu_time:.2f} seconds')
    print(f'Diagonal CPU time: {diagonal_cpu_time:.2f} seconds')

    if cutoff is not None:
        print()
        print(f'Total CPU time for n <= {cutoff}: {cutoff_total_cpu_time:.2f} seconds')
        print(f'Upper CPU time for n <= {cutoff}: {cutoff_upper_cpu_time:.2f} seconds')
        print(f'Lower CPU time for n <= {cutoff}: {cutoff_lower_cpu_time:.2f} seconds')
        print(f'Diagonal CPU time for n <= {cutoff}: {cutoff_diagonal_cpu_time:.2f} seconds')
    print()

def check_boundary_completeness(
    name: str,
    sat_points: List[Point],
    unsat_points: List[Point],
    stop_point: Point,
    is_upper: bool,
):
    sat_set = set(sat_points)
    unsat_set = set(unsat_points)
    all_set = set(sat_set | unsat_set)
    if (is_upper):
        cur = (0, 1)
    else:
        cur = (1,1)

    while True:
        if cur not in all_set:
            x,y=cur
            print(f"{name}: Missing point at ({x},{y}). Stopping.")
            print(f"{name}: Missing point at ({x},{y}). Stopping.", file=sys.stderr)
            return False

        if cur == stop_point:
            break

        x, y = cur

        if is_upper:
            if cur in sat_set:
                cur = (x, y + 1)
            elif cur in unsat_set:
                cur = (x + 1, y - 1)
        else:
            if cur in sat_set:
                cur = (x + 1, y)
            elif cur in unsat_set:
                cur = (x - 1, y + 1)

def run_boundary_checks(
    upper_sat: List[Point],
    upper_unsat: List[Point],
    lower_sat: List[Point],
    lower_unsat: List[Point],
):
    upper_all = sorted(set(upper_sat) | set(upper_unsat))
    lower_all = sorted(set(lower_sat) | set(lower_unsat))

    upper_stop =upper_all[-1] 
    lower_stop =lower_all[-1] 

    print(f'upper bounds: stopping point = {upper_stop}')
    success_up = check_boundary_completeness(
        name='upper bounds',
        sat_points=upper_sat,
        unsat_points=upper_unsat,
        stop_point=upper_stop,
        is_upper=True
    )

    print(f'lower bounds: stopping point = {lower_stop}')
    success_down = check_boundary_completeness(
        name='lower bounds',
        sat_points=lower_sat,
        unsat_points=lower_unsat,
        stop_point=lower_stop,
        is_upper=False
    )
    if not success_up or not success_down:
        sys.exit(0)

def main():
    args = parse_args()

    records = collect_points(Path.cwd())
    if not records:
        print('No trimmed boundary logs found under the current directory.')
        return

    (
        upper_sat,
        upper_unsat,
        lower_sat,
        lower_unsat,
        diagonal_sat,
        total_cpu_time,
        upper_cpu_time,
        lower_cpu_time,
        diagonal_cpu_time,
        cutoff_total_cpu_time,
        cutoff_upper_cpu_time,
        cutoff_lower_cpu_time,
        cutoff_diagonal_cpu_time,
    ) = classify_points(records, args.c)

    print_tables(
        upper_sat,
        upper_unsat,
        lower_sat,
        lower_unsat,
        diagonal_sat,
        total_cpu_time,
        upper_cpu_time,
        lower_cpu_time,
        diagonal_cpu_time,
        args.c,
        cutoff_total_cpu_time,
        cutoff_upper_cpu_time,
        cutoff_lower_cpu_time,
        cutoff_diagonal_cpu_time,
    )

    run_boundary_checks(
        upper_sat,
        upper_unsat,
        lower_sat,
        lower_unsat,
    )

    reflected_upper_unsat = [(y, x) for x, y in upper_unsat]
    combined_reflect = sorted(set(upper_unsat) | set(reflected_upper_unsat))
    print('Combined upper-bound UNSAT points (+ reflection):')
    print(combined_reflect, '\n')




if __name__ == '__main__':
    main()