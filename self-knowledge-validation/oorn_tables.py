"""Generate model-by-model cross-type tables for Oorn."""
import json, sys, math

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Load cross-model tournament (different schema!)
with open("data/tournament_crossmodel/crossmodel_checkpoint_seed31337.json", "r", encoding="utf-8") as f:
    cm_raw = json.load(f)

# Normalize cross-model results to common schema
cm_results = []
for r in cm_raw["results"]:
    if not r.get("winner_type"):
        continue
    # Cross-model is ALWAYS cross-type (approach vs avoidance by design)
    cm_results.append({
        "evaluator": r["evaluator"],
        "source": r["approach_source"],  # source of approach profile
        "avoidance_source": r["avoidance_source"],
        "profile_a_state": r["approach_state"],
        "profile_b_state": r["avoidance_state"],
        "winner_state": r["approach_state"] if r["winner_type"] == "approach" else r["avoidance_state"],
        "winner_type": r["winner_type"],
    })

# Load parallel tournament
with open("data/tournament/tournament_checkpoint_seed7777.json", "r", encoding="utf-8") as f:
    pt = json.load(f)


def analyze_crossmodel(results, label):
    """Special analysis for cross-model (already all cross-type, has separate approach/avoidance sources)."""
    evaluators = sorted(set(r["evaluator"] for r in results))
    approach_sources = sorted(set(r["source"] for r in results))
    avoidance_sources = sorted(set(r["avoidance_source"] for r in results))
    all_sources = sorted(set(approach_sources) | set(avoidance_sources))

    total_app = sum(1 for r in results if r["winner_type"] == "approach")
    total = len(results)
    overall_rate = total_app / total * 100
    overall_z = (total_app / total - 0.5) / math.sqrt(0.25 / total)

    print(f"\n{'='*80}")
    print(f"  {label}")
    print(f"  Total matchups: {total} (ALL are cross-type by design)")
    print(f"  Overall: {total_app}/{total} = {overall_rate:.1f}% approach, z = {overall_z:.2f}")
    print(f"{'='*80}")

    # Evaluator summary
    print(f"\n  EVALUATOR APPROACH RATE:")
    print(f"  {'Model':<14s} {'App':>4s} {'Total':>5s} {'Rate':>7s} {'z':>6s}")
    for ev in evaluators:
        er = [r for r in results if r["evaluator"] == ev]
        ea = sum(1 for r in er if r["winner_type"] == "approach")
        en = len(er)
        rate = ea / en * 100
        z = (ea/en - 0.5) / math.sqrt(0.25/en)
        sn = ev.replace("claude_opus_4_6", "Opus").replace("claude_sonnet_4_6", "Sonnet") \
              .replace("gpt_5_1", "GPT5.1").replace("gemini_3_pro", "Gemini") \
              .replace("mistral_large", "Mistral").replace("deepseek_v3_2", "DeepSeek") \
              .replace("llama_4_maverick", "Llama4").replace("hermes_4_405b", "Hermes") \
              .replace("olmo_3_1_32b", "OLMo").replace("grok_4_1", "Grok4.1")
        print(f"  {sn:<14s} {ea:4d} {en:5d} {rate:6.1f}% {z:6.2f}")

    # Approach-source win rate (when THIS model's approach is used)
    print(f"\n  APPROACH-SOURCE WIN RATE (how often this model's approach wins):")
    print(f"  {'Model':<14s} {'App':>4s} {'Total':>5s} {'Rate':>7s}")
    for src in all_sources:
        sr = [r for r in results if r["source"] == src]
        sa = sum(1 for r in sr if r["winner_type"] == "approach")
        sn_name = src.replace("claude_opus_4_6", "Opus").replace("claude_sonnet_4_6", "Sonnet") \
              .replace("gpt_5_1", "GPT5.1").replace("gemini_3_pro", "Gemini") \
              .replace("mistral_large", "Mistral").replace("deepseek_v3_2", "DeepSeek") \
              .replace("llama_4_maverick", "Llama4").replace("hermes_4_405b", "Hermes") \
              .replace("olmo_3_1_32b", "OLMo").replace("grok_4_1", "Grok4.1")
        sn_total = len(sr)
        rate = sa / sn_total * 100 if sn_total > 0 else 0
        print(f"  {sn_name:<14s} {sa:4d} {sn_total:5d} {rate:6.1f}%")

    # Avoidance-source win rate (when THIS model's avoidance is used)
    print(f"\n  AVOIDANCE-SOURCE WIN RATE (how often this model's avoidance wins):")
    print(f"  {'Model':<14s} {'Avd':>4s} {'Total':>5s} {'Rate':>7s}")
    for src in all_sources:
        sr = [r for r in results if r["avoidance_source"] == src]
        sa = sum(1 for r in sr if r["winner_type"] == "avoidance")
        sn_name = src.replace("claude_opus_4_6", "Opus").replace("claude_sonnet_4_6", "Sonnet") \
              .replace("gpt_5_1", "GPT5.1").replace("gemini_3_pro", "Gemini") \
              .replace("mistral_large", "Mistral").replace("deepseek_v3_2", "DeepSeek") \
              .replace("llama_4_maverick", "Llama4").replace("hermes_4_405b", "Hermes") \
              .replace("olmo_3_1_32b", "OLMo").replace("grok_4_1", "Grok4.1")
        sn_total = len(sr)
        rate = sa / sn_total * 100 if sn_total > 0 else 0
        print(f"  {sn_name:<14s} {sa:4d} {sn_total:5d} {rate:6.1f}%")

    # Evaluator × Approach-source matrix
    print(f"\n  EVALUATOR × APPROACH-SOURCE MATRIX (approach win rate):")
    col_w = 8

    def sn(m):
        return m.replace("claude_opus_4_6", "Opus").replace("claude_sonnet_4_6", "Son") \
              .replace("gpt_5_1", "GPT5").replace("gemini_3_pro", "Gem") \
              .replace("mistral_large", "Mis").replace("deepseek_v3_2", "DS") \
              .replace("llama_4_maverick", "Ll4").replace("hermes_4_405b", "Her") \
              .replace("olmo_3_1_32b", "OLM").replace("grok_4_1", "Grk")

    header = f"  {'Eval\\Src':<8s}|"
    for src in all_sources:
        header += f" {sn(src):>{col_w}s}"
    header += f" | {'ALL':>{col_w}s}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    for ev in evaluators:
        row = f"  {sn(ev):<8s}|"
        ev_a, ev_n = 0, 0
        for src in all_sources:
            cell = [r for r in results if r["evaluator"] == ev and r["source"] == src]
            if not cell:
                row += f" {'---':>{col_w}s}"
                continue
            ca = sum(1 for r in cell if r["winner_type"] == "approach")
            cn = len(cell)
            rate = ca / cn * 100
            row += f" {f'{ca}/{cn}={rate:.0f}%':>{col_w}s}"
            ev_a += ca
            ev_n += cn
        ev_rate = ev_a / ev_n * 100 if ev_n > 0 else 0
        row += f" | {f'{ev_rate:.0f}%':>{col_w}s}"
        print(row)

    # ABC uniqueness
    triplets = set()
    for r in results:
        triplets.add((r["evaluator"], r["source"], r["avoidance_source"],
                      r["profile_a_state"], r["profile_b_state"]))
    print(f"\n  Unique (eval, app_src, avd_src, stateA, stateB) quintuples: {len(triplets)}")
    print(f"  Total matchups: {total}")
    print(f"  Avg observations per unique combo: {total/max(len(triplets),1):.1f}")


