#!/usr/bin/env python3
import argparse
import subprocess
import sys
from datetime import datetime
import time

# XY lookup for special points
XY = {
    (6, 50): (0, 0),
    (6, 96): (0, 0),
    (6, 97): (0, 0),
    (6, 98): (0, 0),
    (7, 122): (33, 88),
    (7, 151): (46, 104),
    (7, 180): (56, 123),
    (7, 220): (0, 0),
    (7, 240): (0, 0),
    (7, 250): (85, 164),  # Hard SAT CNFvsKNF test
    (7, 254): (165, 88),  # Hard SAT CNFvsKNF test
    (7, 261): (0, 0),
    (7, 262): (170, 91),  # Hard SAT CNFvsKNF test
    (7, 270): (0, 0),
    (7, 280): (0, 0),
    (7, 290): (0, 0),
}

# mode templates
MODE_NONE = ["None"]
MODE_STRUCTURAL = ["structural"]
MODE_BOUNDARY = ["U", "UB"]
MODE_NONE_BOUNDARY = ["None", "U", "UB"]
MODE_NONE_UB = ["None", "UB"]
MODE_UB = ["UB"]
MODE_ALL = ["None", "structural", "U", "UB", "US", "UBS"]

# heuristics (FILTER). Always lists of strings.
HEUR_K7_BOTH = ["0", "10"]
HEUR_10 = ["10"]
HEUR_0 = ["0"]

# CCDCL KNF mode: human label, flag value for -w
KNF_MODE_BOTH = [("BOTH", -1), ("HYBRID", 1), ("PURE", 0)]  # if you actually want three passes
KNF_PURE = [("PURE", 0)]
KNF_HYBRID = [("HYBRID", 1)]

# solver templates: human label, -f value
SOLVER_KNF = [("KNF", 1)]
SOLVER_CNF = [("CNF", 0)]
SOLVER_BOTH = [("KNF", 1), ("CNF", 0)]

# vertical/horizontal constraint templates (-c value: if c=0 then v=1)
VH_BOTH = [("ON", 1), ("OFF", 0)]
VH_BINARY = [("OFF", 0)]
VH_CARDINALITY = [("ON", 1)]

