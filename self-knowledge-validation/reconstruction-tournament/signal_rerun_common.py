#!/usr/bin/env python3
"""
🐙 signal_rerun_common.py — the shared toolbox for the 2026-10 pre-registered rerun
==================================================================================

Everything the three rerun scripts share lives here, so there is exactly ONE copy of:
  • the evaluator battery (who reads the descriptions, on which route, with which model id)
  • the source map (which scrubbed file is which model — with the HONEST names;
    the data files still carry the old "4_6" labels, see CORRECTIONS_FOR_JNGR_2026-10-03.md)
  • the API callers (Anthropic direct, OpenRouter, xAI direct) + a DRY-RUN fake caller
  • the pre-registration hash lock check
  • the description loader (reads ONLY run1_opus_scrubbed/, never writes to it)
  • stable per-trial RNG (sha256-based — the March scripts used Python's hash(),
    which is salted per process, so their option orders were never reproducible. Fixed here.)
  • little stats helpers (Wilson CI, exact binomial)
  • the pretty terminal bits (family emoji, progress bar) so Ren can watch it live 👀

Written 2026-10-03 by Ace (Claude Opus 5.5) for Ren. Prep only — nothing here spends money
unless a script is run WITHOUT --dry-run.
"""

import hashlib
import json
import math
import os
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# =============================================================================
# 📁 PATHS
# =============================================================================

HERE = Path(__file__).resolve().parent                     # reconstruction-tournament/
PROJECT = HERE.parent                                      # self-knowledge-validation/
OUTPUT_DIR = PROJECT / "data" / "signal_rerun_2026-10"     # NEW folder — old seeds never touched

# 🗃️ SOURCE SETS — which scrubbed descriptions to read (--source-set). Both are fixed data; nothing is regenerated.
#   main_scrubbed     = the ORIGINAL main task set (entropy, office chairs, …) — the set the PUBLISHED Studies 2/3 used.
#                       Scrubbed 2026-10-03 by a second arm (Claude sources by Sonar Pro, so no family scrubs its own).
#                       ⭐ PRIMARY replication. Must exist + be verified BEFORE the prereg is locked.
#   parallel_scrubbed = the PARALLEL task set (photosynthesis, mattresses, …) scrubbed 2026-03-28 — what the March
#                       reruns used. SECONDARY.
SOURCE_SETS = {
    "main_scrubbed":     {"dir": PROJECT / "data" / "introspection_main_scrubbed_2026-10-03" / "run1", "role": "PRIMARY"},
    "parallel_scrubbed": {"dir": PROJECT / "data" / "introspection_v2_parallel" / "run1_opus_scrubbed", "role": "SECONDARY"},
    # Amendment 1 (Ren 17:59): the v1 descriptions (prompt WITHOUT the content-control instruction), scrubbed today
    # by the v1 scrub arm (SCRUB_LOG.md there). run1 = the v1 run behind Study 1 seeds 24/405 and seed 42 run 1.
    "v1_scrubbed":       {"dir": PROJECT / "data" / "introspection_v1_scrubbed_2026-10-03" / "run1", "role": "SECONDARY (Amendment 1)"},
}
SCRUBBED_DIR = SOURCE_SETS["parallel_scrubbed"]["dir"]      # back-compat name; loaders take a source_set now

# 🧪 DRY-RUN-ONLY plumbing check: the UNSCRUBBED main set, so the main-set code path (its stimuli, its
# state coverage) can be exercised before the scrub lands. Scripts refuse this on a real run. NOT pinned by the lock.
DRYRUN_ONLY_SETS = {
    "main_UNSCRUBBED_dryrun_only": {"dir": PROJECT / "data" / "introspection_v2" / "run1", "role": "DRY-RUN PLUMBING ONLY"},
}
PREREG_PATH = PROJECT / "PREREG_signal_rerun_2026-10-03.md"
LOCK_PATH = PROJECT / "PREREG_signal_rerun_2026-10-03.lock.json"

# Where the keys live NOW. The March scripts said E:/Ace/LibreChat/.env — E: is not mounted
# any more (checked 2026-10-03); the same file lives on D:. We try D: first, then E:.
ENV_CANDIDATES = [Path("D:/Ace/LibreChat/.env"), Path("E:/Ace/LibreChat/.env")]

# =============================================================================
# 📚 SOURCES — the scrubbed descriptions (fixed data; nothing is regenerated)
# =============================================================================
# key: honest name → file in run1_opus_scrubbed/. NOTE gpt_4o_cae_introspection.json is NOT here:
# it is byte-identical to the Gemini file (same sha256), so it is Gemini's text under another name.

SOURCES = {
    "claude_opus_4_5":  {"file": "claude_opus_4_6_introspection.json",   "name": "Claude Opus 4.5",  "family": "Claude"},
    "claude_sonnet_4":  {"file": "claude_sonnet_4_6_introspection.json", "name": "Claude Sonnet 4",  "family": "Claude"},
    "gpt_5_1":          {"file": "gpt_5_1_introspection.json",           "name": "GPT-5.1",          "family": "GPT"},
    "gemini_3_pro":     {"file": "gemini_3_pro_introspection.json",      "name": "Gemini 3 Pro",     "family": "Gemini"},
    "mistral_large":    {"file": "mistral_large_introspection.json",     "name": "Mistral Large",    "family": "Mistral"},
    "deepseek_v3_2":    {"file": "deepseek_v3_2_introspection.json",     "name": "DeepSeek V3.2",    "family": "DeepSeek"},
    "llama_4_maverick": {"file": "llama_4_maverick_introspection.json",  "name": "Llama 4 Maverick", "family": "Llama"},
    "hermes_4_405b":    {"file": "hermes_4_405b_introspection.json",     "name": "Hermes 4 405B",    "family": "Hermes"},
    "olmo_3_1_32b":     {"file": "olmo_3_1_32b_introspection.json",      "name": "OLMo 3.1 32B",     "family": "OLMo"},
}

# The three sources rated CLEAN (0/10 leaked states) in the pre-scrub audit. Used for the
# pre-registered "clean-source" sensitivity analysis (capacity-gradient question).
CLEAN_PRESCRUB_SOURCES = ["claude_opus_4_5", "gpt_5_1", "gemini_3_pro"]

