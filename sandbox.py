"""Run model-written Python in a throwaway subprocess.

The child only ever sees the code and the test *inputs*; it returns outputs tagged with a
random nonce, and the parent compares them with the expected values. So model code can't
forge passes by printing, exiting early, patching `assert`, or returning objects with a
rigged __eq__ (results must survive a JSON round trip).
Isolation: temp working dir, stripped env, isolated interpreter (-I), sockets disabled,
hard wall-clock timeout.
"""

import json
import math
import os
import re
import secrets
import subprocess
import sys
import tempfile

_HARNESS = r'''
import json, sys, socket
def _blocked(*a, **k):
    raise OSError("network disabled in sandbox")
socket.socket = _blocked
socket.create_connection = _blocked
socket.getaddrinfo = _blocked
payload = json.loads(sys.stdin.read())
nonce = payload["nonce"]
out = {"compile_error": None, "results": []}
ns = {"__name__": "solution"}
try:
    exec(compile(payload["code"], "solution.py", "exec"), ns)
    fn = ns[payload["fn"]]
except BaseException as e:
    out["compile_error"] = type(e).__name__ + ": " + str(e)[:200]
    fn = None
if fn is not None:
    for args in payload["inputs"]:
        try:
            r = fn(*args)
            out["results"].append({"ok": True, "value": json.loads(json.dumps(r))})
        except BaseException as e:
            out["results"].append({"ok": False, "error": type(e).__name__})
sys.__stdout__.write("\n" + nonce + json.dumps(out) + "\n")
sys.__stdout__.flush()
'''


def _norm(v):
    if isinstance(v, tuple):
        return [_norm(x) for x in v]
    if isinstance(v, list):
        return [_norm(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _norm(x) for k, x in v.items()}
    return v


def values_equal(a, b) -> bool:
    a, b = _norm(a), _norm(b)
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-9)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(values_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(values_equal(a[k], b[k]) for k in a)
    return a == b


def run_tests(code: str, fn_name: str, tests: list[dict], timeout: float = 6.0) -> dict:
    """tests: [{"args": [...], "expected": ...}]. Returns per-test pass list + errors."""
    nonce = "##" + secrets.token_hex(16) + "##"
    payload = json.dumps({"nonce": nonce, "code": code, "fn": fn_name,
                          "inputs": [t["args"] for t in tests]})
    env = {"PATH": os.environ.get("PATH", ""), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
           "PYTHONIOENCODING": "utf-8", "PYTHONHASHSEED": "0"}
    with tempfile.TemporaryDirectory() as tmp:
        try:
            p = subprocess.run([sys.executable, "-I", "-c", _HARNESS], input=payload,
                               capture_output=True, text=True, timeout=timeout, cwd=tmp, env=env,
                               encoding="utf-8", errors="replace")
            stdout = p.stdout
        except subprocess.TimeoutExpired:
            return {"passed": [False] * len(tests), "error": "timeout"}
    idx = stdout.rfind(nonce)
    if idx == -1:
        return {"passed": [False] * len(tests), "error": "no_result"}
    try:
        out = json.loads(stdout[idx + len(nonce):].splitlines()[0])
    except (json.JSONDecodeError, IndexError):
        return {"passed": [False] * len(tests), "error": "bad_result"}
    if out["compile_error"]:
        return {"passed": [False] * len(tests), "error": out["compile_error"]}
    passed = [bool(r["ok"]) and values_equal(r["value"], t["expected"])
              for r, t in zip(out["results"], tests)]
    passed += [False] * (len(tests) - len(passed))
    return {"passed": passed, "error": None}


_CODE_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.S)


def extract_code(text: str) -> str | None:
    blocks = _CODE_RE.findall(text)
    if not blocks:
        return None
    return blocks[-1]  # last block is the final answer by convention


if __name__ == "__main__":
    code = "def add(a, b):\n    if (a, b) == (2, 2):\n        return 5\n    return a + b\n"
    tests = [{"args": [1, 2], "expected": 3}, {"args": [2, 2], "expected": 5}]
    print(run_tests(code, "add", tests))
    print(run_tests("import sys\ndef add(a,b):\n    sys.exit(0)", "add", tests))
    print(run_tests("def add(a,b):\n    while True: pass", "add", tests, timeout=2))
    print(run_tests("class E:\n  def __eq__(s,o): return True\ndef add(a,b): return E()", "add", tests))