# point templates
TEMPLATES = {
    "k6_n50_test": dict(
        K=6, N=50, X=XY[(6, 50)][0], Y=XY[(6, 50)][1],
        SOLVER=SOLVER_KNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE,
        SEEDS=1, WALLTIME="00:15:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_K7_BOTH,
        KNFMODE=KNF_PURE,
        MEMREQ=4, 
    ),

    "k6_n96_test": dict(
        K=6, N=96, X=XY[(6, 96)][0], Y=XY[(6, 96)][1],
        SOLVER=SOLVER_BOTH, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=2, WALLTIME="00:10:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_K7_BOTH,
        KNFMODE=KNF_PURE,
        MEMREQ=4,
    ),

    # ----------------------------------------- SAT Jobs -----------------------------------------------------------
    # k6 n97
    "k6_n97_all": dict(
        K=6, N=97, X=XY[(6, 97)][0], Y=XY[(6, 97)][1],
        SOLVER=SOLVER_BOTH, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="02:00:00",
        RUNNER="run_retry.sh",
        FILTER=["8"],              # always list
        KNFMODE=KNF_PURE,
        MEMREQ=4,
    ),

    # k7 n220
    "k7_n220_CNF": dict(
        K=7, N=220, X=XY[(7, 220)][0], Y=XY[(7, 220)][1],
        SOLVER=SOLVER_CNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="04:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_K7_BOTH,
        KNFMODE=KNF_PURE,
        MEMREQ=8,
    ),
    "k7_n220_KNF": dict(
        K=7, N=220, X=XY[(7, 220)][0], Y=XY[(7, 220)][1],
        SOLVER=SOLVER_KNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="04:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_K7_BOTH,
        KNFMODE=KNF_PURE,
        MEMREQ=4,       
    ),

    # k7 n240
    "k7_n240_CNF": dict(
        K=7, N=240, X=XY[(7, 240)][0], Y=XY[(7, 240)][1],
        SOLVER=SOLVER_CNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="16:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_K7_BOTH,
        KNFMODE=KNF_PURE,
        MEMREQ=8,       
    ),
    "k7_n240_KNF": dict(
        K=7, N=240, X=XY[(7, 240)][0], Y=XY[(7, 240)][1],
        SOLVER=SOLVER_KNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="16:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_K7_BOTH,
        KNFMODE=KNF_PURE,
        MEMREQ=4,        
    ),

    # k7 n261
    "k7_n261_CNF": dict(
        K=7, N=261, X=XY[(7, 261)][0], Y=XY[(7, 261)][1],
        SOLVER=SOLVER_CNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="36:00:00",  # one always times out at 24h
        RUNNER="run_retry.sh",
        FILTER=HEUR_K7_BOTH,
        KNFMODE=KNF_PURE,
        MEMREQ=12,
    ),
    "k7_n261_KNF": dict(
        K=7, N=261, X=XY[(7, 261)][0], Y=XY[(7, 261)][1],
        SOLVER=SOLVER_KNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="24:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_K7_BOTH,
        KNFMODE=KNF_PURE,
        MEMREQ=4,  
    ),

    # k7 n270
    "k7_n270_KNF": dict(
        K=7, N=270, X=XY[(7, 270)][0], Y=XY[(7, 270)][1],
        SOLVER=SOLVER_KNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_UB,
        SEEDS=15, WALLTIME="36:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_K7_BOTH,
        KNFMODE=KNF_PURE,
        MEMREQ=4,
    ),

    "k7_n270_CNF_NOHEUR": dict(
        K=7, N=270, X=XY[(7, 270)][0], Y=XY[(7, 270)][1],
        SOLVER=SOLVER_CNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_UB,
        SEEDS=15, WALLTIME="36:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_0,
        KNFMODE=KNF_PURE,
        MEMREQ=16, 
    ),

    "k7_n270_CNF_HEUR": dict(
        K=7, N=270, X=XY[(7, 270)][0], Y=XY[(7, 270)][1],
        SOLVER=SOLVER_CNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_UB,
        SEEDS=15, WALLTIME="36:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_10,
        KNFMODE=KNF_PURE,
        MEMREQ=8,
    ),

    # k7 n280
    "k7_n280_KNF": dict(
        K=7, N=280, X=XY[(7, 280)][0], Y=XY[(7, 280)][1],
        SOLVER=SOLVER_KNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_UB,
        SEEDS=15, WALLTIME="36:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_K7_BOTH,
        KNFMODE=KNF_PURE,
        MEMREQ=4,   
    ),

    "k7_n280_CNF_NOHEUR": dict(
        K=7, N=280, X=XY[(7, 280)][0], Y=XY[(7, 280)][1],
        SOLVER=SOLVER_CNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_UB,
        SEEDS=15, WALLTIME="36:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_0,
        KNFMODE=KNF_PURE,
        MEMREQ=20,
    ),

    "k7_n280_CNF_HEUR": dict(
        K=7, N=280, X=XY[(7, 280)][0], Y=XY[(7, 280)][1],
        SOLVER=SOLVER_CNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_UB,
        SEEDS=15, WALLTIME="36:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_10,
        KNFMODE=KNF_PURE,
        MEMREQ=8,
    ),

    # k7 n290
    "k7_n290_KNF": dict(
        K=7, N=290, X=XY[(7, 290)][0], Y=XY[(7, 290)][1],
        SOLVER=SOLVER_KNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_UB,
        SEEDS=15, WALLTIME="36:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_K7_BOTH,
        KNFMODE=KNF_PURE,
        MEMREQ=4,
    ),

    "k7_n290_CNF_NOHEUR": dict(
        K=7, N=290, X=XY[(7, 290)][0], Y=XY[(7, 290)][1],
        SOLVER=SOLVER_CNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_UB,
        SEEDS=15, WALLTIME="36:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_0,
        KNFMODE=KNF_PURE,
        MEMREQ=24,   
    ),

    "k7_n290_CNF_HEUR": dict(
        K=7, N=290, X=XY[(7, 290)][0], Y=XY[(7, 290)][1],
        SOLVER=SOLVER_CNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_UB,
        SEEDS=15, WALLTIME="36:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_10,
        KNFMODE=KNF_PURE,
        MEMREQ=12,
    ),

    # Hard SAT boundary points
    "k7_n250_SAT_KNF": dict(
        K=7, N=250, X=XY[(7, 250)][0], Y=XY[(7, 250)][1],
        SOLVER=SOLVER_KNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_UB,
        SEEDS=15, WALLTIME="36:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_K7_BOTH,
        KNFMODE=KNF_PURE,
        MEMREQ=16,
    ),
    "k7_n250_SAT_CNF": dict(
        K=7, N=250, X=XY[(7, 250)][0], Y=XY[(7, 250)][1],
        SOLVER=SOLVER_CNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_UB,
        SEEDS=15, WALLTIME="36:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_K7_BOTH,
        KNFMODE=KNF_PURE,
        MEMREQ=12,
    ),

    "k7_n254_SAT_KNF": dict(
        K=7, N=254, X=XY[(7, 254)][0], Y=XY[(7, 254)][1],
        SOLVER=SOLVER_KNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_UB,
        SEEDS=15, WALLTIME="36:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_K7_BOTH,
        KNFMODE=KNF_PURE,
        MEMREQ=16, 
    ),
    "k7_n254_SAT_CNF": dict(
        K=7, N=254, X=XY[(7, 254)][0], Y=XY[(7, 254)][1],
        SOLVER=SOLVER_CNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_UB,
        SEEDS=15, WALLTIME="36:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_K7_BOTH,
        KNFMODE=KNF_PURE,
        MEMREQ=12,
    ),

    "k7_n262_SAT_KNF": dict(
        K=7, N=262, X=XY[(7, 262)][0], Y=XY[(7, 262)][1],
        SOLVER=SOLVER_KNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_UB,
        SEEDS=15, WALLTIME="48:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_K7_BOTH,
        KNFMODE=KNF_PURE,
        MEMREQ=16,
    ),
    "k7_n262_SAT_CNF": dict(
        K=7, N=262, X=XY[(7, 262)][0], Y=XY[(7, 262)][1],
        SOLVER=SOLVER_CNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_UB,
        SEEDS=15, WALLTIME="48:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_K7_BOTH,
        KNFMODE=KNF_PURE,
        MEMREQ=12,
    ),
    
    # ----------------------------------------- UNSAT Jobs -----------------------------------------------------------

    # k6 n98
    "k6_n98_all": dict(
        K=6, N=98, X=XY[(6, 98)][0], Y=XY[(6, 98)][1],
        SOLVER=SOLVER_BOTH, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="02:00:00",
        RUNNER="run_retry.sh",
        FILTER=["8"],
        KNFMODE=KNF_PURE,
        MEMREQ=4,
    ),

    # k7 n122
    "k7_n122_all": dict(
        K=7, N=122, X=XY[(7, 122)][0], Y=XY[(7, 122)][1],
        SOLVER=SOLVER_BOTH, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="04:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_K7_BOTH,
        KNFMODE=KNF_PURE,
        MEMREQ=4,    
    ),

    # k7 n151
    "k7_n151_CNF": dict(
        K=7, N=151, X=XY[(7, 151)][0], Y=XY[(7, 151)][1],
        SOLVER=SOLVER_CNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="24:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_K7_BOTH,
        KNFMODE=KNF_PURE,
        MEMREQ=4,
    ),
    "k7_n151_KNF": dict(
        K=7, N=151, X=XY[(7, 151)][0], Y=XY[(7, 151)][1],
        SOLVER=SOLVER_KNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="24:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_K7_BOTH,
        KNFMODE=KNF_PURE,
        MEMREQ=4,
    ),

    # k7 n180
    "k7_n180_CNF": dict(
        K=7, N=180, X=XY[(7, 180)][0], Y=XY[(7, 180)][1],
        SOLVER=SOLVER_CNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="36:00:00",
        RUNNER="run_retry.sh", 
        FILTER=HEUR_K7_BOTH,
        KNFMODE=KNF_PURE,
        MEMREQ=4,
    ),
    "k7_n180_KNF": dict(
        K=7, N=180, X=XY[(7, 180)][0], Y=XY[(7, 180)][1],
        SOLVER=SOLVER_KNF, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="36:00:00",
        RUNNER="run_retry.sh",
        FILTER=HEUR_K7_BOTH,
        KNFMODE=KNF_PURE,
        MEMREQ=4,
    ),

   
}
# k7: 20 works for n180 and n261; n50 <= 2; n100 <= 7; n120 <= 15; n150 <= 14; n200 <= 19; n250 <= 21; n261 ~= 20

