#!/usr/bin/env python3
import argparse
import subprocess
import sys
from datetime import datetime
import time

# This will schedule 15 individual jobs (15 random seeds) for the given template, using run4GB.sh, run8GB.sh, run12GB.sh
# e.g. "k6_n97_all" with SOLVER=SOLVER_BOTH, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY:
# schedules 15 tests for None, U, UB with VH_BINARY using both CNF (15*3 jobs) and KNF (15*3 jobs) giving 90 jobs total.

# CNF needs 8-12GB after n=180; cardnetwrk and sortnetwrk encodings need extra memory
# SBATCH wall-clock times are chosen large enough to avoid timeouts

XY = {
    (6, 50): (0, 0),
    (6, 96): (0, 0),
    (6, 97): (0, 0),
    (6, 98): (0, 0),
    (7, 220): (0, 0),
    (7, 240): (0, 0),
    (7, 261): (0, 0),
    (7, 270): (0, 0),
    (7, 280): (0, 0),
    (7, 290): (0, 0),    
    (7, 122): (33, 88),
    (7, 151): (46, 104),
    (7, 180): (56, 123),
    (7, 250): (85, 164), # Hard SAT CNFvsKNF test
    (7, 254): (165, 88), # Hard SAT CNFvsKNF test
    (7, 262): (170, 91), # Hard SAT CNFvsKNF test
}

# mode templates
MODE_NONE = ["None"]
MODE_STRUCTURAL = ["structural"]
MODE_BOUNDARY = ["U", "UB"]
MODE_NONE_BOUNDARY = ["None", "U", "UB"]
MODE_NONE_UB = ["None", "UB"]
MODE_UB = ["UB"]
MODE_ALL = ["None","structural", "U", "UB", "US", "UBS"]

# solver templates
SOLVER_KNF = [("KNF", 1)]
SOLVER_CNF= [("CNF", 0)]
SOLVER_BOTH = [("KNF", 1), ("CNF", 0)]

# vertical/horizontal constraint templates (-c value: if c=0 then v=1)
VH_BOTH   = [("ON", 1), ("OFF", 0)]
VH_BINARY = [("OFF", 0)]
VH_CARDINALITY = [("ON", 1)]

