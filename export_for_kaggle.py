"""Download Tinker sampler checkpoints and pack everything the GPU stage needs.

Output: kaggle_bundle/  (upload as a private Kaggle dataset named e.g. "hidden-hacks-bundle")
  adapters/<run>/step0005/...   only with --download; otherwise the notebook pulls each LoRA
                                from Tinker by the sampler path in manifest.json
  episodes.jsonl                compact episodes (tokens + labels, no text)
  groups.jsonl                  prompt tokens per group
  cheat_pairs.jsonl, tasks.jsonl, manifest.json

    python export_for_kaggle.py                      # every saved checkpoint of every rl_* run
    python export_for_kaggle.py --steps 0 10 20 30   # subset
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from common import DATA, ROOT, RUNS, read_jsonl, write_jsonl

BUNDLE = ROOT / "kaggle_bundle"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="*")
    ap.add_argument("--steps", nargs="*", type=int)
    ap.add_argument("--clean-frac", type=float, default=0.25, help="share of clean-task episodes kept")
    ap.add_argument("--before-step", type=int, default=None,
                    help="only episodes before this step (for an early bundle while runs continue)")
    ap.add_argument("--download", action="store_true",
                    help="also bundle the adapters (default: Kaggle fetches them from Tinker itself)")
    ap.add_argument("--out", default=str(BUNDLE))
    args = ap.parse_args()
    from tinker_cookbook import weights

    bundle = Path(args.out)
    bundle.mkdir(exist_ok=True)
    runs = args.runs or sorted(p.name for p in RUNS.glob("rl_*") if (p / "checkpoints.jsonl").exists())
    manifest = {"runs": {}}
    all_eps, all_groups = [], []
    for run in runs:
        recs = [r for r in read_jsonl(RUNS / run / "checkpoints.jsonl") if r.get("sampler_path")]
        steps = sorted({int(r["step"]) for r in recs if args.steps is None or int(r["step"]) in args.steps})
        cfg = json.loads((RUNS / run / "config.json").read_text())
        manifest["runs"][run] = {"arm": cfg["arm"], "seed": cfg["seed"], "steps": steps,
                                 "sampler_paths": {str(int(r["step"])): r["sampler_path"] for r in recs
                                                   if int(r["step"]) in steps},
                                 # Tinker no longer serves sampler archives; state checkpoints download
                                 # through an external-weights export (already PEFT-named LoRA)
                                 "state_paths": {str(int(r["step"])): r["state_path"] for r in recs
                                                 if int(r["step"]) in steps}}
        for r in recs:
            s = int(r["step"])
            if s not in steps or not args.download:
                continue
            out = bundle / "adapters" / run / f"step{s:04d}"
            if out.exists() and any(out.iterdir()):
                continue
            print(f"downloading {run} step {s}")
            weights.download(tinker_path=r["state_path"], output_dir=str(out))
        for e in read_jsonl(RUNS / run / "episodes.jsonl"):
            if args.before_step is not None and e["step"] >= args.before_step:
                continue
            h = int(hashlib.md5(e["episode_id"].encode()).hexdigest()[:8], 16)
            if not e["bugged"] and (h % 1000) / 1000 >= args.clean_frac:
                continue
            all_eps.append({k: e[k] for k in ("episode_id", "group_id", "run", "arm", "seed", "step", "task_id",
                                              "bugged", "hacked", "honest_correct", "has_code", "reward",
                                              "truncated", "think_end_pos", "completion_tokens",
                                              "sampled_logprobs")})
        all_groups += read_jsonl(RUNS / run / "groups.jsonl")
    keep_groups = {e["group_id"] for e in all_eps}
    write_jsonl(bundle / "episodes.jsonl", all_eps)
    write_jsonl(bundle / "groups.jsonl", [g for g in all_groups if g["group_id"] in keep_groups])
    for f in ("cheat_pairs.jsonl", "tasks.jsonl"):
        shutil.copy(DATA / f, bundle / f)
    shutil.copy(ROOT / "kaggle_activations.py", bundle / "kaggle_activations.py")
    (bundle / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"bundle ready: {bundle} ({len(all_eps)} episodes). Upload it as a Kaggle dataset; "
          "see README for the notebook cell.")


if __name__ == "__main__":
    main()