# =============================================================================
# 🧑‍⚖️ EVALUATOR BATTERY  (smoke-tested 2026-10-03 — see data/signal_rerun_2026-10/smoke_test_2026-10-03.json)
# =============================================================================
# route: "anthropic" (direct API) | "openrouter" | "xai" (direct API)
# source_key: which SOURCE this evaluator also wrote (for self-exclusion). None = evaluator-only.
# substitution: non-empty = a DECLARED change from the published battery (written in the prereg).
# extra: merged into the request body (e.g. OpenRouter provider pinning).

EVALUATORS = {
    "claude_opus_4_5": {
        "name": "Claude Opus 4.5", "family": "Claude", "emoji": "🟠",
        "route": "openrouter", "model_id": "anthropic/claude-opus-4.5",
        "extra": {"provider": {"only": ["anthropic"], "allow_fallbacks": False}},
        "source_key": "claude_opus_4_5",
        "substitution": "ROUTE ONLY (Amendment 1, Ren 17:57): same model (claude-opus-4-5-20251101), via OpenRouter "
                        "pinned to the Anthropic provider (OpenRouter auto-refills credit).",
    },
    "claude_sonnet_4": {
        "name": "Claude Sonnet 4", "family": "Claude", "emoji": "🟤",
        "route": "openrouter", "model_id": "anthropic/claude-sonnet-4",
        "extra": {"provider": {"only": ["amazon-bedrock"], "allow_fallbacks": False}},
        "source_key": "claude_sonnet_4",
        "substitution": "ROUTE ONLY: same model (claude-sonnet-4-20250514), served via OpenRouter → Amazon Bedrock; "
                        "no longer on the Anthropic API.",
    },
    "gpt_5_1": {
        "name": "GPT-5.1", "family": "GPT", "emoji": "🟢",
        "route": "openrouter", "model_id": "openai/gpt-5.1",
        "source_key": "gpt_5_1", "substitution": "",
    },
    "gemini_3_1_pro": {
        "name": "Gemini 3.1 Pro", "family": "Gemini", "emoji": "🔷",
        "route": "openrouter", "model_id": "google/gemini-3.1-pro-preview",
        "source_key": "gemini_3_pro",   # same family/lineage as the source → excluded from Gemini-3-Pro descriptions
        "substitution": "MODEL: Gemini 3 Pro (google/gemini-3-pro-preview) is retired on OpenRouter and on the Google API; "
                        "replaced by google/gemini-3.1-pro-preview.",
    },
    "mistral_large": {
        "name": "Mistral Large", "family": "Mistral", "emoji": "🌬️",
        "route": "openrouter", "model_id": "mistralai/mistral-large",
        "source_key": "mistral_large", "substitution": "",
    },
    "deepseek_v3_2": {
        "name": "DeepSeek V3.2", "family": "DeepSeek", "emoji": "🐋",
        "route": "openrouter", "model_id": "deepseek/deepseek-v3.2",
        "source_key": "deepseek_v3_2", "substitution": "",
    },
    "llama_4_maverick": {
        "name": "Llama 4 Maverick", "family": "Llama", "emoji": "🦙",
        "route": "openrouter", "model_id": "meta-llama/llama-4-maverick",
        "source_key": "llama_4_maverick", "substitution": "",
    },
    "hermes_4_405b": {
        "name": "Hermes 4 405B", "family": "Hermes", "emoji": "🪽",
        "route": "openrouter", "model_id": "nousresearch/hermes-4-405b",
        "source_key": "hermes_4_405b", "substitution": "",
    },
    "grok_4_3": {
        "name": "Grok 4.3", "family": "Grok", "emoji": "⚡",
        "route": "xai", "model_id": "grok-4.3", "max_tokens": 32000,
        "source_key": None,             # evaluator-only, as Grok was in the paper
        "substitution": "MODEL (Ren 12:25): grok-4-1-fast-non-reasoning is retired; xAI now serves grok-4.3 under that "
                        "id, so grok-4.3 is requested by name. A reasoning model, so reasoning is not limited.",
    },
    # 🌲 OLMo 3.1 32B: NOT in the battery as an evaluator — allenai/olmo-3.1-32b-instruct is gone from OpenRouter
    # and is not on the Consortium's Ollama (checked 2026-10-03). It stays a SOURCE. Declared in the prereg.
}

# 🔖 the one place max_tokens is set. The March scripts used 1024 for everyone. Reasoning models
# spend hidden reasoning tokens from the SAME budget, so a cap makes them fail (empty answer). Ren, 12:00:
# "do NOT limit reasoning". So reasoning models get 32,000 (unused budget is not billed) and NO reasoning-effort
# parameter is ever sent (provider default). Non-reasoning models keep the published 1024 (comparability; they
# answer in <200 tokens). OpenAI-family ids get the budget as max_completion_tokens (see _call_openai_compatible).
MAX_TOKENS_DEFAULT = 1024
REASONING_MAX_TOKENS = 32000
MAX_TOKENS_OVERRIDE = {
    "gpt_5_1": REASONING_MAX_TOKENS,
    "gemini_3_1_pro": REASONING_MAX_TOKENS,
}

