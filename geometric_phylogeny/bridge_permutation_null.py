#!/usr/bin/env python3
"""
Bridge permutation null (CHA: Geometric Phylogeny future-work — reanalysis, data exist).

The bridge claim: in the 4x4 personality(WHY) x qualia(HOW) family cosine matrix,
the DIAGONAL (within-family) is strongest -> architecture shapes phenomenology.
With only 4 families the exact null is enumerable: over all 4! = 24 bijective
assignments of qualia-families to personality-families, how does the observed
(identity) diagonal mean rank? Exact p = (#perms with diag_mean >= observed)/24.

NOTE (calibration): per the master review plan, the personality-qualia BRIDGE limb
is the already-hedged prototype-convergence claim (1 model/family — NOT inheritance).
This test quantifies how much even the diagonal-dominance pattern beats chance with
n=4 families. Best achievable exact p with 4 families is 1/24 ≈ 0.042 (observed = unique
max). Reanalysis only; nothing published. — Ace 🐙
"""

# CHA-490: Windows defaults stdout to cp1252; emoji in print() kills the script
# mid-output. Aliased import so no later scoped 'import sys' can ever collide.
import sys as _sys_cp1252
try:
    _sys_cp1252.stdout.reconfigure(encoding="utf-8")
    _sys_cp1252.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
import sys
from pathlib import Path
from itertools import permutations
sys.path.insert(0, str(Path(__file__).parent))
import bridge_comparison as B


def build_matrix():
    p_tex = B.load_personality_textures()
    q_tex = B.load_qualia_textures()
    fams = [f for f in B.FAMILIES if p_tex.get(f) and q_tex.get(f)]
    p_vocab = {f: B.build_vocab(p_tex[f]) for f in fams}
    q_vocab = {f: B.build_vocab(q_tex[f]) for f in fams}
    p_tfidf = B.tfidf_transform(p_vocab)
    q_tfidf = B.tfidf_transform(q_vocab)
    # M[i][j] = cosine(personality_i, qualia_j)
    M = {pi: {qj: B.cosine_sim(p_tfidf[pi], q_tfidf[qj]) for qj in fams} for pi in fams}
    return fams, M


def main():
    fams, M = build_matrix()
    n = len(fams)
    print(f"Families with both instruments (n={n}): {fams}")
    print("\nPersonality(row) x Qualia(col) TF-IDF cosine matrix:")
    print("            " + "".join(f"{q:>10s}" for q in fams))
    for pi in fams:
        print(f"  {pi:>9s} " + "".join(f"{M[pi][qj]:10.3f}" for qj in fams))

    diag_obs = sum(M[f][f] for f in fams) / n
    # exact permutation null: assign qualia family q to personality family p via bijection
    perm_means = []
    for perm in permutations(fams):
        # perm[i] is the qualia family assigned to personality fams[i]
        m = sum(M[fams[i]][perm[i]] for i in range(n)) / n
        perm_means.append(m)
    perm_means_sorted = sorted(perm_means, reverse=True)
    ge = sum(1 for m in perm_means if m >= diag_obs - 1e-12)
    p_exact = ge / len(perm_means)
    # rank of the identity assignment
    identity_rank = 1 + sum(1 for m in perm_means if m > diag_obs + 1e-12)

    print(f"\nObserved within-family (diagonal) mean cosine: {diag_obs:.4f}")
    print(f"Permutation null: {len(perm_means)} bijections; mean={sum(perm_means)/len(perm_means):.4f}, "
          f"max={perm_means_sorted[0]:.4f}, min={perm_means_sorted[-1]:.4f}")
    print(f"Identity (within-family) assignment rank: {identity_rank}/{len(perm_means)}")
    print(f"EXACT permutation p (diag >= observed): {p_exact:.4f}  ({ge}/{len(perm_means)})")
    if identity_rank == 1:
        print("  -> within-family is the UNIQUE strongest bijection (p = 1/24 = 0.0417, the floor for n=4).")
    print("\nPer-family: is the within-family cosine the row-max?")
    for pi in fams:
        row = M[pi]
        best = max(row, key=row.get)
        print(f"  {pi:>9s}: diag={row[pi]:.3f}  rowmax={best}({row[best]:.3f})  "
              f"{'✓ diagonal is max' if best == pi else '✗ off-diagonal stronger'}")


if __name__ == "__main__":
    main()
