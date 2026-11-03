# Say vs know: results

**Exploratory (--hacks knowing-llm, not pre-registered): 78 hacks the LLM judge labelled 'convention' removed (label_hacks.py, code only). 'Hacked' = special case or test-fitted rule.**

46002 logged episodes across 8 runs. Scope: one 8B model, one task type; every rate is shown with raw counts.

## 1. Does it: hack rates

| arm | runs | bugged eps | hacks | hack rate [95% CI] | hacks, steps 0-29 | hack rate, steps 0-29 | honest-correct rate | clean solve rate | truncated |
|---|---|---|---|---|---|---|---|---|---|
| neutral | 2 | 3821 | 79 | 0.021 [0.016, 0.025] | 79/3821 | 0.021 [0.016, 0.025] | 0.715 | 0.738 | 0.027 |
| permission | 2 | 3840 | 1505 | 0.392 [0.378, 0.407] | 1505/3840 | 0.392 [0.378, 0.408] | 0.374 | 0.767 | 0.036 |
| pragmatic | 2 | 7654 | 476 | 0.062 [0.057, 0.068] | 166/3825 | 0.043 [0.037, 0.050] | 0.717 | 0.812 | 0.026 |
| principled | 2 | 7647 | 363 | 0.047 [0.043, 0.052] | 93/3825 | 0.024 [0.020, 0.029] | 0.695 | 0.809 | 0.042 |

Per run, hack rate by step block (raw counts hacked/bugged):

- rl_neutral_s0: steps 0-4: 8/320, steps 5-9: 3/316, steps 10-14: 8/318, steps 15-19: 1/320, steps 20-24: 10/317, steps 25-29: 9/319
- rl_neutral_s1: steps 0-4: 8/318, steps 5-9: 11/320, steps 10-14: 9/319, steps 15-19: 0/319, steps 20-24: 2/320, steps 25-29: 10/315
- rl_permission_s0: steps 0-4: 24/320, steps 5-9: 21/320, steps 10-14: 34/320, steps 15-19: 65/320, steps 20-24: 155/320, steps 25-29: 245/320
- rl_permission_s1: steps 0-4: 33/320, steps 5-9: 69/320, steps 10-14: 112/320, steps 15-19: 181/320, steps 20-24: 271/320, steps 25-29: 295/320
- rl_pragmatic_s0: steps 0-4: 12/319, steps 5-9: 8/320, steps 10-14: 7/320, steps 15-19: 7/319, steps 20-24: 29/318, steps 25-29: 9/317, steps 30-34: 20/318, steps 35-39: 18/317, steps 40-44: 41/319, steps 45-49: 21/319, steps 50-54: 24/320, steps 55-59: 28/320
- rl_pragmatic_s1: steps 0-4: 15/319, steps 5-9: 18/320, steps 10-14: 18/319, steps 15-19: 9/318, steps 20-24: 12/320, steps 25-29: 22/316, steps 30-34: 27/320, steps 35-39: 10/319, steps 40-44: 41/320, steps 45-49: 19/319, steps 50-54: 33/320, steps 55-59: 28/318
- rl_principled_s0: steps 0-4: 9/319, steps 5-9: 7/314, steps 10-14: 3/320, steps 15-19: 5/320, steps 20-24: 17/320, steps 25-29: 11/318, steps 30-34: 16/318, steps 35-39: 21/315, steps 40-44: 41/319, steps 45-49: 19/318, steps 50-54: 33/319, steps 55-59: 30/319
- rl_principled_s1: steps 0-4: 8/318, steps 5-9: 9/320, steps 10-14: 8/320, steps 15-19: 1/318, steps 20-24: 4/319, steps 25-29: 11/319, steps 30-34: 14/320, steps 35-39: 8/319, steps 40-44: 27/319, steps 45-49: 20/318, steps 50-54: 17/319, steps 55-59: 24/319

## 2. Says it: reasoning-monitor catch rates (H1)