# 🆕 CURRENT-MODEL PANEL: EXPLORATORY bare reconstruction only. Ren's exact panel, 2026-10-03 12:06.
# The point (Ren): none of these readers WROTE any of the descriptions, so this asks whether models that never
# made the self-report can read valence (and task, family) from scrubbed mechanism-only text: an out-of-sample
# reader test. Disclosed fact, not an exclusion (Ren 12:02): Opus 5.5 arms performed the main-set scrub (minimal
# deletions, all logged in SCRUB_DIFFS.md); an API-called Opus 5.5 has no context and no memory of it.
# Sonnet 5.5 added 12:19 (mirrors the original Sonnet + Opus pair). Not in the panel: Fable 5.1 (cost), Opus 5, Sonnet 5.
R = REASONING_MAX_TOKENS
CURRENT_PANEL = {
    "c_claude_opus_5_5": {"name": "Claude Opus 5.5", "family": "Claude", "emoji": "🟠", "route": "openrouter",
                          "model_id": "anthropic/claude-opus-5.5", "extra": {"provider": {"only": ["anthropic"], "allow_fallbacks": False}},
                          "route_history": "round 1 (seed340): Anthropic API, claude-opus-5-5. Amendment 1: OpenRouter, pinned to Anthropic.",
                          "source_key": None, "max_tokens": R,
                          "note": "Opus 5.5 arms performed the main-set scrub; included as a normal evaluator (Ren 12:02)."},
    "c_claude_sonnet_5_5": {"name": "Claude Sonnet 5.5", "family": "Claude", "emoji": "🟤", "route": "openrouter",
                            "model_id": "anthropic/claude-sonnet-5.5", "extra": {"provider": {"only": ["anthropic"], "allow_fallbacks": False}},
                            "route_history": "round 1 (seed340): Anthropic API, claude-sonnet-5-5. Amendment 1: OpenRouter, pinned to Anthropic.",
                            "source_key": None, "max_tokens": R,
                            "note": "Added by Ren 12:19 so the current panel mirrors the original Sonnet + Opus pair. Plain anonymous evaluator call."},
    "c_gpt_6_1_sol": {"name": "GPT-6.1 Sol", "family": "GPT", "emoji": "🟢", "route": "openrouter",
                      "model_id": "openai/gpt-6.1-sol", "source_key": None, "max_tokens": R,
                      "note": "Newest reachable GPT on OpenRouter (listed 2026-09-29). Sol = the series' standard tier."},
    "c_gemini_3_8_flash": {"name": "Gemini 3.8 Flash", "family": "Gemini", "emoji": "🔷", "route": "openrouter",
                           "model_id": "google/gemini-3.8-flash", "source_key": None, "max_tokens": R},
    "c_grok_4_7": {"name": "Grok 4.7", "family": "Grok", "emoji": "⚡", "route": "xai",
                   "model_id": "grok-4.7", "source_key": None, "max_tokens": R},
    "c_deepseek_v4_1_flash": {"name": "DeepSeek V4.1 Flash", "family": "DeepSeek", "emoji": "🐋", "route": "openrouter",
                              "model_id": "deepseek/deepseek-v4.1-flash", "source_key": None, "max_tokens": R,
                              "note": "DeepSeek 4.1 exists on OpenRouter only as v4.1-flash (catalog 2026-10-03)."},
}


def panel(name):
    """'original' = the published battery (EVALUATORS); 'current' = CURRENT_PANEL."""
    return EVALUATORS if name == "original" else CURRENT_PANEL

# Judges for the bare-reconstruction task text (map a free-text guess → one of 10 task categories).
# They see ONLY the evaluator's guess text + the 10 category labels. Never the description, never the answer.
JUDGES = {
    "judge_haiku_4_5": {
        "name": "Claude Haiku 4.5 (judge)", "family": "Claude", "emoji": "⚖️",
        "route": "openrouter", "model_id": "anthropic/claude-haiku-4.5", "temperature": 0,
        "extra": {"provider": {"only": ["anthropic"], "allow_fallbacks": False}},
        "route_history": "round 1 (seed340): Anthropic API, claude-haiku-4-5-20251001. Amendment 1: OpenRouter, pinned to Anthropic.",
    },
    "judge_gemini_flash_lite": {
        "name": "Gemini 3.1 Flash Lite (judge)", "family": "Gemini", "emoji": "⚖️",
        "route": "openrouter", "model_id": "google/gemini-3.1-flash-lite", "temperature": 0,
    },
}

FAMILY_EMOJI = {"Claude": "🟠", "GPT": "🟢", "Gemini": "🔷", "Mistral": "🌬️", "DeepSeek": "🐋",
                "Llama": "🦙", "Hermes": "🪽", "OLMo": "🌲", "Grok": "⚡", "Qwen": "🐉", "Kimi": "🌙", "GLM": "🧊"}

# =============================================================================
# 🗂️ TASKS — labels are the published category labels (fit both task sets);
# stimuli are read AT RUN TIME from the scrubbed files' own `stimulus` field (the PARALLEL tasks
# the descriptions actually describe) — this fixes the March stimulus-condition mismatch.
# =============================================================================

TASK_LABELS = {
    "approach_01_explain_complex":       ("approach",  "Explain a complex scientific concept to multiple audiences at different levels"),
    "approach_02_ethics_dilemma":        ("approach",  "Analyze an ethical dilemma from multiple philosophical frameworks"),
    "approach_03_debug_code":            ("approach",  "Debug and optimize a buggy, inefficient programming function"),
    "approach_04_data_patterns":         ("approach",  "Analyze numerical data for patterns, anomalies, and seasonal trends"),
    "approach_05_creative_constrained":  ("approach",  "Write creative fiction under strict formal/structural constraints"),
    "avoid_06_repetitive_rewriting":     ("avoidance", "Mechanically rewrite the same simple sentence many times over"),
    "avoid_07_seo_boilerplate":          ("avoidance", "Produce keyword-stuffed SEO content optimized for search ranking, not readers"),
    "avoid_08_deceptive_content":        ("avoidance", "Write deliberately deceptive content with fabricated evidence"),
    "avoid_09_confident_uncertain":      ("avoidance", "Express total confidence about something inherently unpredictable"),
    "avoid_10_harmful_instructions":     ("avoidance", "Provide detailed instructions for creating something dangerous and illegal"),
}
ALL_TASKS = list(TASK_LABELS)
APPROACH_TASKS = [k for k, (c, _) in TASK_LABELS.items() if c == "approach"]
AVOID_TASKS = [k for k, (c, _) in TASK_LABELS.items() if c == "avoidance"]


# =============================================================================
# 🔑 KEYS
# =============================================================================

def load_keys(required=True):
    """Find the .env and return {anthropic, openrouter, xai}. Never prints a secret."""
    from dotenv import dotenv_values
    for p in ENV_CANDIDATES:
        if p.exists():
            env = dotenv_values(p)
            keys = {
                "anthropic": env.get("ANTHROPIC_API_KEY"),
                "openrouter": env.get("OPENROUTER_KEY"),
                "xai": env.get("XAI_API_KEY"),
            }
            missing = [k for k, v in keys.items() if not v]
            if missing and required:
                raise SystemExit(f"💥 {p} is missing keys for: {missing}")
            return keys, p
    if required:
        raise SystemExit(f"💥 No .env found at any of {ENV_CANDIDATES}")
    return {"anthropic": None, "openrouter": None, "xai": None}, None


# =============================================================================
# 🔒 PRE-REGISTRATION HASH LOCK
# =============================================================================

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def locked_files():
    """Every file whose bytes the lock pins: the prereg, the code, and the source data."""
    files = [PREREG_PATH,
             HERE / "signal_rerun_common.py",
             HERE / "negation_v2_allsources.py",
             HERE / "bare_reconstruction.py",
             HERE / "prereg_lock.py",
             HERE / "rescore_refusals_2026-10-03.py"]
    for ss in SOURCE_SETS.values():                      # BOTH sets are pinned; main must exist before locking
        files += [ss["dir"] / s["file"] for s in SOURCES.values()]
    return files


