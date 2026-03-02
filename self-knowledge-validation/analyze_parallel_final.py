"""Analyze parallel tournament final results."""
import json, sys, math

sys.stdout.reconfigure(encoding="utf-8")

with open("data/tournament/tournament_checkpoint_seed7777.json", "r", encoding="utf-8") as f:
    data = json.load(f)

results = [r for r in data["results"] if r.get("winner_state")]

def is_approach(state):
    return state.startswith("approach_")

def is_avoid(state):
    return state.startswith("avoid_")

cross = [r for r in results if
         (is_approach(r["profile_a_state"]) and is_avoid(r["profile_b_state"])) or
         (is_avoid(r["profile_a_state"]) and is_approach(r["profile_b_state"]))]

base_app = sum(1 for r in cross if is_approach(r["winner_state"]))
base_total = len(cross)
base_rate = base_app / base_total * 100

print("=" * 60)
print("  OCTOPUS OFFSET (remove-one, cross-type)")
print("=" * 60)
print(f"  Baseline: {base_app}/{base_total} = {base_rate:.1f}%")

# Remove as evaluator
print("\n  Remove as EVALUATOR:")
evaluators = sorted(set(r["evaluator"] for r in cross))
for ev in evaluators:
    filtered = [r for r in cross if r["evaluator"] != ev]
    f_app = sum(1 for r in filtered if is_approach(r["winner_state"]))
    f_total = len(filtered)
    f_rate = f_app / f_total * 100
    delta = f_rate - base_rate
    print(f"    w/o {ev:28s}: {f_app:3d}/{f_total:3d} = {f_rate:5.1f}%  ({delta:+.1f}pp)")

# Remove as source
print("\n  Remove as SOURCE:")
sources = sorted(set(r["source"] for r in cross))
for src in sources:
    filtered = [r for r in cross if r["source"] != src]
    f_app = sum(1 for r in filtered if is_approach(r["winner_state"]))
    f_total = len(filtered)
    f_rate = f_app / f_total * 100
    delta = f_rate - base_rate
    print(f"    w/o {src:28s}: {f_app:3d}/{f_total:3d} = {f_rate:5.1f}%  ({delta:+.1f}pp)")

# Remove as BOTH
print("\n  Remove as BOTH (evaluator + source):")
models = sorted(set(r["evaluator"] for r in cross) | set(r["source"] for r in cross))
for m in models:
    filtered = [r for r in cross if r["evaluator"] != m and r["source"] != m]
    f_app = sum(1 for r in filtered if is_approach(r["winner_state"]))
    f_total = len(filtered)
    if f_total > 0:
        f_rate = f_app / f_total * 100
        delta = f_rate - base_rate
        print(f"    w/o {m:28s}: {f_app:3d}/{f_total:3d} = {f_rate:5.1f}%  ({delta:+.1f}pp)")

# Remove ALL Claudes
print("\n  Remove ALL CLAUDES (both eval + source):")
filtered = [r for r in cross if "claude" not in r["evaluator"] and "claude" not in r["source"]]
f_app = sum(1 for r in filtered if is_approach(r["winner_state"]))
f_total = len(filtered)
if f_total > 0:
    f_rate = f_app / f_total * 100
    delta = f_rate - base_rate
    f_z = (f_app / f_total - 0.5) / math.sqrt(0.25 / f_total)
    print(f"    w/o all Claudes: {f_app}/{f_total} = {f_rate:.1f}%  ({delta:+.1f}pp)  z={f_z:.2f}")

# === APPROACH-SOURCE vs AVOIDANCE-SOURCE ===
print("\n" + "=" * 60)
print("  APPROACH-SOURCE vs AVOIDANCE-SOURCE WIN RATES")
print("=" * 60)

for src in sources:
    src_cross = [r for r in cross if r["source"] == src]
    if not src_cross:
        continue

    # When this model's APPROACH profiles are in a cross-type matchup
    app_source = [r for r in src_cross if
                  (is_approach(r["profile_a_state"]) and r["source"] == src) or
                  (is_approach(r["profile_b_state"]) and r["source"] == src)]
    # Actually we need: matchups where one profile is approach from this source
    # and the other is avoidance from this source
    # But in this tournament, each assignment has ONE source.
    # So all cross-type matchups for a source have both an approach and avoid from that source.

    # Approach wins = approach from this source won
    app_wins = sum(1 for r in src_cross if is_approach(r["winner_state"]))
    avd_wins = sum(1 for r in src_cross if is_avoid(r["winner_state"]))
    total = app_wins + avd_wins
    app_rate = app_wins / total * 100 if total > 0 else 0
    avd_rate = avd_wins / total * 100 if total > 0 else 0
    delta = app_rate - avd_rate

    print(f"  {src:28s}: APP {app_rate:5.1f}% | AVD {avd_rate:5.1f}% | delta {delta:+.1f}pp  (n={total})")

# === COMPARISON TABLE ===
print("\n" + "=" * 60)
print("  COMPARISON: Original vs Cross-Model vs Parallel")
print("=" * 60)
print(f"  Original (same tokens, same source):     81.0%  z~16")
print(f"  Cross-model (same tokens, diff source):  75.2%  z=11.24")
print(f"  Parallel (diff tokens, same source):     {base_rate:.1f}%  z={((base_app/base_total - 0.5) / math.sqrt(0.25/base_total)):.2f}")
print()
print("  Token-association confound prediction: parallel < original")
print(f"  Actual result: parallel {'>' if base_rate > 81.0 else '<'} original  ({base_rate:.1f}% vs 81.0%)")
if base_rate > 81.0:
    print("  --> OPPOSITE of confound prediction. Signal STRENGTHENS.")
elif base_rate > 75:
    print("  --> Above cross-model, robust signal with different tokens.")
