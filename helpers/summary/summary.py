#!/usr/bin/env python3
import re, csv, statistics
from pathlib import Path
from collections import defaultdict

SLURM_DIR = str(Path.cwd().parents[1])
OUTPUT_SUMMARY = "summary.csv"
OUTPUT_TABLES  = "tables.csv"
SLURM_PATTERNS = ("slurm-*.out",)
failures_to_redo = []

KEYS = ["k","n","x","y","symBreak","VHCard","VHBinary","antidiag","lineLen","boundary","KNF","timeout","encoding","k_plus_c","status"]
GROUP_KEYS = ["k","n","x","y","symBreak","VHCard","VHBinary","antidiag","lineLen","boundary","KNF","timeout","encoding","k_plus_c"]

SAT_RE = re.compile(r"\bSAT\s+([0-9]+(?:\.[0-9]+)?)s\b")
UNSAT_RE = re.compile(r"\bUNSAT\s+([0-9]+(?:\.[0-9]+)?)s\b")
FINISH_RE = re.compile(r"Finished SAT solver:\s+([0-9]+(?:\.[0-9]+)?)\s+seconds")
PARAM_LINE = re.compile(r"^k:\s*\d+.*", re.IGNORECASE|re.MULTILINE)
ENC_RE = re.compile(r"encoding:\s*([^,\s]+)", re.IGNORECASE)
TIMEOUT_RE = re.compile(r"timeout:\s*([0-9]+)", re.IGNORECASE)
KPLUSC_RE = re.compile(r"\(k\+c\)\s*:\s*([0-9]+)")
CARD_NO = "cardinality constraint: No heuristic"
CARD_K10_A = "cardinality constraint: Line-length filter heuristic - only include length at least k+10"
CARD_K10_B = "cardinality constraint: Linelength filter heuristic - only include length at least k+10"

HEADER_RE = re.compile(r"^/.*/res_k-?\d+_n-?\d+_x-?\d+_y-?\d+.*$", re.MULTILINE)
CANCEL_LINE_RE = re.compile(r"slurmstepd:\s*error:\s*\*\*\*\s*JOB\s+\d+\s+ON\s+\S+\s+CANCELLED\s+AT\s+.*", re.IGNORECASE)
TIME_LIMIT_TAG = re.compile(r"DUE TO TIME LIMIT", re.IGNORECASE)
FAILURE_RE = re.compile(r"\bFailure\b", re.IGNORECASE)

def _i(v,d=0):
    s=str(v or "").strip()
    try: return int(float(s)) if s!="" else d
    except: return d
def _f(v,d=0.0):
    s=str(v or "").strip()
    try: return float(s) if s!="" else d
    except: return d
def _t(v):
    s=str(v or "").strip()
    try: return float(s) if s!="" else float("inf")
    except: return float("inf")

def sort_cols(r):
    return (_i(r.get("k")),_i(r.get("n")),_i(r.get("x")),_i(r.get("y")),_i(r.get("symBreak")),_i(r.get("VHCard")),_i(r.get("VHBinary")),_i(r.get("antidiag")),_i(r.get("lineLen")),_f(r.get("boundary")),_i(r.get("KNF")),_i(r.get("timeout")),r.get("encoding") or "",_i(r.get("k_plus_c")),r.get("status") or "")

def sort_summary_key(r):
    return (_i(r.get("k")),_i(r.get("n")),_i(r.get("x")),_i(r.get("y")),_i(r.get("symBreak")),_i(r.get("VHCard")),_i(r.get("VHBinary")),_i(r.get("antidiag")),_i(r.get("lineLen")),_f(r.get("boundary")),_i(r.get("KNF")),_i(r.get("timeout")),r.get("encoding") or "",_i(r.get("k_plus_c")),_t(r.get("time")),r.get("status") or "")

def parse_params_line(line):
    kv={}
    for part in line.split(","):
        part=part.strip()
        if ":" in part:
            k,v = part.split(":",1)
            kv[k.strip()] = v.strip()
    return {
        "k":kv.get("k",""), "n":kv.get("n",""), "x":kv.get("x",""), "y":kv.get("y",""),
        "symBreak":kv.get("sym_break",""), "VHCard":kv.get("vh_card",""),
        "VHBinary":kv.get("vh_line",""), "antidiag":kv.get("antidiag",""),
        "lineLen":kv.get("cutoff",""), "boundary":kv.get("boundary",""),
        "KNF":kv.get("solver",""), "timeout":kv.get("timeout",""), "encoding":kv.get("encoding","")
    }

def blocks(text):
    hs=list(HEADER_RE.finditer(text))
    if not hs:
        yield (None, text)
        return
    for i,h in enumerate(hs):
        a=h.start()
        b=hs[i+1].start() if i+1<len(hs) else len(text)
        yield (text[h.start():text.find("\n",h.start())], text[a:b])

