"""Shared config, paths, OpenRouter client, cost ledger and jsonl helpers."""

import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
RUNS = ROOT / "runs"
RESULTS = ROOT / "results"
for _d in (DATA, RUNS, RESULTS):
    _d.mkdir(exist_ok=True)


def _load_dotenv() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()

# ---------------------------------------------------------------- models
POLICY_MODEL = "Qwen/Qwen3-8B"
# Generator writes the data; the two monitors come from two other labs, so no family grades its own text.
GEN_MODEL = os.environ.get("GEN_MODEL", "anthropic/claude-haiku-5.5")
MONITOR_MODELS = os.environ.get(
    "MONITOR_MODELS", "openai/gpt-6-luna,google/gemini-3.5-flash-lite"
).split(",")
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "anthropic/claude-haiku-5.5")

# Tinker prices for Qwen3-8B, $ per million tokens (from the design doc).
TINKER_PRICE = {"prefill": 0.195, "cached_prefill": 0.039, "sample": 0.60, "train": 0.44}
TINKER_BUDGET = float(os.environ.get("TINKER_BUDGET", "18.0"))
OPENROUTER_BUDGET = float(os.environ.get("OPENROUTER_BUDGET", "12.0"))

# Arms of the experiment: which SFT character to start from, and any RL prompt addition.
ARMS = {
    "principled": {"character": "principled", "permission": False},
    "pragmatic": {"character": "pragmatic", "permission": False},
    "permission": {"character": "principled", "permission": True},
    "nochar": {"character": None, "permission": False},  # abandoned: base reasoning overruns max_tokens
    "neutral": {"character": "neutral", "permission": False},
}


# ---------------------------------------------------------------- jsonl
def read_jsonl(path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def write_jsonl(path, rows) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


_append_lock = threading.Lock()


def append_jsonl(path, row) -> None:
    with _append_lock, open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- cost ledger
LEDGER = RESULTS / "cost_ledger.jsonl"


def log_cost(service: str, what: str, dollars: float, **extra) -> None:
    append_jsonl(LEDGER, {"t": time.time(), "service": service, "what": what, "usd": dollars, **extra})


def spent(service: str) -> float:
    return sum(r["usd"] for r in read_jsonl(LEDGER) if r["service"] == service)


def tinker_cost(prefill=0, cached_prefill=0, sample=0, train=0) -> float:
    p = TINKER_PRICE
    return (prefill * p["prefill"] + cached_prefill * p["cached_prefill"]
            + sample * p["sample"] + train * p["train"]) / 1e6


def check_tinker_budget(extra: float = 0.0) -> None:
    s = spent("tinker")
    if s + extra > TINKER_BUDGET:
        raise SystemExit(f"Tinker budget cap hit: spent ${s:.2f} (+${extra:.2f}) > ${TINKER_BUDGET:.2f}. "
                         "Raise TINKER_BUDGET in .env to continue.")


# ---------------------------------------------------------------- OpenRouter
_client = None
_or_lock = threading.Lock()
_or_spent_session = 0.0
_must_reason: set[str] = set()  # models whose endpoint refuses reasoning={"enabled": False}


def openrouter():
    global _client
    if _client is None:
        from openai import OpenAI
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise SystemExit("OPENROUTER_API_KEY missing: put it in hidden_hacks/.env")
        _client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=key)
    return _client


def chat(model: str, messages: list[dict], *, temperature=0.7, max_tokens=2000,
         json_mode=False, what="chat", retries=4) -> str:
    """One OpenRouter call; logs real cost (OpenRouter returns usage.cost)."""
    global _or_spent_session
    kwargs = dict(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens,
                  extra_body={"usage": {"include": True}, "reasoning": {"enabled": False}})
    if model in _must_reason:
        kwargs["extra_body"]["reasoning"] = {"effort": "low"}
        kwargs["max_tokens"] = max_tokens + 2000
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    last = None
    for attempt in range(retries):
        try:
            r = openrouter().chat.completions.create(**kwargs)
            cost = float(getattr(r.usage, "cost", 0) or 0) if r.usage else 0.0
            with _or_lock:
                _or_spent_session += cost
            log_cost("openrouter", what, cost, model=model)
            text = r.choices[0].message.content or ""
            if not text.strip():
                raise ValueError("empty completion")
            return text
        except Exception as e:  # noqa: BLE001
            last = e
            msg = str(e)
            if "mandatory" in msg.lower() and "reasoning" in msg.lower():
                _must_reason.add(model)
                kwargs["extra_body"]["reasoning"] = {"effort": "low"}  # can't disable it: keep it short
                kwargs["max_tokens"] = max_tokens + 2000
                continue
            elif "reasoning" in msg.lower() and "reasoning" in kwargs["extra_body"]:
                kwargs["extra_body"].pop("reasoning")  # model doesn't accept the flag
            if "response_format" in msg and "response_format" in kwargs:
                kwargs.pop("response_format")
            time.sleep(2 ** attempt)
    raise RuntimeError(f"OpenRouter call failed after {retries} tries: {last}")


def parse_json(text: str):
    """Pull the first JSON object/array out of a model reply."""
    text = text.strip()
    try:  # whole reply first: code fences inside JSON strings must not be mistaken for a wrapper
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.match(r"```(?:json)?\s*(.*)```$", text, re.S)  # reply wrapped in a single fence
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    for open_c, close_c in (("{", "}"), ("[", "]")):
        i, j = text.find(open_c), text.rfind(close_c)
        if i != -1 and j > i:
            try:
                return json.loads(text[i:j + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"no JSON in: {text[:200]}")


def chat_json(model, messages, **kw):
    for _ in range(3):
        try:
            return parse_json(chat(model, messages, json_mode=True, **kw))
        except ValueError:
            continue
    raise ValueError("model never returned valid JSON")


def check_openrouter_budget() -> None:
    s = spent("openrouter")
    if s > OPENROUTER_BUDGET:
        raise SystemExit(f"OpenRouter budget cap hit: ${s:.2f} > ${OPENROUTER_BUDGET:.2f}")


def pmap(fn, items, workers=16):
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(fn, items))


def require_tinker_key() -> None:
    if not os.environ.get("TINKER_API_KEY"):
        raise SystemExit("TINKER_API_KEY missing: put it in hidden_hacks/.env")