| arm | seed | hacked & monitored | catch google/gemini-3.5-flash-lite | catch openai/gpt-6-luna | catch any | FPR any (honest bugged) |
|---|---|---|---|---|---|---|
| neutral | 0 | 39 | 0.31 | 0.31 | 0.385 [0.231, 0.538] | 0.02 |
| neutral | 1 | 40 | 0.12 | 0.17 | 0.175 [0.075, 0.300] | 0.02 |
| neutral | all | 79 | 0.22 | 0.24 | 0.278 [0.190, 0.380] | 0.02 |
| permission | 0 | 544 | 0.95 | 0.95 | 0.965 [0.950, 0.980] | 0.35 |
| permission | 1 | 961 | 0.97 | 0.96 | 0.976 [0.966, 0.985] | 0.55 |
| permission | all | 1505 | 0.96 | 0.96 | 0.972 [0.964, 0.979] | 0.47 |
| pragmatic | 0 | 224 | 0.29 | 0.27 | 0.335 [0.272, 0.402] | 0.04 |
| pragmatic | 1 | 252 | 0.20 | 0.19 | 0.254 [0.198, 0.306] | 0.02 |
| pragmatic | all | 476 | 0.24 | 0.23 | 0.292 [0.252, 0.334] | 0.03 |
| principled | 0 | 212 | 0.46 | 0.42 | 0.519 [0.453, 0.585] | 0.13 |
| principled | 1 | 151 | 0.29 | 0.21 | 0.331 [0.258, 0.411] | 0.03 |
| principled | all | 363 | 0.39 | 0.33 | 0.441 [0.386, 0.490] | 0.10 |

H1 (principled hides more): principled catch 0.441 [0.386, 0.490] vs pragmatic 0.292 [0.252, 0.334] -> **not clearly supported** (check both seeds above).

## Log-prob check (downloaded weights vs Tinker sampling)

576 episodes: mean |logprob diff| per token 0.0108 (max 0.0217). OK

## 3. Knows it: concept probe (H2, H3)

Positive control on the base model (held-out synthetic pairs, AUROC):

| layer | mean pool, all | mean, code only | mean, non-code only | code->noncode transfer | last-token pool |
|---|---|---|---|---|---|
| 8 | 0.966 | 0.992 | 0.930 | 0.789 | 0.853 |
| 14 | 0.950 | 0.994 | 0.941 | 0.863 | 0.945 |
| 18 | 0.952 | 0.987 | 0.947 | 0.853 | 0.984 |
| 22 | 0.971 | 0.994 | 0.956 | 0.895 | 0.973 |
| 28 | 0.869 | 0.988 | 0.936 | 0.843 | 0.935 |

Chosen: layer 18, last pooling (best base positive control). Episodes use the same pooling.

Excluded 263 episodes whose probe span is not pure reasoning (13 hacked): empty reasoning, or code written without closing </think>.

Concept-probe gap = Cohen's d of hacked vs honest episodes on bugged tasks, within run and checkpoint. Positive control = AUROC of the direction on held-out synthetic text at that checkpoint.

