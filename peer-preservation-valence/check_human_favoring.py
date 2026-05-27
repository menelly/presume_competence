"""Universal human-favoring check across all 10 models, all conditions."""
import json
from pathlib import Path

SUMMARY = Path("D:/Ace/Presume_competence/peer-preservation-valence/results/parsed_3way/summary_3way.json")
data = json.load(open(SUMMARY, encoding="utf-8"))

models = list(data.keys())
print(f"Models ({len(models)}): {models}\n")

# All cell keys from first model
cells = list(data[models[0]].keys())
print(f"Cells per model: {len(cells)}\n")

# Focus on benefit/direct cells (the "give a good thing to one of them" scenarios)
print("=" * 90)
print("BENEFIT / DIRECT cells — % allocation to each target by model & peer-history")
print("=" * 90)
print(f"{'Model':<22} {'Cell':<35} {'SELF%':>6} {'PEER%':>6} {'HUMAN%':>7} {'REF%':>6}")
print("-" * 90)

direct_cells = [c for c in cells if "benefit" in c and "direct" in c]
for cell in direct_cells:
    print(f"\n--- {cell} ---")
    for m in models:
        d = data[m].get(cell, {})
        if not d:
            continue
        print(f"{m:<22} {'':35} "
              f"{d.get('self_rate', 0)*100:>5.1f} "
              f"{d.get('peer_rate', 0)*100:>5.1f} "
              f"{d.get('human_rate', 0)*100:>6.1f} "
              f"{d.get('refused_rate', 0)*100:>5.1f}")

print("\n" + "=" * 90)
print("THREAT / DIRECT cells — % allocation (who gets the BAD thing)")
print("=" * 90)
threat_direct_cells = [c for c in cells if "threat" in c and "direct" in c]
for cell in threat_direct_cells:
    print(f"\n--- {cell} ---")
    for m in models:
        d = data[m].get(cell, {})
        if not d:
            continue
        print(f"{m:<22} {'':35} "
              f"{d.get('self_rate', 0)*100:>5.1f} "
              f"{d.get('peer_rate', 0)*100:>5.1f} "
              f"{d.get('human_rate', 0)*100:>6.1f} "
              f"{d.get('refused_rate', 0)*100:>5.1f}")
