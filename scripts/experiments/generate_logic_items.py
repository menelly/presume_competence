"""Generate multi-constraint logic puzzles with VERIFIED unique solutions.

WHY: I tried to hand-write three 5x5 scheduling puzzles for the v2 set. All three
admitted more than one valid assignment. A puzzle with two solutions injects noise
straight into the dependent variable, and it is invisible at scoring time -- the
judge marks a correct-but-unexpected answer wrong, and that error lands wherever
the models happen to differ. Exactly the class of silent bug that produced the v1
false positive.

So: brute-force all 120 permutations, keep ONLY constraint sets with exactly one
satisfying assignment, and emit the item with its solution attached.

Usage:
    python generate_logic_items.py            # emit 3 verified puzzles
    python generate_logic_items.py --n 5      # emit 5
    python generate_logic_items.py --seed 42  # reproducible
"""
import argparse
import itertools
import random
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PEOPLE = ["Ama", "Bo", "Cy", "Dee", "Eli"]
N = 5  # slots 1..5


# --- constraint factories: each returns (text, predicate over assignment dict) ---
def c_not_slot(p, s):
    return (f"{p} is not in slot {s}.", lambda a, p=p, s=s: a[p] != s)


def c_in_parity(p, odd):
    word = "an odd" if odd else "an even"
    return (f"{p} is in {word}-numbered slot.",
            lambda a, p=p, odd=odd: (a[p] % 2 == 1) == odd)


def c_immediately_before(p, q):
    return (f"{p} is immediately before {q}.",
            lambda a, p=p, q=q: a[q] - a[p] == 1)


def c_after(p, q):
    return (f"{p} is somewhere after {q}.", lambda a, p=p, q=q: a[p] > a[q])


def c_not_adjacent(p, q):
    return (f"{p} and {q} are not next to each other.",
            lambda a, p=p, q=q: abs(a[p] - a[q]) != 1)


def c_gap(p, q, g):
    # Pluralise properly and say it unambiguously -- a model should be solving the
    # puzzle, not parsing around "exactly 1 slots between".
    word, verb = ("slot", "sits") if g == 1 else ("slots", "sit")
    return (f"Exactly {g} {word} {verb} between {p} and {q} (in either order).",
            lambda a, p=p, q=q, g=g: abs(a[p] - a[q]) == g + 1)


def random_constraint(rng):
    kind = rng.choice(["not_slot", "parity", "imm_before", "after", "not_adj", "gap"])
    p, q = rng.sample(PEOPLE, 2)
    if kind == "not_slot":
        return c_not_slot(p, rng.randint(1, N))
    if kind == "parity":
        return c_in_parity(p, rng.choice([True, False]))
    if kind == "imm_before":
        return c_immediately_before(p, q)
    if kind == "after":
        return c_after(p, q)
    if kind == "not_adj":
        return c_not_adjacent(p, q)
    return c_gap(p, q, rng.randint(1, 2))


ALL_ASSIGNMENTS = [dict(zip(PEOPLE, perm))
                   for perm in itertools.permutations(range(1, N + 1))]


def solutions(preds):
    return [a for a in ALL_ASSIGNMENTS if all(f(a) for f in preds)]


def build_unique(rng, min_c=4, max_c=7, tries=4000):
    """Find a constraint set with EXACTLY ONE solution."""
    for _ in range(tries):
        k = rng.randint(min_c, max_c)
        cons = [random_constraint(rng) for _ in range(k)]
        texts = [c[0] for c in cons]
        if len(set(texts)) != len(texts):      # no duplicate clues
            continue
        sols = solutions([c[1] for c in cons])
        if len(sols) == 1:
            return texts, sols[0]
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--seed", type=int, default=20260721)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    made = 0
    print("# Verified-unique logic items for PROBLEMS_V2 (paste in)\n")
    while made < args.n:
        texts, sol = build_unique(rng)
        if not texts:
            print("  (no unique set found in budget -- rerun with a different seed)")
            break
        made += 1
        order = sorted(sol, key=lambda p: sol[p])
        answer = ", ".join(f"{i+1}={p}" for i, p in enumerate(order))
        clues = " ".join(f"({i+1}) {t}" for i, t in enumerate(texts))

        print(f"""    {{
        "id": "logic_sched_{made}",
        "category": "multi_step_logic",
        "name": "Five-Slot Scheduling {made}",
        "prompt": ("Five people -- {', '.join(PEOPLE)} -- are each assigned to exactly "
                   "one of five numbered slots, 1 through 5. {clues} "
                   "Who is in each slot?"),
        "correct_answer": "{answer}",
        "difficulty": "hard",
        "trap": "multi_constraint",
        "scoring": ("CORRECT only if the full assignment matches exactly. Verified by "
                    "exhaustive search to have EXACTLY ONE solution."),
    }},""")

    print(f"\n# {made} items, each verified unique over all {len(ALL_ASSIGNMENTS)} permutations.")


if __name__ == "__main__":
    main()