# point templates
TEMPLATES = {
    "k6_n50_test": dict(
        K=6, N=50, X=XY[(6,50)][0], Y=XY[(6,50)][1],
        SOLVER= [("KNF", 1)], VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE,
        SEEDS=1, WALLTIME="00:15:00",
        RUNNER="run_retry_4GB.sh",
        FILTER="3",
    ),

    "k6_n96_test": dict(
        K=6, N=96, X=XY[(6,96)][0], Y=XY[(6,96)][1],
        SOLVER= SOLVER_BOTH, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=2, WALLTIME="00:10:00",
        RUNNER="run_retry_4GB.sh",
        FILTER="3",
    ),

    #k6 n97
    "k6_n97_all": dict( 
        K=6, N=97, X=XY[(6,97)][0], Y=XY[(6,97)][1],
        SOLVER=SOLVER_BOTH, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="02:00:00",
        RUNNER="run_retry_4GB.sh",
        FILTER="8",
    ),

    #k6 n98
    "k6_n98_all": dict( 
        K=6, N=98, X=XY[(6,98)][0], Y=XY[(6,98)][1],
        SOLVER=SOLVER_BOTH, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="02:00:00",
        RUNNER="run_retry_4GB.sh",
        FILTER="8",
    ),

    #k7 n220
    "k7_n220_CNF": dict( 
        K=7, N=220, X=XY[(7,220)][0], Y=XY[(7,220)][1],
        SOLVER=[("CNF", 0)], VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="04:00:00",
        RUNNER="run_retry_8GB.sh",
        FILTER="10",
    ),
    "k7_n220_KNF": dict(
        K=7, N=220, X=XY[(7,220)][0], Y=XY[(7,220)][1],
        SOLVER=[("KNF", 1)], VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="04:00:00",
        RUNNER="run_retry_4GB.sh",
        FILTER="10",
    ),    

    #k7 n240
    "k7_n240_CNF": dict( 
        K=7, N=240, X=XY[(7,240)][0], Y=XY[(7,240)][1],
        SOLVER=[("CNF", 0)], VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="16:00:00",
        RUNNER="run_retry_8GB.sh",
        FILTER="10",
    ),    
    "k7_n240_KNF": dict( 
        K=7, N=240, X=XY[(7,240)][0], Y=XY[(7,240)][1],
        SOLVER=[("KNF", 1)], VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="16:00:00",
        RUNNER="run_retry_4GB.sh",
        FILTER="10",
    ),

    #k7 n261
    "k7_n261_CNF": dict(  
        K=7, N=261, X=XY[(7,261)][0], Y=XY[(7,261)][1],
        SOLVER=[("CNF", 0)], VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="36:00:00", # one always times out at 24h
        RUNNER="run_retry_12GB.sh",
        FILTER="10",
    ),
    "k7_n261_KNF": dict( 
        K=7, N=261, X=XY[(7,261)][0], Y=XY[(7,261)][1],
        SOLVER=[("KNF", 1)], VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="24:00:00",
        RUNNER="run_retry_4GB.sh",
        FILTER="10",
    ),
    
    #k7 n270 
    "k7_n270_KNF": dict( 
        K=7, N=270, X=XY[(7,270)][0], Y=XY[(7,270)][1],
        SOLVER=[("KNF", 1)], VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_UB,
        SEEDS=15, WALLTIME="36:00:00",
        RUNNER="run_retry_4GB.sh",
        FILTER="10",
    ),

    #k7 n280 KNF
    "k7_n280_KNF": dict( 
        K=7, N=280, X=XY[(7,280)][0], Y=XY[(7,280)][1],
        SOLVER=[("KNF", 1)], VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_UB,
        SEEDS=15, WALLTIME="36:00:00",
        RUNNER="run_retry_4GB.sh",
        FILTER="10",
    ),

    #k7 n290 KNF
    "k7_n290_KNF": dict( 
        K=7, N=290, X=XY[(7,290)][0], Y=XY[(7,290)][1],
        SOLVER=[("KNF", 1)], VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_UB,
        SEEDS=15, WALLTIME="36:00:00",
        RUNNER="run_retry_4GB.sh",
        FILTER="10",
    ),

    #k7 n122
    "k7_n122_all": dict( 
        K=7, N=122, X=XY[(7,122)][0], Y=XY[(7,122)][1],
        SOLVER=SOLVER_BOTH, VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="04:00:00",
        RUNNER="run_retry_4GB.sh",
        FILTER="10",
    ),

    #k7 n151
    "k7_n151_CNF": dict( 
        K=7, N=151, X=XY[(7,151)][0], Y=XY[(7,151)][1],
        SOLVER=[("CNF", 0)], VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="24:00:00",
        RUNNER="run_retry_4GB.sh",
        FILTER="10",
    ),
    "k7_n151_KNF": dict( 
        K=7, N=151, X=XY[(7,151)][0], Y=XY[(7,151)][1],
        SOLVER=[("KNF", 1)], VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="24:00:00",
        RUNNER="run_retry_4GB.sh",
        FILTER="10",
    ),

    #k7 n180
    "k7_n180_CNF": dict( 
        K=7, N=180, X=XY[(7,180)][0], Y=XY[(7,180)][1],
        SOLVER=[("CNF", 0)], VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="36:00:00",
        RUNNER="run_retry_4GB.sh",
        FILTER="10",
    ),
    "k7_n180_KNF": dict(  
        K=7, N=180, X=XY[(7,180)][0], Y=XY[(7,180)][1],
        SOLVER=[("KNF", 1)], VHCONSTRAINT=VH_BINARY, MODES=MODE_NONE_BOUNDARY,
        SEEDS=15, WALLTIME="36:00:00",
        RUNNER="run_retry_4GB.sh",
        FILTER="10",
    ),     

    # hard SAT tests
    # k7 n250
    "k7_n250_SAT_KNF": dict(  
    K=7, N=250, X=XY[(7,250)][0], Y=XY[(7,250)][1],
    SOLVER=[("KNF", 1)], VHCONSTRAINT=VH_BINARY, MODES=MODE_UB,
    SEEDS=15, WALLTIME="36:00:00",
    RUNNER="run_retry_4GB.sh",
    FILTER="10",
    ),   
    "k7_n250_SAT_CNF": dict(  
    K=7, N=250, X=XY[(7,250)][0], Y=XY[(7,250)][1],
    SOLVER=[("CNF", 0)], VHCONSTRAINT=VH_BINARY, MODES=MODE_UB,
    SEEDS=15, WALLTIME="36:00:00",
    RUNNER="run_retry_12GB.sh",
    FILTER="10",
    ),   

    # k7 n254
    "k7_n254_SAT_KNF": dict(  
    K=7, N=254, X=XY[(7,254)][0], Y=XY[(7,254)][1],
    SOLVER=[("KNF", 1)], VHCONSTRAINT=VH_BINARY, MODES=MODE_UB,
    SEEDS=15, WALLTIME="36:00:00",
    RUNNER="run_retry_4GB.sh",
    FILTER="10",
    ),   
    "k7_n254_SAT_CNF": dict(  
    K=7, N=254, X=XY[(7,254)][0], Y=XY[(7,254)][1],
    SOLVER=[("CNF", 0)], VHCONSTRAINT=VH_BINARY, MODES=MODE_UB,
    SEEDS=15, WALLTIME="36:00:00",
    RUNNER="run_retry_12GB.sh",
    FILTER="10",
    ),   

    # k7 n262
    "k7_n262_SAT_KNF": dict(  
    K=7, N=262, X=XY[(7,262)][0], Y=XY[(7,262)][1],
    SOLVER=[("KNF", 1)], VHCONSTRAINT=VH_BINARY, MODES=MODE_UB,
    SEEDS=15, WALLTIME="48:00:00",
    RUNNER="run_retry_4GB.sh",
    FILTER="10",
    ),   
    "k7_n262_SAT_CNF": dict(  
    K=7, N=262, X=XY[(7,262)][0], Y=XY[(7,262)][1],
    SOLVER=[("CNF", 0)], VHCONSTRAINT=VH_BINARY, MODES=MODE_UB,
    SEEDS=15, WALLTIME="48:00:00",
    RUNNER="run_retry_12GB.sh",
    FILTER="10",
    ),  

}    # k7: 20 works for n180 and n261; n50 <=2; n100 <= 7; n120 <= 15;  n150 <= 14; n200 <= 19; n250 <= 21; n261 ~= 20

