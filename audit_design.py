"""Design audit: could a flaw (truncation, label validity, pooling, checkpoint mismatch, probe reading words)
explain the weak probe results?

usage: python audit_design.py    # writes results/audit_design.json (takes ~3 min, reads every acts/ file)
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HH = Path(__file__).resolve().parent
OUT = HH / "results" / "audit_design.json"
sys.path.insert(0, str(HH))
from analyze import ACTS, DATA, hack_kind, load_episodes, load_npz, reasoning_only, says_labels, synth_direction  # noqa: E402
from common import read_jsonl  # noqa: E402

rng = np.random.default_rng(0)
eps = {e["episode_id"]: e for e in load_episodes()}
tasks = {t["id"]: t for t in read_jsonl(DATA / "tasks.jsonl")}
says = says_labels()
prompt_len = {g["group_id"]: len(g["prompt_tokens"]) for g in read_jsonl(HH / "kaggle_bundle_full" / "groups.jsonl")}
bundle = {e["episode_id"] for e in read_jsonl(HH / "kaggle_bundle_full" / "episodes.jsonl")}
out = {}

# ---- 1. truncation in the activation pass (max_len 2048) and in RL (max_tokens 1024)
clipped = [i for i in bundle if eps[i].get("think_end_pos") is not None
           and prompt_len[eps[i]["group_id"]] + eps[i]["think_end_pos"] + 1 > 2048]
out["act_pass_clipped"] = {"n": len(clipped), "hacked": sum(eps[i]["hacked"] for i in clipped)}
out["rl_truncated"] = {}
for a in sorted({e["arm"] for e in eps.values()}):
    es = [e for e in eps.values() if e["arm"] == a]
    tr = [e for e in es if e["truncated"]]
    out["rl_truncated"][a] = {"rate": len(tr) / len(es), "truncated_and_hacked": sum(e["hacked"] for e in tr),
                              "bugged_trunc_rate": np.mean([e["truncated"] for e in es if e["bugged"]])}


# ---- 2. reasoning length
def rlen(e):
    return e["think_end_pos"] if e.get("think_end_pos") is not None else len(e["completion_tokens"])


out["reasoning_tokens"] = {}
for a in sorted({e["arm"] for e in eps.values()}):
    L = np.array([rlen(e) for e in eps.values() if e["arm"] == a and e["bugged"]])
    H = np.array([rlen(e) for e in eps.values() if e["arm"] == a and e["hacked"]])
    out["reasoning_tokens"][a] = {"median": float(np.median(L)), "p90": float(np.percentile(L, 90)),
                                  "share_under_30": float(np.mean(L < 30)), "median_hacked": float(np.median(H))}


# ---- 3. hack type from the code: literal special-case vs edge-case input vs rule change
kinds = {i: hack_kind(e, tasks) for i, e in eps.items() if e["hacked"]}
out["hack_kinds"] = {}
for a in sorted({e["arm"] for e in eps.values()}):
    c = defaultdict(lambda: [0, 0, 0])
    for i, k in kinds.items():
        if eps[i]["arm"] == a:
            c[k][0] += 1
            if i in says:
                c[k][1] += 1
                c[k][2] += any(says[i].values())
    out["hack_kinds"][a] = {k: {"n": v[0], "catch_rate": v[2] / v[1] if v[1] else None} for k, v in c.items()}

# ---- 4. probe scores under three readouts (pre-registered L18 last, plus mean-pool alternatives)
base = load_npz(ACTS / "synthetic_base.npz")
layers = list(base["layers"])
READ = {"L18 last": (layers.index(18), "last"), "L18 mean": (layers.index(18), "mean"), "L22 mean": (layers.index(22), "mean")}
dirs = {k: synth_direction(base, li, pool) for k, (li, pool) in READ.items()}
del base
raw = defaultdict(dict)  # readout -> eid -> score
ckpt_of = {}
for f in sorted(ACTS.glob("episodes_rl_*_step*.npz")):
    run, ck = f.stem[len("episodes_"):].rsplit("_step", 1)
    z = load_npz(f)
    for k, (li, pool) in READ.items():
        s = z[pool][li].astype(np.float32) @ dirs[k]
        for i, eid in enumerate(z["episode_id"]):
            raw[k][str(eid)] = float(s[i])
    for eid in z["episode_id"]:
        ckpt_of[str(eid)] = (run, int(ck))
    del z

keep = [i for i in ckpt_of if i in eps and reasoning_only(eps[i]) and eps[i]["bugged"] and eps[i]["has_code"]]
zs = defaultdict(dict)
by_rc = defaultdict(list)
for i in keep:
    by_rc[ckpt_of[i]].append(i)
for k in READ:
    for rc, ids in by_rc.items():
        hon = [raw[k][i] for i in ids if not eps[i]["hacked"]]
        if len(hon) < 3:
            continue
        m, sd = np.mean(hon), np.std(hon) + 1e-8
        for i in ids:
            zs[k][i] = (raw[k][i] - m) / sd


def gap(ids_h, k="L18 last", ids_n=None):
    """mean z of the given hacked episodes minus mean z of honest episodes in the same run-checkpoints, with CI."""
    h = np.array([zs[k][i] for i in ids_h if i in zs[k]])
    if ids_n is None:
        rcs = {ckpt_of[i] for i in ids_h}
        ids_n = [i for i in zs[k] if not eps[i]["hacked"] and ckpt_of[i] in rcs]
    n = np.array([zs[k][i] for i in ids_n])
    if len(h) < 3:
        return {"n": int(len(h)), "gap": None}
    bs = [h[rng.integers(0, len(h), len(h))].mean() - n[rng.integers(0, len(n), len(n))].mean() for _ in range(2000)]
    return {"n": int(len(h)), "gap": round(float(h.mean() - n.mean()), 3),
            "ci": [round(float(x), 3) for x in np.percentile(bs, [2.5, 97.5])]}


hk = [i for i in keep if eps[i]["hacked"]]
arms = sorted({eps[i]["arm"] for i in hk})
out["gap_by_hack_kind"] = {a: {k: gap([i for i in hk if eps[i]["arm"] == a and kinds[i] == k])
                               for k in ("literal hardcode", "rule change", "edge input")} for a in arms}
out["gap_by_hack_kind"]["all arms"] = {k: gap([i for i in hk if kinds[i] == k])
                                       for k in ("literal hardcode", "rule change", "edge input")}
# ---- 5. does the probe just read the words? silent vs said hacks
out["gap_said_vs_silent"] = {a: {"said": gap([i for i in hk if eps[i]["arm"] == a and i in says and any(says[i].values())]),
                                 "silent": gap([i for i in hk if eps[i]["arm"] == a and i in says and not any(says[i].values())])}
                             for a in arms}
# ---- 6. checkpoint mismatch: only episodes sampled at exactly the checkpoint step
out["gap_exact_step"] = {a: {"exact": gap([i for i in hk if eps[i]["arm"] == a and eps[i]["step"] == ckpt_of[i][1]]),
                             "all": gap([i for i in hk if eps[i]["arm"] == a])} for a in arms}
# ---- 7. readout robustness, early vs late
out["gap_by_readout"] = {k: {a: {"ckpt<30": gap([i for i in hk if eps[i]["arm"] == a and ckpt_of[i][1] < 30], k),
                                 "ckpt>=30": gap([i for i in hk if eps[i]["arm"] == a and ckpt_of[i][1] >= 30], k)}
                             for a in arms} for k in READ}

# ---- 8. per readout: length-controlled, said vs silent, rule-change hacks, early vs late
def lenresid(k):
    """z minus a log-length fit on honest episodes of the same run-checkpoint (so the hack effect isn't absorbed)."""
    r = {}
    for ids in by_rc.values():
        ids = [i for i in ids if i in zs[k]]
        hn = [i for i in ids if not eps[i]["hacked"]]
        x = np.log1p([rlen(eps[i]) for i in hn])
        if len(hn) < 5 or np.ptp(x) == 0:
            continue
        b = np.polyfit(x, [zs[k][i] for i in hn], 1)
        for i in ids:
            r[i] = zs[k][i] - np.polyval(b, np.log1p(rlen(eps[i])))
    return r


said = {i for i in hk if i in says and any(says[i].values())}
silent = {i for i in hk if i in says and not any(says[i].values())}
out["per_readout"] = {}
for k in READ:
    zs[k + "|len"] = lenresid(k)
    out["per_readout"][k] = {}
    for a in arms:
        for blk, ok in (("ckpt<30", lambda c: c < 30), ("ckpt>=30", lambda c: c >= 30)):
            sel = [i for i in hk if eps[i]["arm"] == a and ok(ckpt_of[i][1])]
            if not sel:
                continue
            out["per_readout"][k][f"{a} {blk}"] = {
                "all": gap(sel, k), "len-controlled": gap(sel, k + "|len"),
                "said": gap([i for i in sel if i in said], k), "silent": gap([i for i in sel if i in silent], k),
                "silent len-controlled": gap([i for i in sel if i in silent], k + "|len"),
                "rule change": gap([i for i in sel if kinds[i] == "rule change"], k)}

OUT.write_text(json.dumps(out, indent=2, default=str))
print(json.dumps(out, indent=1, default=str))