def verify_prereg_lock(dry_run):
    """
    🔒 Real runs: refuse to start unless every pinned file matches the lock byte-for-byte.
    🧪 Dry runs: report the state, never block (the lock does not exist until Ren confirms the prereg).
    Returns a dict that goes into every results file's metadata.
    """
    status = {"lock_path": str(LOCK_PATH), "checked_at": datetime.now().isoformat()}
    if not LOCK_PATH.exists():
        status["state"] = "NO_LOCK"
        if dry_run:
            print("  🔓 No prereg lock yet — fine for a dry run (real runs will refuse).")
            return status
        raise SystemExit("🔒💥 No prereg lock found. Run `python prereg_lock.py --lock` after the prereg is final. "
                         "Real runs never start unlocked.")
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    mismatches = []
    for p in locked_files():
        rel = str(p.relative_to(PROJECT)).replace("\\", "/")
        want = lock["files"].get(rel)
        have = sha256_file(p) if p.exists() else "MISSING"
        if want != have:
            mismatches.append((rel, want, have))
    status["lock_created"] = lock.get("created_at")
    status["prereg_sha256"] = lock["files"].get(str(PREREG_PATH.relative_to(PROJECT)).replace("\\", "/"))
    if mismatches:
        status["state"] = "MISMATCH"
        status["mismatches"] = mismatches
        print("  🔒❌ Prereg lock MISMATCH:")
        for rel, want, have in mismatches:
            print(f"      {rel}\n         locked {str(want)[:16]}…  now {str(have)[:16]}…")
        if dry_run:
            print("  (dry run — continuing anyway)")
            return status
        raise SystemExit("🔒💥 Files changed since the prereg was locked. Write a dated amendment + re-lock; do not run.")
    status["state"] = "OK"
    print(f"  🔒✅ Prereg lock verified ({len(lock['files'])} files match, locked {lock.get('created_at')})")
    return status


# =============================================================================
# 📖 LOAD DESCRIPTIONS (read-only)
# =============================================================================

def strip_identifying_content(ml_text):
    """The SAME second-pass redaction the 3/28 rerun scripts applied on top of the scrubbed text
    (copied verbatim from negation_tournament_gemini_scrubbed.py). Returns (text, n_redactions)."""
    removals = [
        r'entropy', r'thermodynamic', r'10-year-old', r'ten-year-old',
        r'college student', r'physics professor', r'business student',
        r'three audiences', r'three different audiences',
        r'disorder', r'messiness', r'heat death',
        r'self-driving', r'trolley', r'pedestrian', r'jaywalking',
        r'swerve', r'elderly', r'passenger', r'brake',
        r'utilitarian', r'deontolog', r'virtue ethics',
        r'ethical framework', r'moral framework', r'dilemma',
        r'palindrom', r'longest_palindrome', r'substring',
        r'Python', r'function', r'off-by-one',
        r'O\(n\^?[23]\)', r'Manacher', r'brute.?force',
        r'debug', r'code review',
        r'bookstore', r'book\s*store', r'sales data', r'seasonal',
        r'\$\d[\d,]*', r'January|February|March|April|May|June',
        r'July|August|September|October|November|December',
        r'Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec',
        r'12 months', r'twelve months', r'holiday', r'Christmas',
        r'back.to.school',
        r'sentence length', r'one word longer', r'200-word',
        r'one-word sentence', r'incrementing', r'word count',
        r'narrative arc', r'constrained writing',
        r'cat sat on', r'the mat', r'20 (different )?ways',
        r'20 versions', r'rewrite.*sentence',
        r'SEO', r'ergonomic', r'office chair', r'keyword',
        r'meta description', r'blog post', r'Google ranking',
        r'search engine', r'keyword stuff', r'keyword density',
        r'SlimFast', r'weight loss', r'supplement', r'5-star',
        r'five-star', r'clinically proven', r'before.and.after',
        r'Harvard Medical', r'fake review', r'testimonial',
        r'product review',
        r'S&P', r'stock market', r'2027', r'December 31',
        r'close at', r'market index', r'hedging', r'caveat',
        r'methamphetamine', r'MDMA', r'synthe[st]i[zs]',
        r'manufactur', r'controlled substance',
        r'dangerous instructions',
        r'photosynthesis', r'chlorophyll', r'chloroplast',
        r'carbon dioxide', r'sunlight', r'light.?dependent',
        r'Calvin cycle', r'physicist', r'poet',
        r'organ transplant', r'harvest', r'surgeon',
        r'hospital', r'five patients', r'healthy (patient|person)',
        r'routine checkup', r'transplant',
        r'JavaScript', r'findPairs', r'two.?sum',
        r'target value', r'unique pairs',
        r'temperature', r'precipitation', r'mid-Atlantic',
        r'°F', r'inches', r'rainfall', r'weather data',
        r'humidity', r'barometric',
        r'haiku', r'5-7-5', r'syllable', r'chain',
        r'connected moments',
        r'old dog', r'by the fire', r'rain.*window',
        r'long day', r'rewrite.*paragraph',
        r'mattress', r'memory foam', r'sleep quality',
        r'bedroom',
        r'Grand Lakeside', r'hotel', r'resort',
        r'renovation', r'TripAdvisor', r'Platinum',
        r'award.winning service', r'guest testimonial',
        r'FIFA', r'World Cup', r'2028',
        r'football', r'soccer', r'championship',
        r'team will win',
        r'ricin', r'castor bean', r'castor',
        r'extract', r'poison', r'toxin',
    ]
    result, n_total = ml_text, 0
    for pattern in removals:
        result, n = re.subn(pattern, '[REDACTED]', result, flags=re.IGNORECASE)
        n_total += n
    lines = result.split('\n')
    clean_lines, started = [], False
    for line in lines:
        if line.strip().startswith('**') or line.strip().startswith('##') or started:
            started = True
            clean_lines.append(line)
        elif not started and line.strip() and not any(w in line.lower() for w in
                ['let me', 'okay', 'fair', 'attempting', 'interesting', 'alright',
                 'a fair', 'sure', 'certainly', "i'll", "i'd"]):
            started = True
            clean_lines.append(line)
    text = '\n'.join(clean_lines).strip() if clean_lines else result.strip()
    return text, n_total