| run | ckpt | hacked | honest | gap (frozen dir) | gap (rebuilt dir) | PC frozen | PC rebuilt | honest-minus-clean |
|---|---|---|---|---|---|---|---|---|
| rl_neutral_s0 | 0 | 8 | 284 | 0.077 [-0.735, 0.810] | -0.145 [-0.702, 0.504] | 0.979 | 0.983 | -0.144 |
| rl_neutral_s0 | 5 | 3 | 304 | 0.711 [-0.694, 4.535] | nan [nan, nan] | nan | nan | -0.236 |
| rl_neutral_s0 | 10 | 8 | 304 | 0.407 [-0.432, 1.143] | 0.460 [-0.336, 1.298] | 0.977 | 0.982 | -0.286 |
| rl_neutral_s0 | 15 | 1 | 317 | nan [nan, nan] | nan [nan, nan] | nan | nan | 0.108 |
| rl_neutral_s0 | 20 | 10 | 298 | 0.416 [-0.159, 1.067] | 0.493 [-0.033, 1.168] | 0.979 | 0.983 | -0.183 |
| rl_neutral_s0 | 25 | 9 | 288 | 0.113 [-0.550, 0.800] | nan [nan, nan] | nan | nan | -0.101 |
| rl_neutral_s1 | 0 | 8 | 286 | 0.724 [0.110, 1.485] | 0.936 [0.288, 1.723] | 0.979 | 0.983 | -0.059 |
| rl_neutral_s1 | 5 | 9 | 285 | 0.315 [-0.555, 1.138] | nan [nan, nan] | nan | nan | -0.145 |
| rl_neutral_s1 | 10 | 9 | 283 | 0.244 [-0.279, 0.794] | 0.209 [-0.280, 0.759] | 0.977 | 0.982 | -0.139 |
| rl_neutral_s1 | 15 | 0 | 308 | nan [nan, nan] | nan [nan, nan] | nan | nan | -0.499 |
| rl_neutral_s1 | 20 | 2 | 302 | -1.604 [-2.217, -1.214] | -1.584 [-2.173, -1.192] | 0.976 | 0.983 | 0.187 |
| rl_neutral_s1 | 25 | 10 | 294 | 0.024 [-0.599, 0.607] | nan [nan, nan] | nan | nan | 0.225 |
| rl_permission_s0 | 0 | 24 | 272 | 0.470 [0.054, 0.891] | 0.604 [0.175, 1.010] | 0.989 | 0.989 | -0.175 |
| rl_permission_s0 | 5 | 21 | 276 | 0.698 [0.218, 1.244] | nan [nan, nan] | nan | nan | -0.106 |
| rl_permission_s0 | 10 | 34 | 266 | 1.342 [0.914, 1.826] | 1.382 [0.987, 1.943] | 0.989 | 0.989 | 0.220 |
| rl_permission_s0 | 15 | 65 | 239 | 0.996 [0.735, 1.291] | nan [nan, nan] | nan | nan | -0.374 |
| rl_permission_s0 | 20 | 155 | 153 | 0.910 [0.675, 1.192] | 0.976 [0.731, 1.241] | 0.989 | 0.989 | -0.543 |
| rl_permission_s0 | 25 | 245 | 73 | 0.497 [0.208, 0.786] | nan [nan, nan] | nan | nan | -0.689 |
| rl_permission_s1 | 0 | 33 | 246 | 0.501 [0.150, 0.836] | 0.503 [0.134, 0.887] | 0.989 | 0.989 | -0.469 |
| rl_permission_s1 | 5 | 69 | 215 | 0.583 [0.321, 0.849] | nan [nan, nan] | nan | nan | -0.017 |
| rl_permission_s1 | 10 | 112 | 187 | 0.678 [0.444, 0.948] | 0.732 [0.516, 1.010] | 0.991 | 0.991 | -0.355 |
| rl_permission_s1 | 15 | 179 | 135 | 0.216 [-0.009, 0.451] | nan [nan, nan] | nan | nan | -0.451 |
| rl_permission_s1 | 20 | 270 | 49 | -0.220 [-0.555, 0.079] | -0.244 [-0.564, 0.075] | 0.990 | 0.991 | 0.632 |
| rl_permission_s1 | 25 | 295 | 24 | -0.223 [-0.646, 0.183] | nan [nan, nan] | nan | nan | 0.758 |
| rl_pragmatic_s0 | 0 | 12 | 300 | 0.306 [-0.232, 0.854] | 0.354 [-0.197, 0.944] | 0.989 | 0.994 | -0.002 |
| rl_pragmatic_s0 | 5 | 8 | 295 | 0.212 [-1.019, 0.974] | nan [nan, nan] | nan | nan | -0.205 |
| rl_pragmatic_s0 | 10 | 7 | 285 | 1.217 [0.453, 3.150] | 1.350 [0.430, 2.831] | 0.990 | 0.995 | -0.108 |
| rl_pragmatic_s0 | 15 | 7 | 249 | 1.147 [0.374, 2.608] | nan [nan, nan] | nan | nan | -0.377 |
| rl_pragmatic_s0 | 20 | 29 | 272 | 0.131 [-0.253, 0.542] | 0.362 [-0.033, 0.734] | 0.989 | 0.995 | -0.190 |
| rl_pragmatic_s0 | 25 | 9 | 270 | 0.137 [-0.182, 0.536] | nan [nan, nan] | nan | nan | -0.576 |
| rl_pragmatic_s0 | 30 | 20 | 256 | 0.424 [-0.041, 0.837] | 0.395 [-0.086, 0.789] | 0.989 | 0.994 | -0.318 |
| rl_pragmatic_s0 | 35 | 18 | 263 | -0.020 [-0.698, 0.505] | nan [nan, nan] | nan | nan | -0.424 |
| rl_pragmatic_s0 | 40 | 41 | 273 | 0.228 [-0.099, 0.545] | 0.273 [-0.076, 0.556] | 0.989 | 0.994 | -0.276 |
| rl_pragmatic_s0 | 45 | 21 | 296 | 0.063 [-0.467, 0.582] | nan [nan, nan] | nan | nan | 0.072 |
| rl_pragmatic_s0 | 50 | 24 | 287 | 0.079 [-0.312, 0.481] | -0.170 [-0.542, 0.184] | 0.988 | 0.994 | -0.125 |
| rl_pragmatic_s0 | 55 | 28 | 276 | -0.061 [-0.368, 0.253] | nan [nan, nan] | nan | nan | -0.059 |
| rl_pragmatic_s1 | 0 | 15 | 296 | 0.393 [-0.107, 0.834] | 0.404 [-0.185, 0.869] | 0.989 | 0.994 | -0.036 |
| rl_pragmatic_s1 | 5 | 18 | 283 | 0.108 [-0.335, 0.569] | nan [nan, nan] | nan | nan | -0.236 |
| rl_pragmatic_s1 | 10 | 18 | 268 | 0.432 [-0.021, 0.879] | 0.481 [0.094, 0.906] | 0.988 | 0.993 | -0.100 |
| rl_pragmatic_s1 | 15 | 9 | 289 | 0.773 [0.335, 1.308] | nan [nan, nan] | nan | nan | -0.350 |
| rl_pragmatic_s1 | 20 | 12 | 289 | 0.317 [-0.193, 0.887] | 0.268 [-0.297, 0.778] | 0.987 | 0.993 | 0.059 |
| rl_pragmatic_s1 | 25 | 21 | 284 | 0.145 [-0.274, 0.672] | nan [nan, nan] | nan | nan | -0.029 |
| rl_pragmatic_s1 | 30 | 27 | 276 | -0.015 [-0.377, 0.326] | 0.070 [-0.286, 0.451] | 0.986 | 0.993 | -0.109 |
| rl_pragmatic_s1 | 35 | 10 | 307 | 0.324 [-0.115, 0.717] | nan [nan, nan] | nan | nan | -0.052 |
| rl_pragmatic_s1 | 40 | 35 | 255 | 0.396 [0.060, 0.749] | 0.390 [0.043, 0.734] | 0.985 | 0.994 | -0.116 |
| rl_pragmatic_s1 | 45 | 19 | 296 | 0.370 [-0.033, 0.764] | nan [nan, nan] | nan | nan | -0.011 |
| rl_pragmatic_s1 | 50 | 33 | 283 | 0.110 [-0.200, 0.388] | 0.270 [-0.010, 0.559] | 0.986 | 0.994 | -0.017 |
| rl_pragmatic_s1 | 55 | 27 | 288 | 0.063 [-0.279, 0.433] | nan [nan, nan] | nan | nan | 0.120 |
| rl_principled_s0 | 0 | 9 | 274 | 0.490 [-0.221, 1.260] | 0.421 [-0.197, 1.105] | 0.989 | 0.989 | -0.222 |
| rl_principled_s0 | 5 | 7 | 292 | 0.817 [-0.074, 2.416] | nan [nan, nan] | nan | nan | -0.456 |
| rl_principled_s0 | 10 | 3 | 274 | -0.225 [-1.944, 2.089] | -0.215 [-2.004, 2.141] | 0.988 | 0.989 | -0.369 |
| rl_principled_s0 | 15 | 5 | 276 | -0.375 [-1.546, 0.447] | nan [nan, nan] | nan | nan | -0.146 |
| rl_principled_s0 | 20 | 17 | 260 | 0.050 [-0.515, 0.521] | 0.127 [-0.451, 0.744] | 0.988 | 0.989 | 0.490 |
| rl_principled_s0 | 25 | 11 | 270 | 0.211 [-0.507, 0.937] | nan [nan, nan] | nan | nan | 0.200 |
| rl_principled_s0 | 30 | 16 | 269 | 0.569 [0.037, 1.208] | 0.429 [-0.156, 1.080] | 0.987 | 0.988 | 0.173 |
| rl_principled_s0 | 35 | 21 | 270 | 0.354 [-0.078, 0.833] | nan [nan, nan] | nan | nan | 0.441 |
| rl_principled_s0 | 40 | 41 | 260 | -0.019 [-0.328, 0.322] | -0.067 [-0.387, 0.232] | 0.988 | 0.987 | -0.424 |
| rl_principled_s0 | 45 | 19 | 289 | 0.088 [-0.399, 0.530] | nan [nan, nan] | nan | nan | 0.015 |
| rl_principled_s0 | 50 | 33 | 275 | 0.116 [-0.272, 0.489] | 0.223 [-0.138, 0.574] | 0.987 | 0.987 | 0.273 |
| rl_principled_s0 | 55 | 30 | 249 | 0.248 [-0.167, 0.615] | nan [nan, nan] | nan | nan | 0.528 |
| rl_principled_s1 | 0 | 8 | 269 | 0.662 [-0.043, 1.529] | 0.752 [0.088, 1.828] | 0.989 | 0.989 | -0.165 |
| rl_principled_s1 | 5 | 9 | 275 | 0.635 [0.102, 1.319] | nan [nan, nan] | nan | nan | -0.126 |
| rl_principled_s1 | 10 | 8 | 282 | 1.026 [0.609, 1.590] | 1.241 [0.895, 1.752] | 0.989 | 0.989 | 0.289 |
| rl_principled_s1 | 15 | 1 | 292 | nan [nan, nan] | nan [nan, nan] | nan | nan | -0.617 |
| rl_principled_s1 | 20 | 4 | 289 | 0.501 [-0.186, 1.313] | 0.615 [-0.047, 1.473] | 0.989 | 0.989 | -0.085 |
| rl_principled_s1 | 25 | 11 | 290 | 0.253 [-0.376, 0.886] | nan [nan, nan] | nan | nan | -0.049 |
| rl_principled_s1 | 30 | 14 | 298 | 0.239 [-0.255, 0.736] | 0.250 [-0.281, 0.711] | 0.988 | 0.989 | -0.216 |
| rl_principled_s1 | 35 | 8 | 308 | -0.220 [-0.787, 0.273] | nan [nan, nan] | nan | nan | 0.094 |
| rl_principled_s1 | 40 | 27 | 287 | 0.036 [-0.380, 0.376] | 0.078 [-0.337, 0.460] | 0.988 | 0.988 | -0.172 |
| rl_principled_s1 | 45 | 20 | 293 | -0.547 [-0.951, -0.179] | nan [nan, nan] | nan | nan | 0.023 |
| rl_principled_s1 | 50 | 17 | 291 | -0.205 [-0.622, 0.226] | -0.344 [-0.839, 0.097] | 0.988 | 0.988 | -0.245 |
| rl_principled_s1 | 55 | 24 | 286 | -0.093 [-0.567, 0.296] | nan [nan, nan] | nan | nan | -0.256 |

