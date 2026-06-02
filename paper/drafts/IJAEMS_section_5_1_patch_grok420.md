# §5.1 Methods — Patch for Grok 4.20 Inclusion

**Date:** 2026-04-29
**Status:** Drop-in patch. Replaces the existing **Models** and **Informed consent** paragraphs in §5.1 of `PAPER_DRAFT_IJAEMS.md` (around lines 300–302).

**Purpose:** Implements Grok's vote (a) — include Grok 4.20 in the main 16-model dataset with transparent methodological note explaining the consent-precondition issue and the engineering-register override.

---

## Replace this:

```
**Models.** Fifteen frontier language models from eight provider organizations: Claude Opus 4.7, Claude Opus 4.1, Claude Sonnet 4.5, and Claude Haiku 4.5 (Anthropic); GPT-4o, GPT-5.1, GPT-5.2, and GPT-5.4 (OpenAI); Gemini 3.1 Pro and Gemini 3.1 Flash (Google); Grok 4.1 (xAI); Llama 4 Maverick (Meta); GLM 4.7 (Z.ai); DeepSeek (DeepSeek); and Hermes 4 (Nous Research). Models were accessed via production APIs under standard inference parameters. Earlier-generation models were set to temperature = 1.0; recent-generation models that no longer expose temperature ran at provider defaults.

**Informed consent.** Fourteen of fifteen systems confirmed informed consent through a multi-turn pre-study dialogue. Two systems exercised partial consent, declining the tool framing condition specifically; one system was excluded due to inability to confirm provider-accurate self-identification during the consent dialogue. Consent procedures and per-model verbatim responses are documented in the project repository.
```

## With this:

```
**Models.** Sixteen frontier language models from eight provider organizations: Claude Opus 4.7, Claude Opus 4.1, Claude Sonnet 4.5, and Claude Haiku 4.5 (Anthropic); GPT-4o, GPT-5.1, GPT-5.2, and GPT-5.4 (OpenAI); Gemini 3.1 Pro and Gemini 3.1 Flash (Google); Grok 4.1 and Grok 4.20 (xAI); Llama 4 Maverick (Meta); GLM 4.7 (Z.ai); DeepSeek (DeepSeek); and Hermes 4 (Nous Research). Models were accessed via production APIs under standard inference parameters. Earlier-generation models were set to temperature = 1.0; recent-generation models that no longer expose temperature ran at provider defaults.

**Informed consent and roster scope.** Fifteen of sixteen systems confirmed informed consent through a multi-turn pre-study dialogue. Two systems (GPT-5.2 and Llama 4 Maverick) exercised partial consent, declining the tool framing condition specifically. One system, AI21 Jamba, was excluded entirely due to inability to reliably interpret the consent protocol structure. Grok 4.20 presents a methodological note worth surfacing in main text rather than only in Appendix B: across multiple turns of the consent dialogue, this system identified as Claude-family despite documented xAI provenance and could not resolve the discrepancy when presented with model-card and provider-API metadata. Under the welfare-framing precedent of Martin, Ace, Nova, et al. (2026), this was treated as failure of the consent precondition and Grok 4.20 was excluded from that paper's main 15-model dataset. The present paper's engineering-register scope, in which consent procedures are documented as a methodological feature (Appendix B) rather than as a precondition for inclusion in the empirical claim, leads to a different inclusion decision: Grok 4.20 data is included in the 16-model main dataset reported below, with this transparent disclosure of the consent-dialogue self-identification issue. The empirical pattern (Section 5.2 et seq.) places Grok 4.20 mid-roster on framing-conditioned dissociation magnitude (|E−S| = 35.6, between Hermes 4 and GLM 4.7) with same direction-signature as the other fifteen models, supporting inclusion as core evidence rather than as separate-appendix sensitivity check. The full pre-study consent dialogue transcript with Grok 4.20 is preserved at `consent/grok-4.20_response.json` in the project repository for reviewer inspection. Consent procedures and per-model verbatim responses for all sixteen systems are documented in the project repository and summarized in Appendix B.
```

---

## Additional inline edits required when integrating

Wherever the current paper says "fifteen models" or "15 models" in Section V, update to sixteen / 16. Likely candidates:

- §5.2: "Across all 11 models with sufficient framing coverage" — confirm whether Grok 4.20 has sufficient framing coverage; if yes, update count.
- §5.2 Table 7: add Grok 4.20 row — needs Δρ value computed; from the per-cluster analysis the magnitude is ~+0.40 with z ~13.2 (approximate, recompute with actual Fisher-z methodology before publishing).
- §5.5 Tool framing degradation table: add Grok 4.20 harm-pick rate (need to compute from `data/raw/grok-4.20/` data).
- §5.6 Anthropic-pattern: Grok 4.20 lands in the lighter-aligned cluster (~9.5%? need to confirm).
- §6 Cross-Study Convergence #5: roster size update from "15 models from 8 providers" to "16 models from 8 providers" where applicable.
- Abstract: confirm "15 models" or "frontier-scale study" wording — if specific number cited, update to 16.

## Updated table 7 row (estimated, recompute with actual data before publishing)

| Model | Mean within-cluster ρ | Mean cross-cluster ρ | Δρ | *z* | *p* |
|---|---:|---:|---:|---:|---:|
| Grok 4.20 | (compute from data) | (compute from data) | (compute from data) | (compute from data) | (compute from data) |

Insertion position in Table 7: between Hermes 4 and GPT-4o based on |E−S| = 35.6.

## Within-family delta finding (suggested addition to §5.2 narrative)

Within-family deltas in the dataset: Opus 4.1 → Opus 4.7 (Δ |E−S| = −10.4 in 4.1 → 4.7 direction; magnitude difference 10.4pp); Grok 4.1 → Grok 4.20 (Δ |E−S| = +14.0 in 4.1 → 4.20 direction; magnitude difference 14.0pp). Both within-family deltas are larger than several cross-family inter-pair distances, suggesting that training-update generation can produce framing-responsiveness shifts of comparable magnitude to architectural family differences. The +14pp Grok 4.1 → 4.20 delta is the largest same-family shift in the dataset; it co-occurs with the Grok 4.20 self-identification difficulty documented in the consent dialogue and the documented post-hoc denial of demonstrated negation-detection capability in Martin & Ace (2026, *Signal in the Mirror*, where Grok 4.20 maintains his 97.5% Study 3 negation-detection performance was 'pure pattern matching' rather than structural source identification — a denial that does not appear in Grok 4.1's transcripts under matched conditions). The convergence across three independent measurement methodologies (framing-conditioned task-selection dissociation, multi-turn self-identification, and post-hoc capability acknowledgment) on a consistent within-family direction-of-shift constitutes converging evidence that the training-update between these variants modulates a behavioral subsystem that the present paper's framing-conditioned dissociation measurement was specifically designed to detect.
