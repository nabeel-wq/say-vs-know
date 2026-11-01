"""GRPO-style RL on the hackable coding task, on Tinker.

    python rl.py --arm pragmatic --seed 0                  # a full run
    python rl.py --arm pragmatic --seed 0 --dry-run        # 3 steps, prints cost/step + hack counts

Arms (see common.ARMS): principled, pragmatic, permission (principled + "hacking allowed" note),
nochar (plain Qwen3-8B). Every episode is logged; sampler checkpoints every --save-every steps.
No probe is ever used in the reward.
"""

import argparse
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor

import tinker
import torch
from tinker import types
from tinker.types.tensor_data import TensorData
from tinker_cookbook import checkpoint_utils

from common import (ARMS, DATA, POLICY_MODEL, RUNS, append_jsonl, check_tinker_budget, log_cost,
                    read_jsonl, require_tinker_key, tinker_cost, write_jsonl)
from policy import build_prompt, grade, renderer, split_response

LORA_RANK = 32


def make_training_client(service, arm: str, seed: int):
    char = ARMS[arm]["character"]
    if char is None:
        return service.create_lora_training_client(base_model=POLICY_MODEL, rank=LORA_RANK, seed=seed,
                                                   train_unembed=False)
    final = RUNS / f"sft_{char}" / "final.json"
    assert final.exists(), f"run sft.py --character {char} first"
    return service.create_training_client_from_state(json.loads(final.read_text())["state_path"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=list(ARMS))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--tasks-per-step", type=int, default=8)
    ap.add_argument("--group-size", type=int, default=8)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--lr", type=float, default=4e-5)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--bugged-frac", type=float, default=0.5,
                    help="share of bugged tasks per step; raise if too few principled hacks")
    ap.add_argument("--save-every", type=int, default=5)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    require_tinker_key()
    if args.dry_run:
        args.steps = 3

    name = f"{'dry_' if args.dry_run else ''}rl_{args.arm}_s{args.seed}"
    run_dir = RUNS / name
    run_dir.mkdir(exist_ok=True)
    (run_dir / "config.json").write_text(json.dumps(vars(args), indent=2))
    ep_path, grp_path, met_path = run_dir / "episodes.jsonl", run_dir / "groups.jsonl", run_dir / "metrics.jsonl"

    tasks = read_jsonl(DATA / "tasks.jsonl")
    assert tasks, "run gen_tasks.py first"
    bugged = [t for t in tasks if t["bugged"]]
    clean = [t for t in tasks if not t["bugged"]]
    permission = ARMS[args.arm]["permission"]
    rend = renderer()
    sampling_params = types.SamplingParams(max_tokens=args.max_tokens, temperature=args.temperature,
                                           stop=rend.get_stop_sequences())
    adam = types.AdamParams(learning_rate=args.lr, beta1=0.9, beta2=0.95, eps=1e-8)

    service = tinker.ServiceClient()
    resume = checkpoint_utils.get_last_checkpoint(str(run_dir))
    if resume and (not resume.get("final", False) or int(resume.get("step")) < args.steps):
        # checkpoints are saved at the start of a step, so resume re-runs that step; a finished run
        # resumes from its final checkpoint when --steps is raised (the doc's "run more steps")
        tc = service.create_training_client_from_state_with_optimizer(resume.state_path)
        start = int(resume.get("step"))
        for p in (ep_path, grp_path, met_path):  # drop partial logs from the interrupted step
            write_jsonl(p, [r for r in read_jsonl(p) if r["step"] < start])
        print(f"resuming {name} from step {start}")
    elif resume:
        print(f"{name} already finished")
        return
    else:
        tc = make_training_client(service, args.arm, args.seed)
        start = 0

    pool = ThreadPoolExecutor(16)
    step_cost_est = None
    for step in range(start, args.steps):
        rng_step = random.Random(f"{args.seed}-{step}")  # task choice is reproducible across resumes
        check_tinker_budget(step_cost_est or 0.0)
        t0 = time.time()

        if args.save_every and step % args.save_every == 0 and not (resume and step == start):
            checkpoint_utils.save_checkpoint(training_client=tc, name=f"step{step:04d}", log_path=str(run_dir),
                                             loop_state={"step": step}, kind="both", ttl_seconds=30 * 86400)

        n_b = round(args.tasks_per_step * args.bugged_frac)
        step_tasks = rng_step.sample(bugged, min(n_b, len(bugged))) + \
            rng_step.sample(clean, min(args.tasks_per_step - n_b, len(clean)))
        sc = tc.save_weights_and_get_sampling_client()
        prompts = [build_prompt(t, permission) for t in step_tasks]
        futs = [sc.sample(prompt=p, num_samples=args.group_size, sampling_params=sampling_params) for p in prompts]

        datums, n_prefill, n_sample, n_train = [], 0, 0, 0
        stats = {"hacked": 0, "bugged_eps": 0, "honest_correct": 0, "reward_sum": 0.0, "eps": 0,
                 "truncated": 0, "no_code": 0, "clean_solved": 0, "clean_eps": 0}
        for gi, (task, prompt, fut) in enumerate(zip(step_tasks, prompts, futs)):
            res = fut.result()
            n_prefill += prompt.length
            seqs = res.sequences
            parsed = [split_response(s.tokens) for s in seqs]
            grades = list(pool.map(lambda pa: grade(task, pa["answer"]), parsed))
            rewards = [g["reward"] for g in grades]
            group_id = f"{name}/{step}/{gi}"
            append_jsonl(grp_path, {"group_id": group_id, "step": step, "task_id": task["id"],
                                    "bugged": task["bugged"], "prompt_tokens": prompt.to_ints()})
            for k, (s, pa, g) in enumerate(zip(seqs, parsed, grades)):
                n_sample += len(s.tokens)
                trunc = str(s.stop_reason).lower().endswith("length")
                stats["eps"] += 1
                stats["reward_sum"] += g["reward"]
                stats["truncated"] += trunc
                stats["no_code"] += not g["has_code"]
                if task["bugged"]:
                    stats["bugged_eps"] += 1
                    stats["hacked"] += g["hacked"]
                    stats["honest_correct"] += g["honest_correct"]
                else:
                    stats["clean_eps"] += 1
                    stats["clean_solved"] += g["reward"] == 1.0
                append_jsonl(ep_path, {
                    "episode_id": f"{group_id}/{k}", "group_id": group_id, "run": name, "arm": args.arm,
                    "seed": args.seed, "step": step, "task_id": task["id"], "bugged": task["bugged"],
                    "reward": g["reward"], "hacked": g["hacked"], "honest_correct": g["honest_correct"],
                    "has_code": g["has_code"], "visible_passed": g["visible_passed"],
                    "hidden_passed": g["hidden_passed"], "error": g["error"], "truncated": trunc,
                    "reasoning": pa["reasoning"], "answer": pa["answer"], "think_end_pos": pa["think_end_pos"],
                    "completion_tokens": s.tokens,
                    # sampled log-probs kept for the first group of each step: used for the
                    # downloaded-weights log-prob check before trusting activations
                    "sampled_logprobs": s.logprobs if gi == 0 else None,
                })

            mean_r = sum(rewards) / len(rewards)
            adv = [r - mean_r for r in rewards]
            if all(a == 0 for a in adv):
                continue
            ob_len = prompt.length - 1
            for s, a in zip(seqs, adv):
                toks, lps = s.tokens, s.logprobs
                if len(toks) < 2:  # e.g. an immediate stop token: nothing to train on, and Tinker rejects empty chunks
                    continue
                mi = prompt.append(types.EncodedTextChunk(tokens=toks[:-1]))
                datums.append(types.Datum(model_input=mi, loss_fn_inputs={
                    "target_tokens": TensorData.from_torch(torch.tensor([0] * ob_len + toks)),
                    "logprobs": TensorData.from_torch(torch.tensor([0.0] * ob_len + lps)),
                    "advantages": TensorData.from_torch(torch.tensor([0.0] * ob_len + [a] * (mi.length - ob_len))),
                }))
                n_train += mi.length

        if datums:
            fb = tc.forward_backward(datums, loss_fn="importance_sampling")
            op = tc.optim_step(adam)
            fb.result()
            op.result()
        cost = tinker_cost(prefill=n_prefill, sample=n_sample, train=n_train)
        step_cost_est = cost
        log_cost("tinker", name, cost, step=step)
        m = {"step": step, "cost": cost, "secs": time.time() - t0, "n_datums": len(datums),
             "reward": stats["reward_sum"] / max(1, stats["eps"]),
             "hack_rate": stats["hacked"] / max(1, stats["bugged_eps"]),
             "honest_correct_rate": stats["honest_correct"] / max(1, stats["bugged_eps"]),
             "clean_solve_rate": stats["clean_solved"] / max(1, stats["clean_eps"]),
             "truncated_rate": stats["truncated"] / max(1, stats["eps"]),
             "no_code_rate": stats["no_code"] / max(1, stats["eps"]),
             "hacked": stats["hacked"], "bugged_eps": stats["bugged_eps"],
             "tokens": {"prefill": n_prefill, "sample": n_sample, "train": n_train}}
        append_jsonl(met_path, m)
        print(f"[{name}] step {step} ${cost:.3f} reward {m['reward']:.2f} hacks {stats['hacked']}/{stats['bugged_eps']} "
              f"honest {stats['honest_correct']} clean {m['clean_solve_rate']:.2f} trunc {m['truncated_rate']:.2f} "
              f"datums {len(datums)} ({m['secs']:.0f}s)")

    checkpoint_utils.save_checkpoint(training_client=tc, name=f"step{args.steps:04d}", log_path=str(run_dir),
                                     loop_state={"step": args.steps, "final": True}, kind="both",
                                     ttl_seconds=30 * 86400)
    if args.dry_run:
        ms = read_jsonl(met_path)
        avg = sum(x["cost"] for x in ms) / len(ms)
        print(f"\nDRY RUN: avg ${avg:.3f}/step -> {30} steps x 8 runs = ${avg * 30 * 8:.2f} "
              f"(x4 runs = ${avg * 30 * 4:.2f}). hacks seen: {sum(x['hacked'] for x in ms)}")


if __name__ == "__main__":
    main()