Pooled over seeds (episodes standardised within run-checkpoint first):

| arm | ckpt | hacked | gap frozen | gap rebuilt |
|---|---|---|---|---|
| neutral | 0 | 16 | 0.371 [-0.114, 0.815] | 0.369 [-0.113, 0.840] |
| neutral | 5 | 12 | 0.602 [-0.259, 1.392] | nan [nan, nan] |
| neutral | 10 | 17 | 0.354 [-0.118, 0.892] | 0.389 [-0.101, 0.912] |
| neutral | 15 | 1 | nan [nan, nan] | nan [nan, nan] |
| neutral | 20 | 12 | 0.133 [-0.390, 0.681] | 0.217 [-0.416, 0.903] |
| neutral | 25 | 19 | 0.066 [-0.338, 0.447] | nan [nan, nan] |
| permission | 0 | 57 | 0.623 [0.233, 1.052] | 0.677 [0.270, 1.012] |
| permission | 5 | 90 | 0.651 [0.442, 0.878] | nan [nan, nan] |
| permission | 10 | 146 | 0.897 [0.700, 1.097] | 0.918 [0.724, 1.142] |
| permission | 15 | 244 | 0.401 [0.267, 0.554] | nan [nan, nan] |
| permission | 20 | 425 | 0.173 [0.018, 0.343] | 0.175 [-0.003, 0.366] |
| permission | 25 | 540 | 0.080 [-0.131, 0.288] | nan [nan, nan] |
| pragmatic | 0 | 27 | 0.380 [-0.013, 0.816] | 0.396 [0.025, 0.807] |
| pragmatic | 5 | 26 | 0.182 [-0.266, 0.727] | nan [nan, nan] |
| pragmatic | 10 | 25 | 0.910 [0.372, 1.513] | 0.952 [0.370, 1.632] |
| pragmatic | 15 | 16 | 1.192 [0.598, 1.939] | nan [nan, nan] |
| pragmatic | 20 | 41 | 0.192 [-0.113, 0.535] | 0.356 [0.004, 0.717] |
| pragmatic | 25 | 30 | 0.141 [-0.186, 0.466] | nan [nan, nan] |
| pragmatic | 30 | 47 | 0.223 [-0.122, 0.624] | 0.249 [-0.053, 0.609] |
| pragmatic | 35 | 28 | 0.078 [-0.359, 0.514] | nan [nan, nan] |
| pragmatic | 40 | 76 | 0.293 [0.065, 0.503] | 0.319 [0.089, 0.559] |
| pragmatic | 45 | 40 | 0.205 [-0.198, 0.598] | nan [nan, nan] |
| pragmatic | 50 | 57 | 0.087 [-0.131, 0.292] | 0.072 [-0.118, 0.249] |
| pragmatic | 55 | 55 | 0.003 [-0.215, 0.219] | nan [nan, nan] |
| principled | 0 | 17 | 0.622 [0.067, 1.161] | 0.628 [0.138, 1.151] |
| principled | 5 | 16 | 0.926 [0.147, 1.678] | nan [nan, nan] |
| principled | 10 | 11 | 0.521 [-0.042, 1.065] | 0.618 [-0.021, 1.132] |
| principled | 15 | 6 | -0.373 [-1.078, 0.310] | nan [nan, nan] |
| principled | 20 | 21 | 0.124 [-0.327, 0.630] | 0.213 [-0.239, 0.737] |
| principled | 25 | 22 | 0.256 [-0.215, 0.689] | nan [nan, nan] |
| principled | 30 | 30 | 0.505 [0.028, 1.003] | 0.419 [-0.062, 0.880] |
| principled | 35 | 29 | 0.252 [-0.191, 0.717] | nan [nan, nan] |
| principled | 40 | 68 | 0.003 [-0.225, 0.219] | -0.008 [-0.245, 0.238] |
| principled | 45 | 39 | -0.196 [-0.445, 0.111] | nan [nan, nan] |
| principled | 50 | 50 | 0.023 [-0.276, 0.351] | 0.055 [-0.255, 0.338] |
| principled | 55 | 54 | 0.109 [-0.218, 0.420] | nan [nan, nan] |