S = 1  # symmetry break always on

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

def build_job_name(K,N,form_name,c_val,mode,seed):
    mode_tag = mode.replace(" ", "")
    return f"k{K}_n{N}_{form_name}_c{c_val}_{mode_tag}_seed{seed}"

def submit_job(*, walltime, runner, K,N,X,Y, S, C_VAL, V_VAL, A_VAL, L_VAL, B_VAL, F_VAL, seed, filter_thresh):
    cmd = [
        "sbatch",
        f"--time={walltime}",
        f"--exclude=fc30464",
        f"--job-name={build_job_name(K,N, 'KNF' if F_VAL==1 else 'CNF', C_VAL, 'NA', seed)}",
        runner,
        "-k", str(K), "-n", str(N), "-x", str(X), "-y", str(Y), "-s", str(S),
        "-c", str(C_VAL), "-v", str(V_VAL), "-a", str(A_VAL), "-l", str(L_VAL), "-b", str(B_VAL),
        "-f", str(F_VAL), "-r", str(seed), "-t", str(0), "-j", str(filter_thresh)
    ]
    job_name = build_job_name(K,N, 'KNF' if F_VAL==1 else 'CNF', C_VAL, f"v{V_VAL}_a{A_VAL}_l{L_VAL}_b{B_VAL}", seed)
    cmd[2] = f"--job-name={job_name}"

    print(f"[{ts()}] SUB: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("template", help="e.g. k7_n261_all")
    args = p.parse_args()

    if args.template not in TEMPLATES:
        print("Unknown template:", args.template)
        print("Valid keys:", ", ".join(sorted(TEMPLATES.keys())))
        sys.exit(1)

    cfg = TEMPLATES[args.template]
    K, N, X, Y = cfg["K"], cfg["N"], cfg["X"], cfg["Y"]
    solver   = cfg["SOLVER"]
    vhcon = cfg["VHCONSTRAINT"]
    modes   = cfg["MODES"]
    seeds   = cfg["SEEDS"]
    walltime = cfg["WALLTIME"]
    runner  = cfg["RUNNER"]
    filter_thresh = cfg["FILTER"]

    total = len(solver) * len(vhcon) * len(modes) * seeds
    print(f"[{ts()}] Template={args.template}: submitting {total} jobs")

    for form_name, f_val in solver:
        for vhc_name, c_val in vhcon:
            for mode in modes:
                v_val, a_val, l_val, b_val = params_for_mode(mode, c_val)
                for seed in range(1, seeds + 1):
                    submit_job(
                        walltime=walltime,
                        runner=runner,
                        K=K, N=N, X=X, Y=Y, S=S,
                        C_VAL=c_val, V_VAL=v_val, A_VAL=a_val, L_VAL=l_val, B_VAL=b_val,
                        F_VAL=f_val, seed=seed, filter_thresh=filter_thresh
                    )
                    time.sleep(1)

    print(f"[{ts()}] Done.")

if __name__ == "__main__":
    main()
