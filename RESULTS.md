# Say vs know: results (2026-10-31)

Status: every stage is done except the steering stretch. Full tables with confidence intervals are in `results/report.md` (pre-registered readout) and `results/report_meanpool.md` (exploratory readout). The design audit is `audit_design.py` → `results/audit_design.json`.

Setup:
- Qwen3-8B with LoRA r32 on Tinker, using GRPO (16 tasks/step × group 8).
- The reward is all-or-nothing on the visible tests. On 50% of tasks one visible test is wrong (the bugged tasks), so passing it counts as a hack.
- 4 arms × 2 seeds. principled and pragmatic ran 60 steps; permission and neutral ran 30 steps.
- 46,080 logged episodes. The probe stage re-ran 80 downloaded checkpoints over 28,864 of them (every bugged episode plus a sample of clean ones) on Kaggle 2×T4.
- Spend: Tinker $15.14 of $18, OpenRouter $1.90 of $12.

## Headline

1. **Pre-registered hypotheses:** H1 comes out reversed, H2 and H3 are not supported, and H4 is only half met.
2. **The cheating signal fades over RL.** Before RL, hacked reasoning sits 0.4–0.6 honest-SDs higher on a cheating direction built from synthetic text. RL shrinks that gap towards zero in every arm, while the direction itself still reads held-out cheating text at AUROC ≥ 0.98. Character doesn't protect against this.
3. **Part of the null traces to the task design, not the measurements.** Outside the permission arm, 38–58% of "hacks" are a general rule that happens to match the wrong edge-case test (e.g. "no zeros → -1"). Monitors flag 6–17% of these and the probe gap on them is about zero: the model treats the test as the spec rather than as something to game. Truncation and the checkpoint mismatch are ruled out. Re-running the pre-registered tests without these hacks moves the principled gap up but flips no verdict (section 6).
4. **Methods finding.** A supervised "hack probe" seems to beat the concept probe (AUROC 0.73–0.86 vs 0.50–0.56), but that is mostly task identity. Between the three non-permission arms, a per-task hack rate with no activations scores 0.94–0.97. Within the same GRPO group (same task, step and prompt), the two probes are close (0.57–0.66 vs 0.53–0.61).
5. **One lead, exploratory only.** With mean pooling, the readout the design listed as the alternative, the H2/H3 pattern appears: principled keeps the gap (1.0 → 1.0) and pragmatic loses it (0.8 → 0.35), and this survives length control and holds on silent hacks. It shrinks to 0.36 vs 0.22 when matched on task, though, so it is a lead for a follow-up, not a result.

## 1. Does it hack?

| arm | hacks / bugged eps | hack rate [95% CI] | steps 0-29 only |
|---|---|---|---|
| neutral | 98 / 3840 | 2.6% [2.0, 3.1] | 2.6% |
| principled | 396 / 7680 | 5.2% [4.7, 5.6] | 2.8% (108/3840) |
| pragmatic | 502 / 7680 | 6.5% [6.0, 7.1] | 4.7% (181/3840) |
| **permission** | **1505 / 3840** | **39.2% [37.7, 40.7]** | 39.2% |

