#!/usr/bin/env python3
import argparse
import os
import sys
import math

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


def extract_solution(v, n, k, sat_log_file_path):
    with open(sat_log_file_path, 'r') as log_file:
        lines = log_file.readlines()

    model = []
    for line in lines:
        if line.startswith('v '):
            numbers = list(map(int, line[2:].strip().split()))
            model.extend([num for num in numbers if num > 0])
        elif line.startswith('c New solution:'):
            numbers = list(map(int, line[16:].strip().split()))
            print(numbers)
            model.extend([num for num in numbers if num > 0])

    model = [lit for lit in model if lit > 0] 
    model_set = set(model)

    points_list = []
    for x in range(n):
        for y in range(n):
            if y < n - x:
                if v[x][y] in model_set:
                    points_list.append((x, y))
    return points_list



def point_is_valid(x, y, n):
    return x >= 0 and y >= 0 and x + y < n

def verify_solution(n,k,point_list):
    collinear_list = []
    point_set = set(point_list)
    seen_lines = set()
    for (x1, y1) in point_list:
        for (x2, y2) in point_list:
            if (x1, y1) == (x2, y2):
                continue
            if (x2 < x1) or (y2 < y1):
                continue

            # get the primitive distance between points on the line
            g = math.gcd(x2 - x1, y2 - y1)
            m_p = (x2 - x1) // g
            m_q = (y2 - y1) // g

            tmp_point_list = []

            # move to first point on grid
            x = x1
            y = y1
            while point_is_valid(x - m_p, y - m_q, n): 
                x -= m_p
                y -= m_q

            # walk forward with reduced step along the line, collect all path-points along it
            while point_is_valid(x,y,n):
                if (x,y) in point_set:
                    tmp_point_list.append((x, y))
                x += m_p
                y += m_q

            if len(tmp_point_list) >= k:
                line = tuple(tmp_point_list)

                # print(tmpPointsList)
                if line not in seen_lines:
                    seen_lines.add(line)
                    collinear_list.append(tmp_point_list)
    
    if collinear_list:
        print(f"Failure: {k} or more points found on the same line.")
        for line in collinear_list:
            (x1, y1)= line[0]
            (x2, y2)= line[1]
            if (x2 - x1) == 0:
                print('vline. points: ', end="")
            elif (y2 - y1) == 0:
                print('hline. points: ', end="")
            else:
                print(f'slope: {((y2 - y1) / (x2 - x1)):.2g}; m_p: {(y2-y1)}, m_q: {(x2-x1)}; points: ',end="")
            for points in line:
                (x, y)=points
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
    print(f"Extracted {len(points_list)} path points.")
    if len(points_list) != n:
        print(f"Failure: Only found {len(points_list)} points instead of {n}.")
        return 2

    collinear_list = verify_solution(n, k, points_list)

    if collinear_list:
        return 1
    
    print("Solution verified.")
    return 0

if __name__ == '__main__':
    sys.exit(main())