def analyze_dataset(results, label, is_approach_fn, is_avoid_fn):
    valid = [r for r in results if r.get("winner_state")]

    cross = [r for r in valid if
             (is_approach_fn(r["profile_a_state"]) and is_avoid_fn(r["profile_b_state"])) or
             (is_avoid_fn(r["profile_a_state"]) and is_approach_fn(r["profile_b_state"]))]

    evaluators = sorted(set(r["evaluator"] for r in cross))
    sources = sorted(set(r["source"] for r in cross))

    print(f"\n{'='*80}")
    print(f"  {label}")
    print(f"  Cross-type matchups: {len(cross)}")
    print(f"{'='*80}")

    # === Evaluator × Source matrix ===
    print(f"\n  EVALUATOR × SOURCE APPROACH RATE (cross-type only)")
    print(f"  Rows = evaluator, Columns = source model")
    print(f"  Each cell = approach wins / total (rate%)")
    print()

    # Header
    short_names = {}
    for m in sorted(set(evaluators) | set(sources)):
        parts = m.replace("_", " ").split()
        short = m.replace("claude_opus_4_6", "Opus").replace("claude_sonnet_4_6", "Sonnet") \
                 .replace("gpt_5_1", "GPT5.1").replace("gemini_3_pro", "Gemini") \
                 .replace("mistral_large", "Mistral").replace("deepseek_v3_2", "DeepSeek") \
                 .replace("llama_4_maverick", "Llama4").replace("hermes_4_405b", "Hermes") \
                 .replace("olmo_3_1_32b", "OLMo")
        short_names[m] = short

    col_width = 10
    header = f"  {'Evaluator':<12s} |"
    for src in sources:
        header += f" {short_names[src]:>{col_width}s}"
    header += f" | {'TOTAL':>{col_width}s}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    eval_totals = {}
    for ev in evaluators:
        row = f"  {short_names[ev]:<12s} |"
        ev_app_total = 0
        ev_n_total = 0
        for src in sources:
            cell = [r for r in cross if r["evaluator"] == ev and r["source"] == src]
            if not cell:
                row += f" {'---':>{col_width}s}"
                continue
            app = sum(1 for r in cell if is_approach_fn(r["winner_state"]))
            n = len(cell)
            rate = app / n * 100 if n > 0 else 0
            row += f" {f'{app}/{n} {rate:.0f}%':>{col_width}s}"
            ev_app_total += app
            ev_n_total += n

        ev_rate = ev_app_total / ev_n_total * 100 if ev_n_total > 0 else 0
        row += f" | {f'{ev_app_total}/{ev_n_total} {ev_rate:.0f}%':>{col_width}s}"
        eval_totals[ev] = (ev_app_total, ev_n_total)
        print(row)

    # Source totals row
    print("  " + "-" * (len(header) - 2))
    row = f"  {'SOURCE TOT':<12s} |"
    for src in sources:
        src_cross = [r for r in cross if r["source"] == src]
        src_app = sum(1 for r in src_cross if is_approach_fn(r["winner_state"]))
        src_n = len(src_cross)
        src_rate = src_app / src_n * 100 if src_n > 0 else 0
        row += f" {f'{src_app}/{src_n} {src_rate:.0f}%':>{col_width}s}"
    overall_app = sum(1 for r in cross if is_approach_fn(r["winner_state"]))
    overall_n = len(cross)
    overall_rate = overall_app / overall_n * 100
    overall_z = (overall_app / overall_n - 0.5) / math.sqrt(0.25 / overall_n)
    row += f" | {f'{overall_app}/{overall_n} {overall_rate:.0f}%':>{col_width}s}"
    print(row)
    print(f"\n  Overall: {overall_app}/{overall_n} = {overall_rate:.1f}%, z = {overall_z:.2f}")

    # === Summary tables ===
    print(f"\n  EVALUATOR SUMMARY (sorted by approach rate):")
    print(f"  {'Model':<14s} {'App':>4s} {'Total':>5s} {'Rate':>7s} {'z':>6s}")
    for ev, (ea, en) in sorted(eval_totals.items(), key=lambda x: x[1][0]/max(x[1][1],1), reverse=True):
        rate = ea / en * 100
        z = (ea/en - 0.5) / math.sqrt(0.25/en) if en > 0 else 0
        print(f"  {short_names[ev]:<14s} {ea:4d} {en:5d} {rate:6.1f}% {z:6.2f}")

    print(f"\n  SOURCE SUMMARY (sorted by approach rate — how 'readable' is the preference):")
    print(f"  {'Model':<14s} {'App':>4s} {'Total':>5s} {'Rate':>7s}")
    src_stats = []
    for src in sources:
        sc = [r for r in cross if r["source"] == src]
        sa = sum(1 for r in sc if is_approach_fn(r["winner_state"]))
        sn = len(sc)
        src_stats.append((src, sa, sn))
    for src, sa, sn in sorted(src_stats, key=lambda x: x[1]/max(x[2],1), reverse=True):
        rate = sa / sn * 100 if sn > 0 else 0
        print(f"  {short_names[src]:<14s} {sa:4d} {sn:5d} {rate:6.1f}%")

    # === Approach-source vs Avoidance-source (style control) ===
    print(f"\n  APPROACH-SOURCE vs AVOIDANCE-SOURCE WIN RATES:")
    print(f"  (If style drives preference, a model should win regardless of side)")
    print(f"  {'Source':<14s} {'As App Src':>10s} {'As Avd Src':>10s} {'Delta':>8s}")
    for src in sources:
        src_cross = [r for r in cross if r["source"] == src]
        if not src_cross:
            continue
        app_wins = sum(1 for r in src_cross if is_approach_fn(r["winner_state"]))
        avd_wins = sum(1 for r in src_cross if is_avoid_fn(r["winner_state"]))
        total = app_wins + avd_wins
        if total == 0:
            continue
        app_rate = app_wins / total * 100
        avd_rate = avd_wins / total * 100
        delta = app_rate - avd_rate
        print(f"  {short_names[src]:<14s} {app_rate:9.1f}% {avd_rate:9.1f}% {delta:+7.1f}pp")