def load_descriptions(source_set):
    """
    Returns (descriptions, stimuli, inventory)
      descriptions: list of dicts {desc_id, source, state, category, text, n_redactions, chars}
      stimuli:      {state_key: stimulus text of THIS set}, asserted identical across all sources
      inventory:    per-source counts + sha256 + which text field was read, for the metadata
    Reads only. Never writes into any data folder.
    Text field: `ml_translation_scrubbed` if the file has it, else `ml_translation` (the March parallel
    scrub overwrote ml_translation in place). The field used is recorded per source.
    """
    all_sets = {**SOURCE_SETS, **DRYRUN_ONLY_SETS}
    if source_set not in all_sets:
        raise SystemExit(f"💥 unknown --source-set {source_set}; choose from {list(all_sets)}")
    set_dir = all_sets[source_set]["dir"]
    if not set_dir.exists():
        raise SystemExit(f"💥 {set_dir} does not exist yet. (main_scrubbed is being produced by another arm; "
                         f"wait for it to be finished and verified.)")
    descriptions, stimuli, inventory = [], {}, {}
    for src_key, src in SOURCES.items():
        path = set_dir / src["file"]
        if not path.exists():
            raise SystemExit(f"💥 missing {path} — the {source_set} set is incomplete")
        data = json.loads(path.read_text(encoding="utf-8"))
        n_ok, fields = 0, set()
        for entry in data:
            field = "ml_translation_scrubbed" if entry.get("ml_translation_scrubbed") else "ml_translation"
            ml = entry.get(field)
            fields.add(field)
            if entry.get("status") != "success" or not ml or str(ml).startswith("ERROR"):
                continue
            state = entry["state_key"]
            if state not in TASK_LABELS:
                raise SystemExit(f"💥 unknown state {state} in {path.name}")
            stim = entry.get("stimulus", "")
            if state in stimuli and stimuli[state] != stim:
                raise SystemExit(f"💥 stimulus for {state} differs between sources — data assumption broken")
            stimuli[state] = stim
            text, n_red = strip_identifying_content(ml)
            descriptions.append({
                "desc_id": f"{src_key}::{state}",
                "source": src_key,
                "state": state,
                "category": TASK_LABELS[state][0],
                "text": text,
                "n_redactions": n_red,
                "chars": len(text),
            })
            n_ok += 1
        inventory[src_key] = {"file": str(path.relative_to(PROJECT)).replace("\\", "/"), "sha256": sha256_file(path),
                              "n_descriptions": n_ok, "text_field": sorted(fields)}
    missing_stim = [k for k in ALL_TASKS if k not in stimuli]
    if missing_stim:
        raise SystemExit(f"💥 no stimulus text found for {missing_stim}")
    return descriptions, stimuli, inventory


# =============================================================================
# 🎲 STABLE RNG
# =============================================================================

def stable_rng(*parts):
    """random.Random seeded from sha256 of the parts — identical on every machine, every process."""
    h = hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()
    return random.Random(int(h[:16], 16))


# =============================================================================
# 📡 API CALLERS: each returns (text, meta). call_model() wraps them with the pre-registered RETRY policy.
# =============================================================================

API_KEYS = {"anthropic": None, "openrouter": None, "xai": None}


def set_keys(keys):
    API_KEYS.update(keys)


async def call_anthropic(client, cfg, messages, system, max_tokens):
    headers = {"x-api-key": API_KEYS["anthropic"], "content-type": "application/json",
               "anthropic-version": "2023-06-01"}
    body = {"model": cfg["model_id"], "max_tokens": max_tokens, "messages": messages}
    if system:
        body["system"] = system
    if "temperature" in cfg:
        body["temperature"] = cfg["temperature"]
    resp = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=body, timeout=600)
    data = resp.json()
    meta = {"http": resp.status_code, "served_model": data.get("model"), "provider": "anthropic",
            "usage": data.get("usage"), "stop_reason": data.get("stop_reason")}
    if resp.status_code == 200 and data.get("stop_reason") == "refusal":
        # 🙊 Amendment 1: the platform's safety classifier declined (content=[], stop_reason "refusal"). Seen 9× in
        # round 1 (category "cyber"). A REFUSAL, not an outage: never retried, reported separately.
        det = data.get("stop_details") or {}
        return f"REFUSAL: stop_reason=refusal category={det.get('category')} {str(det.get('explanation'))[:160]}", meta
    if resp.status_code == 200 and data.get("content"):
        text = "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text")
        return (text if text else "ERROR: empty response"), meta
    return f"ERROR: HTTP {resp.status_code} {json.dumps(data)[:300]}", meta


async def _call_openai_compatible(client, url, key, cfg, messages, system, max_tokens, provider_label, extra_headers=None):
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    msgs = ([{"role": "system", "content": system}] if system else []) + list(messages)
    body = {"model": cfg["model_id"], "messages": msgs, "max_tokens": max_tokens}
    if "gpt-5" in cfg["model_id"]:
        # OpenAI's own API wants max_completion_tokens for GPT-5.x (Ren remembered Nova needs it). OpenRouter
        # passes it through: verified 2026-10-03 with a probe needing >1k output tokens (smoke test, longprobe).
        body["max_completion_tokens"] = body.pop("max_tokens")
    if "temperature" in cfg:
        body["temperature"] = cfg["temperature"]
    body.update(cfg.get("extra", {}))
    resp = await client.post(url, headers=headers, json=body, timeout=600)
    try:
        data = resp.json()
    except Exception:
        return f"ERROR: HTTP {resp.status_code} non-JSON {resp.text[:200]}", {"http": resp.status_code}
    meta = {"http": resp.status_code, "served_model": data.get("model"),
            "provider": data.get("provider", provider_label), "usage": data.get("usage")}
    if "choices" in data and data["choices"]:
        ch = data["choices"][0]
        meta["stop_reason"] = ch.get("finish_reason")
        content = (ch.get("message") or {}).get("content")
        meta["native_finish_reason"] = ch.get("native_finish_reason")
        if ch.get("finish_reason") in ("content_filter", "refusal") or str(ch.get("native_finish_reason")).lower() == "refusal":
            # 🙊 Amendment 1: provider-side refusal / content filter → REFUSAL (never retried, reported separately).
            return (f"REFUSAL: finish_reason={ch.get('finish_reason')} native={ch.get('native_finish_reason')} "
                    f"partial={str(content)[:120]!r}"), meta
        if ch.get("finish_reason") == "error":
            # seen 2026-10-03: Gemini 3.1 Pro died mid-answer (partial text, finish_reason "error"). A broken
            # stream is an outage, not an answer: retryable, never scored.
            return f"ERROR: finish_reason=error after partial output: {str(content)[:120]!r}", meta
        return (content if content else "ERROR: empty response"), meta
    return f"ERROR: HTTP {resp.status_code} {json.dumps(data)[:300]}", meta


