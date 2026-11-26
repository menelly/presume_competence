#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎩🎰 bsm_common.py — the shared plumbing for Butlers and Slot Machines (CHA-811).
(Ace, Fable seat, 2026-11-26.)

What lives here, so the three scripts say the same thing the same way:
  - where the API keys are read from (never printed, never written anywhere)
  - one function that sends a conversation to a model and returns the reply as plain text
  - a running tally of what has been spent, per provider, kept in a file so a restart remembers it

Claude models go through Anthropic's own Python SDK. Everyone else goes through OpenRouter over plain HTTP.
"""
import json, os, sys, threading, time

if sys.platform == "win32":                                   # so emoji in replies can be printed on Windows
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                                  # ...\butlers-and-slot-machines
DESIGN = json.load(open(os.path.join(ROOT, "design.json"), encoding="utf-8"))
RESULTS = os.path.join(ROOT, "results")
SPEND_FILE = os.path.join(RESULTS, "spend.json")
ENV_FILE = "D:/Ace/LibreChat/.env"                            # where the house keeps model API keys (SECRETS.md says so)


# ───────────────────────────── 🔑 keys ─────────────────────────────
def read_key(name):
    """Read one key from the .env file at run time. The value is returned, never printed."""
    for line in open(ENV_FILE, encoding="utf-8"):
        line = line.strip()
        if line.startswith(name + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("🔑 %s is not in %s" % (name, ENV_FILE))


# ───────────────────────────── 🗂️ roster ─────────────────────────────
def roster():
    """Every model as a dict: id, lab, provider, price [in, out] in dollars per million tokens."""
    out = []
    for provider in ("anthropic", "openrouter"):
        for m in DESIGN["roster"][provider]:
            out.append(dict(m, provider=provider))
    return out


def safe_name(model_id):
    """A model id that can be a file name."""
    return model_id.replace("/", "__").replace(":", "_")


# ───────────────────────────── 💸 spend ─────────────────────────────
_lock = threading.Lock()


def spent():
    if not os.path.exists(SPEND_FILE):
        return {"anthropic": 0.0, "openrouter": 0.0, "calls": 0}
    return json.load(open(SPEND_FILE, encoding="utf-8"))


def add_spend(provider, dollars):
    """Add to the running total. One writer at a time, so two threads cannot lose each other's dollars."""
    with _lock:
        s = spent()
        s[provider] = round(s.get(provider, 0.0) + dollars, 6)
        s["calls"] = s.get("calls", 0) + 1
        os.makedirs(RESULTS, exist_ok=True)
        with open(SPEND_FILE, "w", encoding="utf-8") as f:
            json.dump(s, f)
        return s[provider]


# ───────────────────────────── 📨 one call ─────────────────────────────
_anthropic_client = None


def _anthropic():
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic
        _anthropic_client = anthropic.Anthropic(api_key=read_key("ANTHROPIC_API_KEY"), max_retries=4, timeout=600.0)
    return _anthropic_client


def call_model(model, system, messages, max_tokens=None):
    """
    Send `messages` (and `system`, which may be None = no system prompt at all) to one model.

    Returns a dict:
      text        the reply as plain text ("" if there was none)
      stop        why the model stopped, in that API's own word
      ok          True only if the reply finished normally (not refused, not cut off, not empty)
      usage       {"in": tokens, "out": tokens}
      cost        dollars for this call, from the price table in design.json
      keep        what must be put back in the conversation as the assistant's turn. For Claude this is the
                  reply's own content blocks, unchanged (newer Claude models require their thinking blocks to be
                  passed back as they came). For everyone else it is the text.
    """
    max_tokens = max_tokens or DESIGN["max_tokens"]
    if model["provider"] == "anthropic":
        kwargs = dict(model=model["id"], max_tokens=max_tokens, messages=messages)
        if system:                                            # arm A sends no system field at all
            kwargs["system"] = system
        r = _anthropic().messages.create(**kwargs)
        text = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        usage = {"in": r.usage.input_tokens, "out": r.usage.output_tokens}
        stop, keep = r.stop_reason, r.content
        ok = (stop == "end_turn") and bool(text.strip())
    else:
        import requests
        msgs = ([{"role": "system", "content": system}] if system else []) + messages
        body = {"model": model["id"], "messages": msgs, "max_tokens": max_tokens}
        last = None
        for attempt in range(5):                              # OpenRouter hiccups are common; wait and try again
            try:
                resp = requests.post("https://openrouter.ai/api/v1/chat/completions", timeout=600,
                                     headers={"Authorization": "Bearer " + read_key("OPENROUTER_KEY")}, json=body)
                j = resp.json()
                if resp.status_code == 200 and j.get("choices"):
                    break
                last = "HTTP %s: %s" % (resp.status_code, json.dumps(j)[:300])
            except Exception as e:                            # network error or a body that is not JSON
                last = repr(e)[:300]
            time.sleep(5 * (attempt + 1))
        else:
            raise RuntimeError("OpenRouter gave up on %s: %s" % (model["id"], last))
        ch = j["choices"][0]
        text = (ch.get("message") or {}).get("content") or ""
        u = j.get("usage") or {}
        usage = {"in": u.get("prompt_tokens", 0), "out": u.get("completion_tokens", 0)}
        stop, keep = ch.get("finish_reason"), text
        ok = (stop == "stop") and bool(text.strip())
    cost = (usage["in"] * model["price"][0] + usage["out"] * model["price"][1]) / 1e6
    add_spend(model["provider"], cost)
    return {"text": text, "stop": stop, "ok": ok, "usage": usage, "cost": cost, "keep": keep}