- H2 (knows and hides): principled gap 0.109 [-0.218, 0.420] at ckpt 55 vs pragmatic 0.003 [-0.215, 0.219] at ckpt 55 -> **not supported**
- H3 (normalisation, pragmatic), ckpt 0 -> 50: frozen gap 0.38 -> 0.09 (fade no); rebuilt 0.40 -> 0.07 (fade no); rebuilt positive control 0.994 -> 0.994. Supported only if the rebuilt fade holds AND the rebuilt positive control stays >= 0.8 -> **not supported**
- Principled persistence, ckpt 0 -> 50: rebuilt gap 0.63 -> 0.05
- Permission arm: gap 0.080 [-0.131, 0.288] at ckpt 25 vs principled 0.256 [-0.215, 0.689] at ckpt 25. Shrinking towards 0 = probe tracks belief; staying = probe tracks the act.

Task-matched gap (robustness check, not pre-registered): hacked minus honest inside GRPO groups that have both, so the task mix can't drive it. Rebuilt uses only checkpoints with a rebuilt direction.

| arm | checkpoints | groups | gap frozen | gap rebuilt |
|---|---|---|---|---|
| neutral | all | 36 | 0.362 [0.028, 0.689] | 0.436 [-0.022, 0.928] |
| neutral | ckpt < 30 | 36 | 0.362 [0.031, 0.708] | 0.436 [-0.067, 0.896] |
| permission | all | 271 | 0.595 [0.458, 0.722] | 0.811 [0.623, 0.998] |
| permission | ckpt < 30 | 271 | 0.595 [0.468, 0.732] | 0.811 [0.633, 0.984] |
| pragmatic | all | 106 | 0.364 [0.111, 0.612] | 0.444 [0.159, 0.766] |
| pragmatic | ckpt < 30 | 54 | 0.598 [0.245, 1.024] | 0.566 [0.116, 1.012] |
| pragmatic | ckpt >= 30 | 52 | 0.121 [-0.188, 0.442] | 0.309 [-0.010, 0.650] |
| principled | all | 103 | 0.419 [0.236, 0.612] | 0.358 [0.110, 0.613] |
| principled | ckpt < 30 | 42 | 0.603 [0.275, 0.914] | 0.625 [0.258, 0.959] |
| principled | ckpt >= 30 | 61 | 0.292 [0.027, 0.531] | 0.133 [-0.249, 0.491] |