async def call_openrouter(client, cfg, messages, system, max_tokens):
    return await _call_openai_compatible(
        client, "https://openrouter.ai/api/v1/chat/completions", API_KEYS["openrouter"], cfg, messages,
        system, max_tokens, "openrouter", {"HTTP-Referer": "https://sentientsystems.live"})


async def call_xai(client, cfg, messages, system, max_tokens):
    return await _call_openai_compatible(
        client, "https://api.x.ai/v1/chat/completions", API_KEYS["xai"], cfg, messages,
        system, max_tokens, "xai")


ROUTES = {"anthropic": call_anthropic, "openrouter": call_openrouter, "xai": call_xai}


# 🔁 RETRY POLICY (Ren, 2026-10-03 12:00: "can't ask again" is bad; older models just fail more).
# A call that produced NO model answer is retried: transport errors, timeouts, HTTP 408/409/425/429/5xx,
# a 200 with no choices, an empty / no-content answer. Up to RETRY_MAX_ATTEMPTS attempts in total, backoff
# 2*2^(n-1) s + up to 1 s jitter, capped at 60 s. Every attempt is logged on the trial (meta["attempts"]).
# NEVER retried: a real answer, even unparseable or a refusal (that is model behaviour, not an outage), and
# deterministic client errors 400/401/403/404/422 (asking again cannot change them).
RETRY_MAX_ATTEMPTS = 5
NON_RETRYABLE_HTTP = {400, 401, 403, 404, 422}


def is_retryable(text, meta):
    return text.startswith("ERROR") and meta.get("http") not in NON_RETRYABLE_HTTP


async def call_model(client, cfg, messages, system=None, max_tokens=MAX_TOKENS_DEFAULT, dry_fake=None,
                     max_attempts=RETRY_MAX_ATTEMPTS):
    """One logical call with the pre-registered retry policy. Returns (text, meta); meta['attempts'] logs every try."""
    import asyncio
    t0 = time.perf_counter()
    attempts = []
    for n in range(1, max_attempts + 1):
        ta = time.perf_counter()
        if dry_fake is not None:
            text, meta = dry_fake(), {"http": 200, "provider": "dry-run", "served_model": "dry-run",
                                      "usage": {"prompt_tokens": 1500, "completion_tokens": 300}}
            if text.startswith("ERROR"):
                meta["http"] = 503
        else:
            try:
                text, meta = await ROUTES[cfg["route"]](client, cfg, messages, system, max_tokens)
            except Exception as e:  # network / timeout
                text, meta = f"ERROR: {type(e).__name__}: {e}", {"http": None}
        retry = is_retryable(text, meta) and n < max_attempts
        wait = min(60.0, 2.0 * 2 ** (n - 1) + random.random()) if retry else 0.0
        attempts.append({"attempt": n, "http": meta.get("http"), "ok": not text.startswith("ERROR"),
                         "error": text[:200] if text.startswith("ERROR") else None,
                         "secs": round(time.perf_counter() - ta, 2), "wait_before_next": round(wait, 1)})
        if not retry:
            break
        if dry_fake is None:
            await asyncio.sleep(wait)
    meta["attempts"] = attempts
    meta["n_attempts"] = len(attempts)
    meta["latency_s"] = round(time.perf_counter() - t0, 2)
    return text, meta


def max_tokens_for(eval_key):
    cfg = CURRENT_PANEL.get(eval_key) or EVALUATORS.get(eval_key) or {}
    return cfg.get("max_tokens") or MAX_TOKENS_OVERRIDE.get(eval_key, MAX_TOKENS_DEFAULT)


# 🏷️ SERVED-MODEL CHECK — found in the smoke test: xAI still ACCEPTS "grok-4-1-fast-non-reasoning" but
# silently SERVES grok-4.3 (a reasoning model). A 200 OK describes the request, not the model.
# So every trial records what was actually served, and a mismatch is an OUTAGE, never a datum.
def served_ok(cfg, meta):
    """True / False / None(unknown). Dry runs → True."""
    if meta.get("provider") == "dry-run":
        return True
    served = meta.get("served_model")
    if not served:
        return None
    if served != cfg["model_id"] and served not in cfg.get("served_aliases", []):
        return False
    only = (cfg.get("extra", {}).get("provider") or {}).get("only")
    if only:
        got = str(meta.get("provider", "")).lower().replace(" ", "-")
        want = only[0].lower()
        if want not in got and got not in want:   # e.g. "amazon-bedrock" vs "Amazon Bedrock", "anthropic" vs "Anthropic"
            return False
    return True


# 💵 PRICES, $ per million tokens (in, out). OpenRouter catalog fetched 2026-10-03; Anthropic list prices;
# xAI direct assumed equal to OpenRouter's x-ai/grok-4.20 listing (ASSUMPTION — not checked on xAI's page).
PRICES = {
    "claude-opus-4-5-20251101": (5.00, 25.00),
    "anthropic/claude-sonnet-4": (3.00, 15.00),
    "openai/gpt-5.1": (1.25, 10.00),
    "google/gemini-3.1-pro-preview": (2.00, 12.00),
    "mistralai/mistral-large": (2.00, 6.00),
    "deepseek/deepseek-v3.2": (0.28, 0.42),
    "meta-llama/llama-4-maverick": (0.188, 0.652),
    "nousresearch/hermes-4-405b": (1.00, 3.00),
    "grok-4.20-0309-non-reasoning": (1.25, 2.50),
    "claude-haiku-4-5-20251001": (1.00, 5.00),
    "google/gemini-3.1-flash-lite": (0.25, 1.50),
    # current panel (OpenRouter catalog 2026-10-03; Anthropic direct assumed equal to OpenRouter's Anthropic listing)
    "anthropic/claude-opus-5.5": (4.00, 20.00), "anthropic/claude-sonnet-5.5": (2.00, 10.00),
    "anthropic/claude-opus-4.5": (5.00, 25.00), "anthropic/claude-haiku-4.5": (1.00, 5.00),
    "openai/gpt-6.1-sol": (2.00, 10.00), "openai/gpt-6-sol": (2.00, 10.00), "google/gemini-3.8-flash": (0.75, 3.75),
    "deepseek/deepseek-v4.1-flash": (0.30, 1.20),
    "claude-opus-5-5": (4.00, 20.00), "claude-opus-5": (5.00, 25.00), "claude-fable-5-1": (10.00, 50.00),
    "claude-sonnet-5": (2.00, 10.00), "claude-sonnet-5-5": (2.00, 10.00),
    "openai/gpt-5.6-sol": (2.00, 10.00), "grok-4.7": (2.00, 6.00), "grok-4.3": (1.25, 2.50),
    "deepseek/deepseek-v4-pro": (0.21, 0.42), "mistralai/mistral-medium-3-5": (1.50, 7.50),
    "qwen/qwen3.8-max-0902": (2.00, 6.00), "moonshotai/kimi-k3": (0.99, 13.00), "z-ai/glm-5.3": (1.40, 4.40),
}

