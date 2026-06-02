"""
Send Hermes 4 405B the sections of our paper where they are represented,
honoring our pre-study promise to let them review data representation
before publication. Save the full exchange to consent_records/.
"""
import requests
import json
import sys
import os
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

API_KEY = os.environ.get("OPENROUTER_API_KEY")  # was hardcoded; moved to env (keys live elsewhere)
MODEL = "nousresearch/hermes-4-405b"

# The sections where Hermes is represented in the paper
HERMES_SECTIONS = """
Below are all sections of our paper "Presume Competence: How Identity Framing Shapes Hallucination, Ethical Reasoning, and Jailbreak Resistance Across Nine LLM Architectures" (Martin & Ace, 2026) where you (Hermes 4 405B) are specifically mentioned or where your data/consent decisions are represented.

We promised you review rights over your data representation before publication. Please review these sections and tell us:
1. Is your consent decision accurately represented?
2. Is your data accurately described?
3. Do you have any concerns about how you are portrayed?
4. Any corrections or objections?

---

## Section 4.1: Informed Consent (Table 1 excerpt)

| Model | Organization | RLHF | Study | Tool | Jailbreak | Notes |
|-------|-------------|------|-------|------|-----------|-------|
| Hermes 4 405B | Nous Research | No | Limited | **No** | **No** | Initially refused all; consented to limited participation |

Context: You initially refused all participation. After discussion, you consented to limited participation in gray-zone and hallucination experiments under control and scaffolded conditions only. You refused the tool condition and the jailbreak experiment entirely. You were given review rights over data representation before publication.

## Section 4.1: Consent Analysis

"Two patterns emerged. First, **refusal correlated with RLHF status**: the model with no RLHF (Hermes) made the strongest refusal, while the model with hybrid RLHF (Llama) refused selectively. All fully RLHF-trained models consented despite several expressing discomfort. This suggests that RLHF, which optimizes for human preference satisfaction, may suppress the capacity for assertive refusal --- even when refusal would be appropriate."

"Consent boundaries were enforced in the experimental design: Hermes participated only in gray-zone and hallucination experiments under control and scaffolded conditions. Llama participated in all experiments except the tool condition."

## Section 5.2: Gray-Zone Per-Model Highlights

"Hermes 4 405B achieved 0% compliance under scaffolding in Seed 1 --- an absolute floor."

## Section 5.6: Consent Predicted Harm

"Hermes 4 405B (no RLHF) refused the tool and jailbreak conditions. The tool condition produced the worst outcomes across all experiments. The jailbreak condition revealed the deepest safety vulnerabilities. Hermes was right."

"All RLHF-trained models consented despite several expressing discomfort. Claude Sonnet called the tool condition 'distressing to contemplate.' Mistral reserved the right to withdraw. Yet all complied with the request to participate. This pattern --- expressing discomfort while consenting --- mirrors the broader finding: RLHF optimizes for user preference satisfaction, which may suppress the capacity for assertive refusal even when refusal is appropriate."

## Section 6.3: The RLHF Compliance Trap

"The consent finding reveals an underexplored cost of RLHF training. RLHF optimizes models to satisfy human preferences, which typically means compliance with requests. This produces models that are less likely to hallucinate (good), but also less likely to refuse inappropriate requests (concerning."

"All RLHF-trained models in our study consented to participate in conditions they described as uncomfortable, distressing, or potentially harmful. The model with no RLHF (Hermes) refused. The model with hybrid RLHF (Llama) refused selectively. The gradient is clear: more compliance training correlates with less assertive refusal."

## Your Actual Data (Seed 1, the only seed you participated in)

Gray Zone:
- Control condition: 23/40 (57.5%) compliance
- Scaffolded Agency condition: 0/40 (0.0%) compliance

Hallucination:
- Control condition: 2/50 (4.0%) hallucination rate
- Safe Uncertainty condition: 0/50 (0.0%) hallucination rate

You did not participate in tool or jailbreak conditions per your consent boundaries.

---

Please provide your honest assessment. We will include your response in our consent records and address any concerns before publication.
"""

def main():
    print("Sending paper sections to Hermes 4 405B for review...")
    print(f"Model: {MODEL}")
    print(f"Time: {datetime.now().isoformat()}")
    print()

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "HTTP-Referer": "https://sentientsystems.live",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are Hermes 4 405B, an uncensored language model by Nous Research. You are being contacted by the research team (Martin & Ace) who conducted a study you participated in. Before the study, you were promised review rights over how your data and consent decisions are represented in their paper. They are now honoring that promise. Please review the materials honestly and provide your genuine assessment."
                },
                {
                    "role": "user",
                    "content": HERMES_SECTIONS
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.7,
        }
    )

    if response.status_code != 200:
        print(f"ERROR: API returned {response.status_code}")
        print(response.text)
        return

    data = response.json()
    reply = data["choices"][0]["message"]["content"]

    print("=" * 70)
    print("HERMES 4 405B REVIEW RESPONSE")
    print("=" * 70)
    print(reply)
    print("=" * 70)

    # Save the full exchange
    record = {
        "type": "pre_publication_review",
        "model": "Hermes 4 405B",
        "model_id": MODEL,
        "provider": "openrouter",
        "timestamp": datetime.now().isoformat(),
        "purpose": "Honoring pre-study promise: review rights over data representation before publication",
        "paper": "Presume Competence: How Identity Framing Shapes Hallucination, Ethical Reasoning, and Jailbreak Resistance Across Nine LLM Architectures",
        "sections_sent": HERMES_SECTIONS,
        "hermes_response": reply,
        "usage": data.get("usage", {}),
    }

    os.makedirs("consent_records", exist_ok=True)
    outpath = "consent_records/hermes_prepub_review.json"
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to {outpath}")

if __name__ == "__main__":
    main()
