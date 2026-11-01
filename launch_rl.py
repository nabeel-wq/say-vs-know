"""Launch several RL runs in parallel (one subprocess each, logs in runs/<name>/stdout.log).

    python launch_rl.py                                   # main 4: {principled,pragmatic} x seeds {0,1}
    python launch_rl.py --arms permission nochar          # the $10 extension arms
    python launch_rl.py --arms principled pragmatic permission nochar   # all 8
"""

import argparse
import subprocess
import sys

from common import RUNS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", nargs="+", default=["principled", "pragmatic"])
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    ap.add_argument("extra", nargs=argparse.REMAINDER, help="passed through to rl.py, after --")
    args = ap.parse_args()
    extra = [a for a in args.extra if a != "--"]
    procs = []
    for arm in args.arms:
        for seed in args.seeds:
            name = f"rl_{arm}_s{seed}"
            (RUNS / name).mkdir(exist_ok=True)
            log = open(RUNS / name / "stdout.log", "a", encoding="utf-8")
            p = subprocess.Popen([sys.executable, "-u", "rl.py", "--arm", arm, "--seed", str(seed), *extra],
                                 stdout=log, stderr=subprocess.STDOUT)
            procs.append((name, p))
            print(f"started {name} (pid {p.pid})")
    failed = []
    for name, p in procs:
        rc = p.wait()
        print(f"{name} exited {rc}")
        if rc:
            failed.append(name)
    if failed:
        sys.exit(f"failed: {failed} (see runs/<name>/stdout.log; rerun resumes from last checkpoint)")


if __name__ == "__main__":
    main()