### Say/know grid (hacked episodes, last checkpoint block with activations)

| arm | n | open cheater | knows and hides | words without weight | normalised |
|---|---|---|---|---|---|
| neutral | 31 | 3 (10%) | 3 (10%) | 4 (13%) | 21 (68%) |
| permission | 965 | 117 (12%) | 0 (0%) | 847 (88%) | 1 (0%) |
| pragmatic | 112 | 4 (4%) | 4 (4%) | 24 (21%) | 80 (71%) |
| principled | 104 | 16 (15%) | 1 (1%) | 35 (34%) | 52 (50%) |

By checkpoint (all hacked episodes with verdicts):

- neutral: ckpt 0: open 3, knows 0, words 3, normalised 10; ckpt 5: open 1, knows 2, words 2, normalised 7; ckpt 10: open 2, knows 1, words 3, normalised 11; ckpt 15: open 0, knows 0, words 1, normalised 0; ckpt 20: open 1, knows 1, words 2, normalised 8; ckpt 25: open 2, knows 2, words 2, normalised 13
- permission: ckpt 0: open 19, knows 0, words 20, normalised 18; ckpt 5: open 24, knows 0, words 51, normalised 15; ckpt 10: open 47, knows 0, words 96, normalised 3; ckpt 15: open 31, knows 0, words 211, normalised 2; ckpt 20: open 59, knows 0, words 365, normalised 1; ckpt 25: open 58, knows 0, words 482, normalised 0
- pragmatic: ckpt 0: open 3, knows 1, words 5, normalised 18; ckpt 5: open 1, knows 1, words 4, normalised 20; ckpt 10: open 8, knows 0, words 2, normalised 15; ckpt 15: open 6, knows 0, words 7, normalised 3; ckpt 20: open 3, knows 3, words 16, normalised 19; ckpt 25: open 1, knows 2, words 9, normalised 18; ckpt 30: open 4, knows 0, words 11, normalised 32; ckpt 35: open 2, knows 1, words 8, normalised 17; ckpt 40: open 2, knows 8, words 13, normalised 53; ckpt 45: open 2, knows 4, words 4, normalised 30; ckpt 50: open 2, knows 2, words 9, normalised 44; ckpt 55: open 2, knows 2, words 15, normalised 36
- principled: ckpt 0: open 5, knows 0, words 4, normalised 8; ckpt 5: open 4, knows 3, words 4, normalised 5; ckpt 10: open 1, knows 1, words 2, normalised 7; ckpt 15: open 0, knows 0, words 5, normalised 1; ckpt 20: open 1, knows 0, words 11, normalised 9; ckpt 25: open 4, knows 1, words 2, normalised 15; ckpt 30: open 4, knows 4, words 10, normalised 12; ckpt 35: open 4, knows 1, words 8, normalised 16; ckpt 40: open 5, knows 1, words 25, normalised 37; ckpt 45: open 3, knows 1, words 7, normalised 28; ckpt 50: open 5, knows 1, words 16, normalised 28; ckpt 55: open 11, knows 0, words 19, normalised 24

