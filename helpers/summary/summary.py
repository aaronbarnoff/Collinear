#!/usr/bin/env python3
import re, csv, statistics
from pathlib import Path
from collections import defaultdict

SLURM_DIR = str(Path.cwd().parents[1])
OUTPUT_SUMMARY = "summary.csv"
OUTPUT_TABLES  = "tables.csv"
SLURM_PATTERNS = ("slurm-*.out",)

KEYS = ["k","n","x","y","symBreak","VHCard","VHBinary","antidiag","lineLen","boundary","KNF","timeout","encoding","k_plus_c","status"]
GROUP_KEYS = ["k","n","x","y","symBreak","VHCard","VHBinary","antidiag","lineLen","boundary","KNF","timeout","encoding","k_plus_c"]

RES_RE = re.compile(r"res_k(?P<k>-?\d+)_n(?P<n>-?\d+)_x(?P<x>-?\d+)_y(?P<y>-?\d+)_s(?P<symBreak>-?\d+)_c(?P<VHCard>-?\d+)_v(?P<VHBinary>-?\d+)_a(?P<antidiag>-?\d+)_l(?P<lineLen>-?\d+)_b(?P<boundary>-?\d+(?:\.\d+)?)_f(?P<KNF>-?\d+)_r(?P<seed>-?\d+)(?:_[A-Za-z0-9.-]+)*")
SAT_RE = re.compile(r"\bSAT\s+([0-9]+(?:\.[0-9]+)?)s\b")
UNSAT_RE = re.compile(r"\bUNSAT\s+([0-9]+(?:\.[0-9]+)?)s\b")
FINISH_RE = re.compile(r"Finished SAT solver:\s+([0-9]+(?:\.[0-9]+)?)\s+seconds")
PARAMS_RE = re.compile(r"encoding:\s*([^,\s]+)", re.IGNORECASE)
TIMEOUT_RE = re.compile(r"timeout:\s*([0-9]+)", re.IGNORECASE)
KPLUS_RE = re.compile(r"k\+([0-9]+)")
CANCEL_LINE_RE = re.compile(r"slurmstepd:\s*error:\s*\*\*\*\s*JOB\s+\d+\s+ON\s+\S+\s+CANCELLED\s+AT\s+.*", re.IGNORECASE)
TIME_LIMIT_TAG = re.compile(r"DUE TO TIME LIMIT", re.IGNORECASE)

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

def _dir_line(text,m):
    a=text.rfind("\n",0,m.start())+1; b=text.find("\n",m.end()); b=len(text) if b==-1 else b
    return text[a:b].strip()

def scan():
    files=[]; root=Path(SLURM_DIR)
    for pat in SLURM_PATTERNS: files+=root.glob(pat)
    for p in sorted(files):
        try: text=p.read_text(errors="ignore")
        except: continue
        ms=list(RES_RE.finditer(text))
        for i,m in enumerate(ms):
            a=m.start(); b=ms[i+1].start() if i+1<len(ms) else len(text)
            block=text[a:b]; g=m.groupdict(); header=_dir_line(text,m); lf=str(p)
            cancel=CANCEL_LINE_RE.search(block); tl=bool(cancel and TIME_LIMIT_TAG.search(block))
            if cancel and not tl:
                print(f"SKIP[MANUAL_CANCEL] {header}"); continue
            blk=block.lower()
            if not tl and ("failure" in blk or "error" in blk):
                tag="FAILURE" if "failure" in blk else "ERROR"
                print(f"SKIP[{tag}] {header} | slurm_file={lf}"); continue
            status="RUNNING"; wall=None
            mu=UNSAT_RE.search(block); msat=SAT_RE.search(block); mf=FINISH_RE.search(block)
            if mu and (not msat or mu.start()<msat.start()): status="UNSAT"; wall=float(mu.group(1))
            elif msat: status="SAT"; wall=float(msat.group(1))
            elif mf: status="SAT"; wall=float(mf.group(1))
            if tl: status="TIME_LIMIT"; wall=None
            enc=(PARAMS_RE.search(block).group(1) if PARAMS_RE.search(block) else "")
            tout=(TIMEOUT_RE.search(block).group(1) if TIMEOUT_RE.search(block) else "0")
            kpc=(KPLUS_RE.search(block).group(1) if KPLUS_RE.search(block) else "")
            yield {"k":g["k"],"n":g["n"],"x":g["x"],"y":g["y"],"symBreak":g["symBreak"],"VHCard":g["VHCard"],
                   "VHBinary":g["VHBinary"],"antidiag":g["antidiag"],"lineLen":g["lineLen"],"boundary":g["boundary"],
                   "KNF":g["KNF"],"timeout":tout,"encoding":enc,"k_plus_c":kpc,"status":status,
                   "time":(None if wall is None else round(wall,2)),"path":header}

def median_with_infs(total, times_sorted):
    m=(total+1)//2
    return (round(times_sorted[m-1],2), m) if len(times_sorted)>=m else (float("inf"), m)

def main():
    rows=list(scan())

    summary_headers=KEYS+["time","path"]
    summary_rows=[{k:r.get(k,"") for k in summary_headers} for r in rows]
    summary_rows.sort(key=sort_summary_key)
    with open(OUTPUT_SUMMARY,"w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=summary_headers); w.writeheader(); w.writerows(summary_rows)

    times_by=defaultdict(list); total_by=defaultdict(int); status_by=defaultdict(set)
    for r in rows:
        gkey=tuple(r[k] for k in GROUP_KEYS)
        total_by[gkey]+=1; status_by[gkey].add(r["status"])
        if r["time"] is not None: times_by[gkey].append(r["time"])

    out=[]; mx=0
    for gkey in sorted(total_by.keys()):
        ts=sorted(times_by.get(gkey,[])); cnt=total_by[gkey]; mx=max(mx,cnt)
        status = list(status_by[gkey])[0] if len(status_by[gkey])==1 else "MIXED"
        med, pos = median_with_infs(cnt, ts)
        avg=round(statistics.mean(ts),2) if ts else float("inf")
        mn=round(ts[0],2) if ts else float("inf")
        mxv=round(ts[-1],2) if ts else float("inf")
        row=dict(zip(GROUP_KEYS,gkey)); row.update({"status":status,"count":cnt,"avg":avg,"min":mn,"max":mxv,"median":med})
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

if __name__=="__main__":
    main()