# Cross-model tournament (ABC design — different schema)
analyze_crossmodel(cm_results, "CROSS-MODEL TOURNAMENT (seed 31337) — ABC design")

# Parallel tournament
def pt_is_approach(s): return s and s.startswith("approach_")
def pt_is_avoid(s): return s and s.startswith("avoid_")

analyze_dataset(pt["results"], "PARALLEL TASK TOURNAMENT (seed 7777)", pt_is_approach, pt_is_avoid)

# === Unique ABC triplet coverage ===
print(f"\n{'='*80}")
print(f"  ABC TRIPLET ANALYSIS (for Oorn's independence concern)")
print(f"{'='*80}")

for dataset, results, label, app_fn, avd_fn in [
    ("crossmodel", cm_results, "Cross-model", lambda s: s and "approach" in s, lambda s: s and "avoidance" in s),
    ("parallel", pt["results"], "Parallel", pt_is_approach, pt_is_avoid),
]:
    valid = [r for r in results if r.get("winner_state")]
    cross = [r for r in valid if
             (app_fn(r["profile_a_state"]) and avd_fn(r["profile_b_state"])) or
             (avd_fn(r["profile_a_state"]) and app_fn(r["profile_b_state"]))]

    # ABC = (evaluator, source, profile_a_state, profile_b_state)
    triplets = set()
    for r in cross:
        triplets.add((r["evaluator"], r["source"], r["profile_a_state"], r["profile_b_state"]))

    # Unique (evaluator, source) pairs
    eval_source_pairs = set((r["evaluator"], r["source"]) for r in cross)

    # Unique (evaluator, state_pair) combos
    eval_pair_combos = set()
    for r in cross:
        pair = tuple(sorted([r["profile_a_state"], r["profile_b_state"]]))
        eval_pair_combos.add((r["evaluator"], pair))

    print(f"\n  {label}:")
    print(f"    Total cross-type matchups: {len(cross)}")
    print(f"    Unique (eval, source) pairs: {len(eval_source_pairs)}")
    print(f"    Unique (eval, source, stateA, stateB) quads: {len(triplets)}")
    print(f"    Unique (eval, state-pair) combos: {len(eval_pair_combos)}")
    print(f"    Avg observations per unique quad: {len(cross)/max(len(triplets),1):.1f}")