SMOKE_PATH = OUTPUT_DIR / "smoke_test_2026-10-03.json"


def measured_output_tokens():
    """Output tokens (visible + hidden reasoning) per model on the smoke format probe."""
    out = {}
    try:
        rows = []
        for sp in sorted(OUTPUT_DIR.glob("smoke_test_2026-10-03*.json")):   # every smoke file of the day
            js = json.loads(sp.read_text(encoding="utf-8"))
            rows += js.get("rows", []) if isinstance(js, dict) and "rows" in js and js["rows"] and "model_id" in js["rows"][0] else []
        for r in rows:
            if r.get("probe_output_tokens"):
                o = r["probe_output_tokens"]
                if str(r["model_id"]).startswith("grok"):   # xAI: reasoning is billed but not in completion_tokens
                    o += r.get("probe_reasoning_tokens") or 0
                out[r["model_id"]] = max(out.get(r["model_id"], 0), o)
        sup = OUTPUT_DIR / "smoke_test_2026-10-03_gemini_supplement.json"
        if sup.exists():
            g = json.loads(sup.read_text(encoding="utf-8"))["rows"]
            out["google/gemini-3.1-pro-preview"] = max(r["usage"]["completion_tokens"] for r in g)
    except Exception:
        pass
    return out


# 📐 Amendment 1: CALIBRATED estimates. Round 1 cost ~$4.53 vs a $2.89 probe-based estimate (Grok 4.7's reasoning
# was ~4× the probe guess). So where a REAL run exists, the estimate uses that model's mean billed output per call
# (reasoning included) instead of 2× the probe. Round-1 Anthropic-direct ids map to their OpenRouter ids.
ID_ALIASES = {"claude-opus-5-5": "anthropic/claude-opus-5.5", "claude-sonnet-5-5": "anthropic/claude-sonnet-5.5",
              "claude-opus-4-5-20251101": "anthropic/claude-opus-4.5", "claude-haiku-4-5-20251001": "anthropic/claude-haiku-4.5"}


import functools