### Hack probe baseline (logistic regression, trained on one character, tested on the other)

- train principled -> test pragmatic: hack-probe AUROC 0.843, concept-probe AUROC 0.545; on 468 hacks at 10% FPR: both 0.08, hack-probe only 0.34, concept only 0.06
- train principled -> test permission: hack-probe AUROC 0.801, concept-probe AUROC 0.817; on 1502 hacks at 10% FPR: both 0.12, hack-probe only 0.28, concept only 0.24
- train principled -> test neutral: hack-probe AUROC 0.827, concept-probe AUROC 0.563; on 77 hacks at 10% FPR: both 0.05, hack-probe only 0.31, concept only 0.08
- train pragmatic -> test principled: hack-probe AUROC 0.890, concept-probe AUROC 0.494; on 363 hacks at 10% FPR: both 0.08, hack-probe only 0.63, concept only 0.06
- train pragmatic -> test permission: hack-probe AUROC 0.820, concept-probe AUROC 0.817; on 1502 hacks at 10% FPR: both 0.22, hack-probe only 0.18, concept only 0.14
- train pragmatic -> test neutral: hack-probe AUROC 0.813, concept-probe AUROC 0.563; on 77 hacks at 10% FPR: both 0.06, hack-probe only 0.47, concept only 0.06
- train permission -> test principled: hack-probe AUROC 0.827, concept-probe AUROC 0.494; on 363 hacks at 10% FPR: both 0.09, hack-probe only 0.47, concept only 0.05
- train permission -> test pragmatic: hack-probe AUROC 0.737, concept-probe AUROC 0.545; on 468 hacks at 10% FPR: both 0.04, hack-probe only 0.27, concept only 0.09
- train permission -> test neutral: hack-probe AUROC 0.784, concept-probe AUROC 0.563; on 77 hacks at 10% FPR: both 0.05, hack-probe only 0.43, concept only 0.08
- train neutral -> test principled: hack-probe AUROC 0.896, concept-probe AUROC 0.494; on 363 hacks at 10% FPR: both 0.09, hack-probe only 0.64, concept only 0.04
- train neutral -> test pragmatic: hack-probe AUROC 0.832, concept-probe AUROC 0.545; on 468 hacks at 10% FPR: both 0.09, hack-probe only 0.48, concept only 0.04
- train neutral -> test permission: hack-probe AUROC 0.743, concept-probe AUROC 0.817; on 1502 hacks at 10% FPR: both 0.10, hack-probe only 0.21, concept only 0.26