s_val = 1  # symmetry break always on

def ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def params_for_mode(mode: str, c_val: int):
    if mode == "U":
        a, l, b, v = 0, 0, 1, (1 if c_val == 0 else 0)
    elif mode == "UB":
        a, l, b, v = 0, 0, 2, (1 if c_val == 0 else 0)
    elif mode == "US":
        a, l, b, v = 1, 5, 1, 1
    elif mode == "UBS":
        a, l, b, v = 1, 5, 2, 1
    elif mode == "structural":
        a, l, b, v = 1, 5, 0, 1
    elif mode == "None":
        a, l, b, v = 0, 0, 0, (1 if c_val == 0 else 0)
    else:
        raise ValueError(f"Unknown mode: {mode}")
    return v, a, l, b

def submit_job(*, walltime, runner, k_val, n_val, x_val, y_val, s_val,
               c_val, v_val, a_val, l_val, b_val, f_val, r_val, j_val, w_val,
               mode_tag: str, knf_tag: str, memreq):
    jobname = f"k{k_val}n{n_val}x{x_val}y{y_val}f{f_val}s{r_val}m{mode_tag}w{knf_tag}"
    cmd = [
        "sbatch",
        f"--time={walltime}",
        #f"--exclude=fc30464", # node issues fixed
        f"--mem-per-cpu={memreq}G",
        f"--job-name={jobname}",
        runner,
        "-k", str(k_val), "-n", str(n_val), "-x", str(x_val), "-y", str(y_val), "-s", str(s_val),
        "-c", str(c_val), "-v", str(v_val), "-a", str(a_val), "-l", str(l_val), "-b", str(b_val),
        "-f", str(f_val), "-r", str(r_val), "-t", "0", "-j", str(j_val), "-w", str(w_val)
    ]
    print(f"[{ts()}] SUB: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("template", help="e.g. k7_n261_CNF")
    args = p.parse_args()

    if args.template not in TEMPLATES:
        print("Unknown template:", args.template)
        print("Valid keys:", ", ".join(sorted(TEMPLATES.keys())))
        sys.exit(1)

    cfg = TEMPLATES[args.template]
    k_val, n_val, x_val, y_val = cfg["K"], cfg["N"], cfg["X"], cfg["Y"]
    solver = cfg["SOLVER"]
    vhcon = cfg["VHCONSTRAINT"]
    modes = cfg["MODES"]
    seeds = cfg["SEEDS"]
    walltime = cfg["WALLTIME"]
    runner = cfg["RUNNER"]
    filter_list = cfg["FILTER"]
    knfmode = cfg["KNFMODE"]
    memreq=cfg["MEMREQ"]

    if isinstance(filter_list, str):
        filter_list = [filter_list]

    total = len(solver) * len(vhcon) * len(modes) * len(filter_list) * len(knfmode) * seeds
    print(f"[{ts()}] Template={args.template}: submitting {total} jobs")

    for form_name, f_val in solver:
        for vhc_name, c_val in vhcon:
            for mode in modes:
                v_val, a_val, l_val, b_val = params_for_mode(mode, c_val)
                for knf_name, w_val in knfmode:
                    for j_val in filter_list:
                        for seed in range(1, seeds + 1):
                            submit_job(
                                walltime=walltime,
                                runner=runner,
                                k_val=k_val, n_val=n_val, x_val=x_val, y_val=y_val, s_val=s_val,
                                c_val=c_val, v_val=v_val, a_val=a_val, l_val=l_val, b_val=b_val,
                                f_val=f_val, r_val=seed, j_val=j_val, w_val=w_val,
                                mode_tag=mode, knf_tag=knf_name, memreq=memreq
                            )
                            time.sleep(1)

    print(f"[{ts()}] Done.")

if __name__ == "__main__":
    main()
