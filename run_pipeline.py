"""Run the whole Tinker + OpenRouter side end to end (everything except the Kaggle GPU stage).

    python run_pipeline.py                 # all stages
    python run_pipeline.py --from rl       # resume from a stage
    python run_pipeline.py --only monitors

Stages: data -> sft -> dry -> rl -> monitors -> spillover -> export -> analyze
The dry run measures real cost per step; RL steps are then trimmed automatically to fit the
remaining Tinker budget (cut steps first, as the design doc says).
"""

import argparse
import json
import math
import subprocess
import sys

from common import DATA, LEDGER, ROOT, RUNS, TINKER_BUDGET, read_jsonl, spent

STAGES = ["data", "sft", "dry", "rl", "monitors", "spillover", "export", "analyze"]
MAIN_ARMS = ["principled", "pragmatic"]
EXT_ARMS = ["permission", "neutral"]  # "nochar" was dropped: base reasoning overran max_tokens


def sh(*cmd):
    print("\n$ python", " ".join(cmd), flush=True)
    r = subprocess.run([sys.executable, "-u", *cmd])
    if r.returncode:
        sys.exit(f"stage failed: {' '.join(cmd)}")


def stage_data():
    if not (DATA / "tasks.jsonl").exists():
        sh("gen_tasks.py", "--n-batches", "30")  # ~45% of candidates survive validation
    if len(read_jsonl(DATA / "tasks.jsonl")) < 60:
        sh("gen_tasks.py", "--n-batches", "40", "--target", "70")
    if not (DATA / "dialogues_pragmatic.jsonl").exists():
        sh("gen_text.py", "dialogues")
    if not (DATA / "cheat_pairs.jsonl").exists():
        sh("gen_text.py", "pairs")
    if not (DATA / "spillover.jsonl").exists():
        sh("gen_text.py", "spillover")


def stage_sft():
    if not (DATA / "dialogues_neutral.jsonl").exists():
        sh("gen_text.py", "neutral")
    for c in MAIN_ARMS + ["neutral"]:
        if not (RUNS / f"sft_{c}" / "final.json").exists():
            sh("sft.py", "--character", c)


def stage_dry():
    if not (RUNS / "dry_rl_pragmatic_s0" / "metrics.jsonl").exists():
        sh("rl.py", "--arm", "pragmatic", "--seed", "0", "--dry-run")


def plan_steps(n_runs: int) -> int:
    ms = read_jsonl(RUNS / "dry_rl_pragmatic_s0" / "metrics.jsonl")
    per_step = sum(m["cost"] for m in ms) / len(ms) * 1.15  # later steps run longer as reasoning grows
    remaining = TINKER_BUDGET - spent("tinker") - 0.6  # keep room for spillover sampling
    steps = min(30, math.floor(remaining / (per_step * n_runs)))
    hacks = sum(m["hacked"] for m in ms)
    print(f"dry run: ${per_step / 1.15:.3f}/step measured, {hacks} hacks in {len(ms)} steps; "
          f"${remaining:.2f} left for {n_runs} runs -> {steps} steps each")
    if steps < 10:
        sys.exit("budget too tight for a meaningful run; lower --max-tokens / --group-size or raise TINKER_BUDGET")
    return steps


def stage_rl(with_ext: bool):
    # Steps are sized once so that every planned arm fits TINKER_BUDGET; main arms run first, and the
    # extension arms reuse the same step count (so arms stay comparable) once the budget covers them.
    plan_f = RUNS / "rl_plan.json"
    arms = MAIN_ARMS + (EXT_ARMS if with_ext else [])
    if plan_f.exists():
        plan = json.loads(plan_f.read_text())
    else:
        plan = {"arms": arms, "steps": plan_steps(len(arms) * 2)}
        plan_f.write_text(json.dumps(plan))
    rl_args = ["--steps", str(plan["steps"]), *plan.get("rl_args", [])]
    sh("launch_rl.py", "--arms", *MAIN_ARMS, "--", *rl_args)
    if not with_ext:
        return
    # extension arms may run fewer steps than the main arms (doc: cut steps before seeds); they are then
    # compared with the main arms' checkpoint at the same step
    ext_steps = plan.get("ext_steps", plan["steps"])
    ledger = [r for r in read_jsonl(LEDGER) if r["service"] == "tinker"]
    main_rows = [r for r in ledger if r["what"].split("_s")[0] in {f"rl_{a}" for a in MAIN_ARMS}]
    per_run_step = sum(r["usd"] for r in main_rows) / max(1, len(main_rows))
    ext_done = sum(r["usd"] for r in ledger if r["what"].split("_s")[0] in {f"rl_{a}" for a in EXT_ARMS})
    need = per_run_step * len(EXT_ARMS) * 2 * ext_steps - ext_done + 0.6
    left = TINKER_BUDGET - spent("tinker")
    if need > left:
        sys.exit(f"extension arms need ~${need:.2f}, only ${left:.2f} left under TINKER_BUDGET. "
                 "Add the credit, raise TINKER_BUDGET in .env, then: python run_pipeline.py --from rl")
    sh("launch_rl.py", "--arms", *EXT_ARMS, "--", "--steps", str(ext_steps), *plan.get("rl_args", []))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", choices=STAGES, default="data")
    ap.add_argument("--only", choices=STAGES)
    ap.add_argument("--no-extension", action="store_true", help="skip permission + no-character arms")
    args = ap.parse_args()
    todo = [args.only] if args.only else STAGES[STAGES.index(args.start):]
    for s in todo:
        print(f"\n===== {s} =====  (Tinker spent so far ${spent('tinker'):.2f}, OpenRouter ${spent('openrouter'):.2f})")
        if s == "data":
            stage_data()
        elif s == "sft":
            stage_sft()
        elif s == "dry":
            stage_dry()
        elif s == "rl":
            stage_rl(not args.no_extension)
        elif s == "monitors":
            sh("monitors.py")
        elif s == "spillover":
            sh("spillover.py")
        elif s == "export":
            sh("export_for_kaggle.py", "--out", str(ROOT / "kaggle_bundle_full"))
        elif s == "analyze":
            sh("analyze.py")
    print(f"\nDone. Tinker ${spent('tinker'):.2f}, OpenRouter ${spent('openrouter'):.2f}. "
          "Next: upload kaggle_bundle/ to Kaggle (see README), then copy acts/ back and rerun analyze.py.")


if __name__ == "__main__":
    main()