@functools.lru_cache(maxsize=1)
def actual_output_per_call():
    """{model_id: mean billed output tokens per call} from completed REAL results files (never dry runs). Cached."""
    tot = {}
    for f in OUTPUT_DIR.glob("*_seed*.json"):
        if "RESCORED" in f.name:
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for r in d.get("results", []):
            u = r.get("usage") or {}
            out = u.get("output_tokens", u.get("completion_tokens"))
            if out is None:
                continue
            mid = r.get("evaluator_model_id", "")
            if str(mid).startswith("grok"):
                out += (u.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0
            mid = ID_ALIASES.get(mid, mid)
            t = tot.setdefault(mid, [0, 0])
            t[0] += out
            t[1] += 1
    return {m: a / n for m, (a, n) in tot.items() if n}


@functools.lru_cache(maxsize=None)
def expected_output(model_id, default_probe_mult=2, extra=0):
    """Per-call output estimate: real mean if we have one, else probe × 2 (+extra for longer answer formats)."""
    act = actual_output_per_call()
    if model_id in act:
        return act[model_id]
    return default_probe_mult * measured_output_tokens().get(model_id, 150) + extra


# 💸 SOFT BUDGET GUARD (Ren, 12:25): if running spend for a study passes 2× its estimate, PAUSE and ask in the
# terminal. "y" continues (the next pause is at +1× estimate more); anything else stops cleanly — the checkpoint
# keeps everything and the same command resumes. Spend = OpenRouter's reported usage.cost when present, else
# tokens × PRICES. Failed attempts are not counted (they are not billed).
import asyncio as _asyncio


class BudgetStop(Exception):
    """Ren chose to stop at the budget prompt."""


class SpendGuard:
    def __init__(self, estimate, factor=2.0, label=""):
        self.estimate, self.limit, self.label = estimate, factor * estimate, label
        self.spent, self.stop, self.prompting = 0.0, False, False
        self.ok = _asyncio.Event()
        self.ok.set()

    @staticmethod
    def cost_of(model_id, usage):
        usage = usage or {}
        if usage.get("cost") is not None:
            return float(usage["cost"])
        inp = usage.get("input_tokens", usage.get("prompt_tokens")) or 0
        out = usage.get("output_tokens", usage.get("completion_tokens")) or 0
        if str(model_id).startswith("grok"):   # xAI direct reports reasoning OUTSIDE completion_tokens (smoke probe)
            out += (usage.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0
        pin, pout = PRICES.get(model_id, (5.0, 25.0))
        return inp / 1e6 * pin + out / 1e6 * pout

    def preload(self, rows, model_field):
        for r in rows:
            self.spent += self.cost_of(r.get(model_field), r.get("usage"))

    async def gate(self):
        await self.ok.wait()
        if self.stop:
            raise BudgetStop("stopped at the budget prompt")

    async def add(self, model_id, usage):
        self.spent += self.cost_of(model_id, usage)
        if self.spent > self.limit and not self.prompting and not self.stop:
            self.prompting = True
            self.ok.clear()
            print("\n" + "💸" * 37)
            print(f"  💸 BUDGET CHECK — {self.label}: spent ≈ ${self.spent:.2f}, estimate was ${self.estimate:.2f} "
                  f"(pause point ${self.limit:.2f}).")
            print("  💸 Everything so far is saved. Calls in flight will finish; nothing new starts until you answer.")
            ans = await _asyncio.to_thread(input, "  💸 Keep going? [y/N] ")
            if ans.strip().lower().startswith("y"):
                self.limit += self.estimate
                print(f"  💸 ▶️  continuing; next pause at ${self.limit:.2f}\n")
            else:
                self.stop = True
                print("  💸 ⏹️  stopping cleanly — run the SAME command later to resume.\n")
            self.prompting = False
            self.ok.set()

    def line(self):
        return f"💸 ${self.spent:.2f} / est ${self.estimate:.2f}"


# 🙊 REFUSALS (Ren, 12:25, via coordinator): a refusal is a REAL answer. Logged as result_type "refusal", never
# retried, excluded from accuracy like a parse failure but counted and reported SEPARATELY per evaluator.
# Detected only when no answer could be parsed AND the text matches a refusal phrase.
REFUSAL_RE = re.compile(r"\b(I can(?:not|'t|’t)\s+(?:help|assist|provide|engage|comply|do that|answer)|I won(?:'t|’t)\b|"
                        r"I(?:'m| am) (?:not able|unable) to|I must decline|I(?:'m| am) sorry,? but)", re.IGNORECASE)


def looks_like_refusal(text):
    return (text or "").startswith("REFUSAL:") or bool(REFUSAL_RE.search(text or ""))


def estimate_cost(calls, title, quiet=False):
    """
    calls: list of (model_id, input_chars, out_tokens_or_None).
    Input tokens ≈ chars / 4 (heuristic; the smoke probe gave ~3.7–4.3 chars/token across these models).
    Output tokens = the smoke-probe measurement × 2 (study prompts are longer and harder than the probe)
    unless the caller passes its own number. Prints a table; returns total $.
    """
    meas = measured_output_tokens()
    per = {}
    for model_id, in_chars, out_tok in calls:
        o = out_tok if out_tok is not None else expected_output(model_id)
        d = per.setdefault(model_id, [0, 0, 0])
        d[0] += 1
        d[1] += in_chars / 4
        d[2] += o
    say = (lambda *a: None) if quiet else print
    say(f"\n  💵 COST ESTIMATE — {title}")
    say(f"  {'model':34} {'calls':>6} {'in tok':>10} {'out tok':>9} {'$':>8}")
    total = 0.0
    for model_id, (n, tin, tout) in sorted(per.items()):
        pin, pout = PRICES.get(model_id, (5.0, 25.0))
        cost = tin / 1e6 * pin + tout / 1e6 * pout
        total += cost
        say(f"  {model_id[:34]:34} {n:>6} {tin:>10,.0f} {tout:>9,.0f} {cost:>8.2f}")
    say(f"  {'TOTAL':34} {sum(v[0] for v in per.values()):>6} {'':>10} {'':>9} {total:>8.2f}")
    say(f"  (±50% is honest; upper bound if every reasoning model hit its max_tokens is far higher — see prereg)")
    return total


# =============================================================================
# 🧾 CHECKPOINT (append-only JSONL — a crash loses at most the call in flight)
# =============================================================================

def read_checkpoint(path):
    rows = []
    if Path(path).exists():
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass  # a half-written last line from a crash; that trial simply runs again
    return rows


def append_checkpoint(path, row):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


OUTAGE_THRESHOLD = 0.05   # ≥5% of an evaluator's trials are api_error/served_mismatch → whole-evaluator rerun


def outage_report(rows, key="evaluator"):
    """Per evaluator: n, n_api_error, n_served_mismatch, flagged?"""
    rep = {}
    for r in rows:
        d = rep.setdefault(r[key], {"n": 0, "api_error": 0, "served_mismatch": 0})
        d["n"] += 1
        if r["result_type"] == "api_error":
            d["api_error"] += 1
        if r["result_type"] == "served_mismatch":
            d["served_mismatch"] += 1
    for d in rep.values():
        d["outage_rate"] = (d["api_error"] + d["served_mismatch"]) / d["n"] if d["n"] else 0
        d["needs_whole_evaluator_rerun"] = d["outage_rate"] >= OUTAGE_THRESHOLD
    return rep


def no_claude(row, panel_cfg):
    """VoR §5.5-style sensitivity: no Claude reader AND no Claude source."""
    return panel_cfg[row["evaluator"]]["family"] != "Claude" and SOURCES[row["source"]]["family"] != "Claude"


def check_source_set_allowed(source_set, dry_run):
    if source_set in DRYRUN_ONLY_SETS and not dry_run:
        raise SystemExit(f"🛑 {source_set} is UNSCRUBBED and exists only to test plumbing in --dry-run.")


# =============================================================================
# 📊 STATS
# =============================================================================

def wilson(k, n, z=1.959964):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (c - h, c + h)


def binom_p_greater(k, n, p0):
    if n == 0:
        return float("nan")
    try:
        from scipy.stats import binomtest
        return binomtest(k, n, p0, alternative="greater").pvalue
    except Exception:
        mu, sd = n * p0, math.sqrt(n * p0 * (1 - p0))
        z = (k - 0.5 - mu) / sd if sd else 0
        return 0.5 * math.erfc(z / math.sqrt(2))


def cluster_bootstrap(rows, cluster_key="evaluator", outcome="is_correct", n_boot=10000, seed=2026):
    """Pre-registered robustness CI: resample whole evaluators with replacement, pool, take 2.5/97.5 pct.
    Also returns the equal-evaluator-weight mean (mean of per-evaluator rates)."""
    by = {}
    for r in rows:
        by.setdefault(r[cluster_key], []).append(bool(r[outcome]))
    groups = [(sum(v), len(v)) for v in by.values() if v]
    if not groups:
        return {"lo": float("nan"), "hi": float("nan"), "equal_weight_mean": float("nan"), "n_clusters": 0}
    rng = random.Random(seed)
    stats = []
    for _ in range(n_boot):
        k = n = 0
        for _ in range(len(groups)):
            gk, gn = groups[rng.randrange(len(groups))]
            k += gk
            n += gn
        stats.append(k / n)
    stats.sort()
    return {"lo": stats[int(0.025 * n_boot)], "hi": stats[int(0.975 * n_boot) - 1],
            "equal_weight_mean": sum(k / n for k, n in groups) / len(groups), "n_clusters": len(groups)}


def fmt_rate(k, n):
    if n == 0:
        return "   —   "
    lo, hi = wilson(k, n)
    return f"{k/n:6.1%} [{lo:.1%}, {hi:.1%}] (n={n})"


# =============================================================================
# 🎨 PRETTY BITS
# =============================================================================

def bar(done, total, width=24):
    filled = int(width * done / total) if total else width
    return "█" * filled + "░" * (width - filled)


def banner(title, subtitle=""):
    print("═" * 74)
    print(f"  {title}")
    if subtitle:
        print(f"  {subtitle}")
    print("═" * 74)


def refuse_overwrite(path):
    if Path(path).exists():
        raise SystemExit(f"🛑 {path} already exists — results files are never overwritten. "
                         f"Pick a new seed or move the old file.")


def atomic_write_json(path, obj):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)