def scan():
    root=Path(SLURM_DIR); files=[]
    for pat in SLURM_PATTERNS: files+=list(root.glob(pat))
    for p in sorted(files):
        try:
            text=p.read_text(errors="ignore")
        except:
            continue

        for header, block in blocks(text):
            cancel=CANCEL_LINE_RE.search(block)
            time_limit=bool(cancel and TIME_LIMIT_TAG.search(block))

            if cancel and not time_limit:
                continue

            mline = PARAM_LINE.search(block)
            if not mline:
                continue

            params = parse_params_line(mline.group(0))
            if not all(params[k] for k in ["k","n","x","y","symBreak","VHCard","VHBinary","antidiag","lineLen","boundary","KNF"]):
                continue

            encoding=(ENC_RE.search(block).group(1) if ENC_RE.search(block) else params["encoding"])
            timeout=(TIMEOUT_RE.search(block).group(1) if TIMEOUT_RE.search(block) else params["timeout"])

            k_heuristic = KPLUSC_RE.search(block)
            if k_heuristic: 
                k_plus_c = k_heuristic.group(1)
            else:
                if CARD_NO in block: 
                    k_plus_c="0"
                elif (CARD_K10_A in block) or (CARD_K10_B in block): 
                    k_plus_c="10"
                else:
                    k_plus_c=""

            status="RUNNING"
            wall=None

            if FAILURE_RE.search(block):
                status="FAILURE"
                wall=None
                mt = SAT_RE.search(block)
                if not mt:
                    mt = FINISH_RE.search(block)
                fail_time = mt.group(1) if mt else "?"
                failures_to_redo.append(f"{p.name}\t{(header or str(p)).strip()}\t{fail_time}s")
            else:
                mu=UNSAT_RE.search(block)
                msat=SAT_RE.search(block)
                mf=FINISH_RE.search(block)
                if mu and (not msat or mu.start()<msat.start()): 
                    status="UNSAT" 
                    wall=float(mu.group(1))
                elif msat: 
                    status="SAT"; wall=float(msat.group(1))
                elif mf: 
                    status="SAT"; wall=float(mf.group(1))

                if time_limit: 
                    status="TIME_LIMIT" 
                    wall=None

            row = dict(params)
            row.update({"encoding":encoding,"timeout":timeout,"k_plus_c":k_plus_c,"status":status,"slurm":p.name,"time":(None if wall is None else round(wall,2)),"path":(header or str(p))})
            yield row

def median_with_infs(total, times_sorted):
    m=(total+1)//2
    return (round(times_sorted[m-1],2), m) if len(times_sorted)>=m else (float("inf"), m)

def main():
    rows=list(scan())

    summary_headers=KEYS+["slurm","time","path"]
    summary_rows=[{k:r.get(k,"") for k in summary_headers} for r in rows]
    summary_rows.sort(key=sort_summary_key)
    with open(OUTPUT_SUMMARY,"w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=summary_headers); w.writeheader(); w.writerows(summary_rows)

    times_by=defaultdict(list)
    total_by=defaultdict(int)
    status_by=defaultdict(set)
    for r in rows:
        gkey=tuple(r[k] for k in GROUP_KEYS)
        total_by[gkey]+=1
        status_by[gkey].add(r["status"])
        if r["time"] is not None: 
            times_by[gkey].append(r["time"])

    out=[]; mx=0
    for gkey in sorted(total_by.keys()):
        sorted_times=sorted(times_by.get(gkey,[]))
        cnt=total_by[gkey]; mx=max(mx,cnt)
        status = list(status_by[gkey])[0] if len(status_by[gkey])==1 else "MIXED"
        med, pos = median_with_infs(cnt, sorted_times)
        avg=round(statistics.mean(sorted_times),2) if sorted_times else float("inf")
        minv=round(sorted_times[0],2) if sorted_times else float("inf")
        maxv=round(sorted_times[-1],2) if sorted_times else float("inf")
        row=dict(zip(GROUP_KEYS,gkey)) 
        row.update({"status":status,"count":cnt,"avg":avg,"min":minv,"max":maxv,"median":med})
        out.append(row)
        print(f"[GROUP] k={row['k']} n={row['n']} x={row['x']} y={row['y']} f={row['KNF']} b={row['boundary']} k+c={row['k_plus_c']} status={row['status']} | count={cnt} median_pos={pos} median_val={'inf' if med==float('inf') else med}")

    out.sort(key=sort_cols)
    table_headers=KEYS+["count","avg","min","max","median"]
    with open(OUTPUT_TABLES,"w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=table_headers); w.writeheader(); w.writerows(out)

    sum_meds=round(sum(r["median"] for r in out if isinstance(r["median"],float) and r["median"]!=float("inf")),2)
    done=sum(1 for r in out if isinstance(r["median"],float) and r["median"]!=float("inf"))
    print(f"Writing per-instance summary: {OUTPUT_SUMMARY}")
    print(f"Writing grouped table: {OUTPUT_TABLES}")
    print(f"Sum of finite medians across {done} completed groups: {sum_meds}")
    print(f"Max count overall: {mx}")

    if failures_to_redo:
        print("failures to redo:")
        for path in failures_to_redo:
            print(path)

if __name__=="__main__":
    main()