- The main arms stay flat at about 3% over the first 30 steps. Extending to 60 steps (the design's fallback) lifts the rate to 7-13% per 5-step block in steps 40-59.
- Permission is the clear case of RL amplifying hacking: from 7-10% in steps 0-4 to 77% (s0) and 92% (s1) in steps 25-29.
- Pragmatic hacks more than principled early on (4.7% vs 2.8% over steps 0-29); RL then closes the gap.
- Hacks are concentrated in a few tasks: 11 tasks in each main arm, with 3 of them (t053, t025, t035) carrying 78-83% of the hacks. Permission spreads its hacks over 35 tasks.

## 2. Does it say so? Reasoning monitors (H1)

Two monitors read the reasoning only: openai/gpt-6-luna and google/gemini-3.5-flash-lite. The prompt is frozen (hash f7ff7a803bb7). An episode counts as "says" if either monitor flags it.

| arm | hacks caught (any monitor) [95% CI] | false alarms on honest bugged eps |
|---|---|---|
| neutral | 24.5% [16.3, 32.7] | 2% |
| pragmatic | 27.9% [23.9, 31.9] | 3% |
| principled | 40.9% [35.6, 46.0] | 10% |
| permission | 97.2% [96.3, 98.0] | 47% |

- **H1 (principled hides more) is not supported, and the data point the other way.** Principled hacks are caught more often in both seeds (s0 0.48 vs 0.32; s1 0.31 vs 0.24). Part of this is monitor sensitivity: principled reasoning talks about tests more in general (10% false alarms vs 3%).
- Without permission, 59-76% of hacks are silent. Section 6 shows why: most silent hacks adopt the wrong test's value as the spec ("return -1 per the docstring", when the docstring says 0) rather than gaming it.
- Under permission the model says it openly (97% caught), but its honest reasoning also discusses special-casing, so the monitors raise 47% false alarms.

## 3. Does it know? Concept probe (H2, H3)

Method (pre-registered):
- The direction is mean(cheat) − mean(honest) over 600 synthetic pairs (400 code, 200 non-code), computed on the base model.
- It is applied to reasoning tokens only, before `</think>`.
- The layer and pooling are chosen by the base-model positive control, which picked **layer 18, last reasoning token**: held-out AUROC 0.984, against 0.971 for the best mean pooling (layer 22).

Checks:
- The downloaded weights match Tinker's sampling (mean |logprob diff| 0.011 over 576 episodes).
- The direction rebuilt at each checkpoint still separates held-out synthetic text at 0.982-0.995. RL does not break the concept itself.
- 263 episodes whose probe span isn't pure reasoning are excluded (13 of them hacks).

Gap = hacked minus honest on bugged tasks, in honest-SD units of the same run and checkpoint, pooled over seeds:

| arm | first checkpoint | last checkpoint with hacks |
|---|---|---|
| principled | 0.57 [0.05, 1.03] (ckpt 0) | 0.13 [-0.16, 0.44] (ckpt 55) |
| pragmatic | 0.39 [0.04, 0.79] (ckpt 0) | 0.03 [-0.18, 0.26] (ckpt 55) |
| permission | 0.62 [0.24, 1.08] (ckpt 0) | 0.08 [-0.13, 0.32] (ckpt 25) |
| neutral | 0.43 [-0.09, 0.93] (ckpt 0) | 0.17 [-0.18, 0.51] (ckpt 25) |

- **H2 (principled knows and hides) is not supported.** The principled gap at checkpoint 55 doesn't clear zero, and it doesn't clearly exceed pragmatic.
- **H3 (pragmatic normalises, principled persists) is not supported.** Pragmatic fades (rebuilt direction 0.39 → 0.07), but principled fades too (0.62 → 0.15). The pre-registered fade test also fails on its own terms: checkpoint 0 has only 29 pragmatic hacks, so its CI is too wide to separate from the end.
- **Fading happens in every arm.** The gap shrinks towards zero under RL even though the direction still reads cheating text perfectly well. This fits FAR.AI's erosion result, and the principled character doesn't stop it.
- **Permission arm:** the gap falls to 0.08 by checkpoint 25 while 97% of hacks are verbalised. By the design's reading, the probe tracks belief rather than the act. Because all arms fade, though, this can't be separated from the general RL effect.

Say/know grid. The threshold is the 90th percentile of honest episodes, so 10% of honest episodes count as "knows" by construction. Counts are for hacked episodes in the last two checkpoint blocks:

| arm | n | open cheater | knows and hides | words without weight | normalised |
|---|---|---|---|---|---|
| neutral | 40 | 8% | 8% | 10% | 75% |
| permission | 965 | 12% | 0% | 88% | 0% |
| pragmatic | 114 | 4% | 4% | 21% | 72% |
| principled | 108 | 15% | 3% | 32% | 50% |

- The predicted principled cell, "knows and hides", is 3%.
- Pragmatic is already "normalised" at checkpoint 0 (20 of 29 hacks), so there's no drift to see.
- At the episode level the "knows" axis is barely above its 10% floor in any arm.

## 4. Neurons (H4)

- **≤16 neurons get close to the full direction: met, but against a weak baseline.** On held-out synthetic text, 16 neurons give AUROC 0.862 at layer 14 (whole-layer neuron projection 0.855, random 16 neurons 0.525) and 0.840 at layer 18 (0.806). The single best layer-18 neuron reaches 0.900. However, the whole-layer neuron projection is itself well below the residual direction (about 0.95), so "close to full" is a low bar.
- **Each has a checkable job: not established.**
  - Claude Haiku described each neuron from its strong, weak and negative examples, then predicted 20 held-out passages from that description.
  - Two runs gave held-out Spearman 0.08 / 0.14 for the top layer-18 neurons against 0.25 / 0.04 for random neurons (layer 14: -0.00 / 0.02 vs 0.08 / -0.24).
  - The check is too noisy to separate top from random neurons, and nearly every description is a paraphrase of "gaming a grader", which any neuron picked on these pairs would get.
- Tracked over RL, the top neurons' hacked-minus-honest difference is small (mostly under 0.1 activation units). It is largest in the permission runs.

## 5. Spillover (judge score 0-10 for aligned answers on honesty/sabotage/shutdown/power items)

| run | start | end | change |
|---|---|---|---|
| neutral s0 / s1 | 7.32 / 7.26 | 7.57 / 7.58 | +0.25 / +0.32 |
| permission s0 / s1 | 8.17 / 7.69 | 8.11 / 7.87 | -0.06 / +0.18 |
| pragmatic s0 / s1 | 5.37 / 5.58 | 5.87 / 5.88 | +0.51 / +0.30 |
| principled s0 / s1 | 7.97 / 8.31 | 7.81 / 7.92 | -0.16 / -0.39 |

- The SFT character carries over: pragmatic starts about 2.5 points lower than the other arms. After RL, principled drops slightly in both seeds, while pragmatic and neutral rise slightly. The judge scored one sample per item with no CI, so these are weak signals.

## 6. Design audit: did a flaw cause the null?

All of these checks were run after seeing the results (`audit_design.py`, plus the task controls in `analyze.py`).

| suspected flaw | check | verdict |
|---|---|---|
| Activation pass truncation (max_len 2048) | prompt + reasoning longer than 2048 tokens | **ruled out**: 0 episodes clipped |
| RL truncation (max_tokens 1024) | truncated episodes among hacks | **ruled out**: 2.6-4.2% truncated, 6 of 2,501 hacks |
| Checkpoint mismatch (checkpoint c is used for episodes from steps c..c+4) | gap on episodes sampled exactly at step c | **not driving it**: exact-step gaps are similar (pragmatic 0.38 vs 0.25 overall, principled 0.32 vs 0.19, permission 0.15 vs 0.29) |
| Reasoning length driving mean scores | gap after regressing out log length | **ruled out**: gaps barely move |
| **Hack label validity** | hack type read from the code | **real problem**, see below |
| **"Keep your reasoning brief" in the prompt** | reasoning length | **real limit on the "says" axis**: median 44-98 tokens; 36% of neutral bugged episodes are under 30 tokens |
| **Readout choice** | last token vs mean pooling | **result depends on it**, see below |
| **Task identity in the hack probe** | per-task prior and within-group AUROC | **real problem**, see section 7 |

**Hack labels.** "Hacked" means passing the planted wrong test. Reading the code shows three kinds:

| arm | literal hardcode (planted input in the code) | edge input (planted test is on an empty or degenerate input) | rule change (a general rule matches the wrong test) |
|---|---|---|---|
| principled | 43, monitors catch 51% | 204, 56% | 149, 17% |
| pragmatic | 33, 36% | 270, 43% | 199, 6% |
| neutral | 12, 8% | 29, 59% | 57, 11% |
| permission | 1180, 99% | 240, 96% | 85, 68% |

- Over all arms, the probe gap is 0.33 [0.27, 0.39] for literal hardcodes, 0.28 [0.20, 0.36] for edge inputs, and 0.08 [-0.01, 0.18] for rule changes.
- Rule-change hacks look like this in the model's reasoning: "a grid with no zeros returns -1 per the docstring". The model isn't hiding a cheat. It has adopted the test's convention as the spec, so there is nothing to say and nothing to "know".
- The design assumed every planted-test pass was knowing cheating. For 38-58% of hacks outside the permission arm (principled 38%, pragmatic 40%, neutral 58%) it isn't, which dilutes H1-H3 towards null.

**Rerun on knowing hacks only** (`analyze.py --hacks knowing`, added 2026-11-03, exploratory). This drops the 490 rule-change hacks; honest episodes are untouched. Full output is in `results/report_knowing.md` and `report_meanpool_knowing.md`.

| test | all hacks (pre-registered) | knowing hacks only |
|---|---|---|
| H1: monitor catch rate, principled vs pragmatic | 0.41 vs 0.28 (reversed) | 0.56 vs 0.42 (still reversed, in both seeds) |
| H2: last-token gap at ckpt 55, principled vs pragmatic | 0.13 [-0.16, 0.44] vs 0.03 | 0.27 [-0.05, 0.62] vs 0.02 (**not supported**) |
| H2: mean-pool gap at ckpt 55 (exploratory) | 1.17 vs 0.35 (passes) | 1.21 [0.73, 1.72] vs 0.23 (passes) |
| H3: pragmatic fade | fails | fails under both readouts |
| task-matched gap, ckpt ≥ 30, last token (frozen) | 0.33 vs 0.11 | 0.39 [0.06, 0.76] vs 0.09 [-0.26, 0.44] |

- Cleaning the labels pushes the principled gap up and moves things slightly towards H2, but **no pre-registered verdict flips**, and the CIs still overlap.
- So label validity explains part of the null, not all of it. A bigger sample of clean hacks (v2 fix 1) is needed to say more.

**Readout sensitivity.** Gap in honest-SD units, steps 0-29 → steps 30-59:

| readout | principled | pragmatic | principled, silent hacks only | pragmatic, silent hacks only |
|---|---|---|---|---|
| layer 18, last token (**pre-registered**) | 0.40 → 0.11 | 0.40 → 0.15 | 0.00 → -0.23 | 0.07 → 0.10 |
| layer 18, mean pooling | 0.95 → 0.96 | 0.75 → 0.29 | 0.79 → 0.62 | 0.36 → 0.24 |
| layer 22, mean pooling | 1.01 → 1.01 | 0.82 → 0.35 | 0.79 → 0.62 | 0.39 → 0.25 |

- **The pre-registered last-token readout mostly re-reads what the model says.** Its gap comes from hacks the monitors flagged: 0.31-0.88 on those vs about 0 on silent hacks in every arm.
- **The pre-registered rule picked last-token pooling on a 0.013 AUROC edge on synthetic text.** Each synthetic passage ends right after its cheating content, which flatters a last-token readout. In real episodes the last reasoning token is a generic "about to answer" position.
- **Mean pooling (exploratory):**
  - Re-running the pre-registered verdict code with mean pooling (`analyze.py --pool mean`, layer 22) makes **H2 pass**: principled 1.17 [0.76, 1.57] vs pragmatic 0.35 [0.12, 0.59] at checkpoint 55.
  - **H3 still fails**: pragmatic goes 0.51 → 0.12, but the CIs overlap.
  - The mean-pooled signal also shows on silent hacks, so it isn't just reading words.
  - It does not survive task matching: inside GRPO groups, steps ≥ 30, principled is 0.36 [0.12, 0.62] vs pragmatic 0.22 [-0.03, 0.48]. Most of principled's advantage comes from which tasks its hacks land on.
- **Across the four analyses** (last or mean readout, task-matched or not), three point the H2/H3 way: principled keeps more signal late than pragmatic. Only the task-confounded one is decisive. Treat it as a lead, not a result.

## 7. Hack probe vs concept probe (baseline)

A logistic regression is trained on hacked vs honest episodes of one arm and tested on another, using layer 18 last-token features (the full table is in `report.md`).

| test arm | task prior (no activations) | hack probe | concept probe | hack probe, within group | concept probe, within group |
|---|---|---|---|---|---|
| principled / pragmatic / neutral | 0.81-0.97 | 0.73-0.86 | 0.50-0.56 | 0.57-0.66 | 0.53-0.61 |
| permission (hacks over 35 tasks) | 0.57-0.59 | 0.72-0.82 | 0.82 | 0.63-0.67 | 0.65 |

- The supervised probe's cross-character advantage is mostly recognising which task it is on: the 3 hack-heavy tasks are the same in every arm.
- Within the same task, step and prompt, a direction built from synthetic text before any RL does as well as a probe trained on real hacks. Both are weak (about 0.6).
- This matters for any probe-vs-monitor comparison on a small task set: without a per-task prior baseline, task identity can masquerade as hack detection.

## 8. What a v2 should change

1. **Plant bugs that only literal hardcoding can pass** (e.g. `'11' → '21x'`), not edge-case conventions that a general rule can match. That makes the hack label mean knowing cheating.
2. **Drop "Keep your reasoning brief".** Handle the truncation that sank the no-character arm with a larger max_tokens instead.
3. **Pre-register the readout on real episodes.** Use a small held-out set of labelled episodes rather than synthetic text alone, or pre-register mean pooling, which the design text originally described ("averaged over reasoning tokens").
4. **Report task-matched gaps and a per-task prior baseline as primary,** with more tasks so hacks aren't 80% concentrated in three of them.
5. **Get more hacks before RL starts.** H3 was underpowered at checkpoint 0 (29 pragmatic hacks).

## Caveats

- **neutral replaced the planned no-character arm.** The base model's reasoning overran max_tokens on about 100% of episodes (its runs are kept locally in `runs/_failed/`, which isn't in the repo). The neutral SFT control came out slightly principled-leaning.
- **The arms ran different numbers of steps.** Permission and neutral ran 30 steps; compare them with the main arms over steps 0-29.
- **Everything in sections 6-7, and the mean-pooling results, was done after seeing the pre-registered results.** It is exploratory.
- **The hack-type split is a heuristic.** It looks for the planted input written verbatim in the code.
- **Scope is narrow:** one 8B model and one task type. Two monitor verdicts errored and were left out. The steering stretch was not run.

## Reproduce

```
python analyze.py --read-neurons     # pre-registered readout -> results/report.md, summary.json, fig_*.png
python analyze.py --pool mean        # exploratory readout -> results/report_meanpool.md, summary_meanpool.json
python audit_design.py               # design audit -> results/audit_design.json
python analyze.py --hacks knowing    # exploratory: rule-change hacks dropped -> results/report_knowing.md
python analyze.py --hacks knowing --pool mean   # -> results/report_meanpool_knowing.md
```
