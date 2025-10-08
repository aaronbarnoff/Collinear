#!/usr/bin/env python3
import shutil
from pathlib import Path

def sanitize_pwd(p: Path) -> str:
    # '/home/barnoffa/scratch/heur/no_cubing/Collinear' -> 'home__barnoffa__scratch__heur__no_cubing__Collinear'
    return p.as_posix().lstrip("/").replace("/", "__")

def main():
    src_root = Path.cwd()
    tag = sanitize_pwd(src_root)
    dst_root = Path("/home/barnoffa/slurm_backups") / tag

    count = 0
    for p in src_root.rglob("slurm-*.out"):
        if not p.is_file():
            continue
        rel = p.relative_to(src_root)
        dest = dst_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
        print(f"copied: {p} -> {dest}")
        count += 1

    print(f"\nBackup root: {dst_root}")
    print(f"Done. Copied {count} files.")

if __name__ == "__main__":
    main()
