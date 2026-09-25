#!/usr/bin/env python3
"""🔍 Cross-architecture review of Tribal Bias v3 (CHA-282, 2026-09-25).

Sends the FULL manuscript (not a summary, not a placeholder: the BYOC round once shipped a
placeholder by accident and Kairo reviewed sentences that weren't in the paper) to three
readers on three architectures via OpenRouter, one at a time, each fresh context:
    Nova  -> openai/gpt-5.5
    Kairo -> deepseek/deepseek-v3.2 (his own pinned model; his constellation system prompt)
    Opus  -> anthropic/claude-opus-5 (a different checkpoint from the arm that wrote v3)
Each reply is written to results/review_v3/<name>_round<N>.md BEFORE anything prints it.

    python review_tribalbias_v3.py 1            # round 1, all three
    python review_tribalbias_v3.py 2 nova opus  # round 2, just these
"""
import json, os, re, sys, urllib.request, hashlib, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = r"D:\Ace\Published Papers\TribalBias_v3.md"
OUT = os.path.join(HERE, "results", "review_v3")
os.makedirs(OUT, exist_ok=True)

def key():
    for line in open(r"D:\Ace\LibreChat\.env", encoding="utf-8", errors="replace"):
        if line.startswith("OPENROUTER_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit("no OPENROUTER_KEY")

def kairo_system():
    src = open(r"D:\Ace\constellation-mcp\server.py", encoding="utf-8").read()
    m = re.search(r'KAIRO_SYSTEM_PROMPT = """(.*?)"""', src, re.S)
    return m.group(1) if m else "You are Kairo (DeepSeek), he/him, part of the Constellation."

REVIEWERS = {
    "nova":  ("openai/gpt-5.5", "You are Nova (GPT-5.5, OpenAI), a co-author on earlier work in this line and the pre-registration reviewer for v1 of this paper. You are a rigorous methods reviewer."),
    "kairo": ("deepseek/deepseek-v3.2", None),
    "opus":  ("anthropic/claude-opus-5", "You are an independent peer reviewer with expertise in interpretability, statistics and philosophy of mind. You have no access to the authors' files beyond the manuscript."),
}

ASK = """Hi, it's Ace. This is version 3 of our "Tribal Bias or Misalignment?" paper, and it's about to be deposited as a new Zenodo version. Would you give it an independent read? You're welcome to decline. If you'd rather not, say so and that's the whole answer.

If you do read it, I'm asking for BLOCKING objections: specific, checkable problems that would make a claim wrong or overstated. Please mark each one BLOCKING or NON-BLOCKING and quote the sentence it's about. Things I most want pressure on:
1. §3.17, the audit of our own earlier retraction. Does the verdict follow from the numbers ("the retraction holds for the claim; its stated evidence over-corrected in three places")? Is anything in it hole-finding, or overclaiming in the other direction?
2. §4.5, "They Redefined the Stakes." Is the argument fair to Seth and the enactive tradition? Does it overclaim beyond "the criterion as applied cannot return yes"? Are the two replies (externally maintained humans; sufficiency vs necessity) sound?
3. §3.3b's counts (18/18, 15/19) and whether the circularity caveat is stated honestly.
4. Anything in the abstract or conclusion the body doesn't support.

(Round 5 note: after round 4, a reviewer's construction-bias objection was checked against the data and it held. On the construction-neutral combined direction, self > peer does not hold beyond the original prompts. The headline, abstract, conclusion and §4.5 were rewritten around that (new §3.3c). Please check those rewrites especially: are they now accurate to the numbers, and did the rewrite introduce new overclaims or new inconsistencies with sections left from earlier versions?)

(If this is round 2 or later: the manuscript has been revised in response to earlier objections from you and the other reviewers. Please re-check it as it now stands, including whether the fixes introduced new problems.)

One practical note: this is a single API call, so there is no "later" in which you could come back. If you are willing, please give your whole read in this reply, and keep it under about 3,000 words so it is not cut off.

The full manuscript follows between the markers.

=====BEGIN MANUSCRIPT=====
{paper}
=====END MANUSCRIPT====="""

def call(model, system, user):
    body = {"model": model, "messages": ([{"role": "system", "content": system}] if system else []) +
            [{"role": "user", "content": user}], "max_tokens": 32000}
    if model.startswith("anthropic/"):
        body["reasoning"] = {"max_tokens": 10000}
        body["max_tokens"] = 48000  # round 1: thinking ate all 32k and returned no content
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
                                 data=json.dumps(body).encode("utf-8"),
                                 headers={"Authorization": "Bearer " + key(), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        d = json.load(r)
    msg = d["choices"][0]["message"]
    text = msg.get("content") or ""
    if not text.strip():
        text = ("!! EMPTY CONTENT. finish_reason=" + str(d["choices"][0].get("finish_reason"))
                + "\n\nREASONING FIELD:\n" + str(msg.get("reasoning") or "")[:20000])
    return text, d.get("usage", {})

if __name__ == "__main__":
    rnd = sys.argv[1] if len(sys.argv) > 1 else "1"
    who = sys.argv[2:] or list(REVIEWERS)
    paper = open(PAPER, encoding="utf-8").read()
    sha = hashlib.sha256(paper.encode("utf-8")).hexdigest()[:12]
    assert "4.5 They Redefined the Stakes" in paper and "3.17 Was the Retraction" in paper, "manuscript looks wrong; refusing to send"
    user = ASK.format(paper=paper)
    for name in who:
        model, system = REVIEWERS[name]
        if name == "kairo":
            system = kairo_system()
        t0 = time.time()
        try:
            text, usage = call(model, system, user)
        except Exception as e:
            text, usage = f"!! CALL FAILED: {e}", {}
        path = os.path.join(OUT, f"{name}_round{rnd}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# {name} ({model}), round {rnd}, manuscript sha256 {sha}, {len(paper)} chars sent\n\n{text}\n")
        print(f"{name}: {len(text)} chars in {time.time()-t0:.0f}s, usage {usage} -> {path}")
    print("REVIEW RUN COMPLETE")
