#!/usr/bin/env python3
import sys
from pathlib import Path
from collections import deque

def sanitize_pwd(p: Path) -> str:
    return p.as_posix().lstrip("/").replace("/", "__")

def keep_positive_v_line(line: str):
    s = line.lstrip(" \t")
    leading = line[:len(line) - len(s)]
    if not s.startswith("v"):
        return line
    toks = s[1:].strip().split()
    kept = [t for t in toks if not t.startswith("-")]
    if not kept:
        return None
    return f"{leading}v {' '.join(kept)}\n"

def process_file(src: Path, dst: Path) -> bool:
    head = []
    tail = deque(maxlen=75)
    s_lines = []
    v_lines = []
    try:
        with src.open(errors="ignore") as f:
            for i, line in enumerate(f):
                if i < 50:
                    head.append(line)
                tail.append(line)
                stripped = line.lstrip(" \t")
                if stripped.startswith("s"):
                    s_lines.append(line)
                elif stripped.startswith("v"):
                    vline = keep_positive_v_line(line)
                    if vline:
                        v_lines.append(vline)
    except Exception as e:
        print(f"skip (read error): {src} ({e})", flush=True)
        return False

    out = []
    out.append("First 50 lines:\n")
    out.extend(head)
    out.append("\nLast 75 lines:\n")
    out.extend(list(tail))
    out.append("\nSolution:\n")
    out.append("s\n")
    out.extend(s_lines)
    out.append("v\n")
    out.extend(v_lines)

    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        with dst.open("w") as g:
            g.writelines(out)
    except Exception as e:
        print(f"skip (write error): {dst} ({e})", flush=True)
        return False

    print(f"saved: {src} -> {dst}", flush=True)
    return True

def main():
    src_root = Path.cwd()
    tag = sanitize_pwd(src_root)
    dst_root = Path("/home/barnoffa/slurm_backups") / tag

    patterns = ("satOutput.log", "solverLog_*.txt")
    total = 0
    scanned = 0

    for pat in patterns:
        for p in src_root.rglob(pat):
            if not p.is_file():
                continue
            rel = p.relative_to(src_root)
            dest = dst_root / rel
            if process_file(p, dest):
                total += 1
            scanned += 1
            if scanned % 200 == 0:
                print(f"...processed {scanned} files so far", flush=True)

    print(f"\nBackup root: {dst_root}", flush=True)
    print(f"Done. Saved {total} files.", flush=True)

if __name__ == "__main__":
    sys.exit(main())