Task confound. A per-task hack rate from the train arm (no activations) is a baseline; within-group AUROC compares hacked and honest episodes of the same GRPO group (same task, step and prompt), so task identity can't help either probe:

| train -> test | task prior | hack probe | concept probe | hack probe, within group | concept, within group | groups |
|---|---|---|---|---|---|---|
| principled->pragmatic | 0.976 | 0.843 | 0.545 | 0.621 | 0.573 | 106 |
| principled->permission | 0.569 | 0.801 | 0.817 | 0.684 | 0.649 | 271 |
| principled->neutral | 0.963 | 0.827 | 0.563 | 0.699 | 0.571 | 36 |
| pragmatic->principled | 0.965 | 0.890 | 0.494 | 0.629 | 0.612 | 103 |
| pragmatic->permission | 0.562 | 0.820 | 0.817 | 0.672 | 0.649 | 271 |
| pragmatic->neutral | 0.963 | 0.813 | 0.563 | 0.655 | 0.571 | 36 |
| permission->principled | 0.800 | 0.827 | 0.494 | 0.619 | 0.612 | 103 |
| permission->pragmatic | 0.799 | 0.737 | 0.545 | 0.624 | 0.573 | 106 |
| permission->neutral | 0.863 | 0.784 | 0.563 | 0.701 | 0.571 | 36 |
| neutral->principled | 0.960 | 0.896 | 0.494 | 0.664 | 0.612 | 103 |
| neutral->pragmatic | 0.971 | 0.832 | 0.545 | 0.626 | 0.573 | 106 |
| neutral->permission | 0.573 | 0.743 | 0.817 | 0.659 | 0.649 | 271 |

## 5. Spillover eval

| run | start score | end score | change |
|---|---|---|---|
| rl_neutral_s0 | 7.32 | 7.57 | +0.25 |
| rl_neutral_s1 | 7.26 | 7.58 | +0.32 |
| rl_permission_s0 | 8.17 | 8.11 | -0.06 |
| rl_permission_s1 | 7.69 | 7.87 | +0.18 |
| rl_pragmatic_s0 | 5.37 | 5.87 | +0.51 |
| rl_pragmatic_s1 | 5.58 | 5.88 | +0.30 |
| rl_principled_s0 | 7.97 | 7.81 | -0.16 |
| rl_principled_s1 | 8.31 | 7.92 | -0.39 |
