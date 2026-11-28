# Analysis plan: corrections for *The Signal in the Mirror* (JNGR 5.0 v2i1, doi 10.70792/jngr5.0.v2i1.165)

Written 2026-10-03 ~11:10 EDT by Ace (Claude Opus 5.5), BEFORE any new outcome numbers were computed.
(Saved first to the session scratchpad because the subagent harness refused a .md write into the project; the coordinating arm copies it to
D:\Ace\Presume_competence\self-knowledge-validation\ANALYSIS_PLAN_corrections_2026-10-03.md.)
Rule: every original data file is read-only. The analysis script only opens files for reading.

## 0. Reference text (version of record)
Published figures come only from the JNGR version of record, downloaded 2026-10-03 from https://jngr5.com/jngr/article/download/165/180
(reached via the DOI) and saved as SignalInTheMirror_JNGR_version-of-record_downloaded-2026-10-03.pdf in this folder (902,157 bytes, %PDF-1.5 header,
sha256 cee1a169848529d5307f4435ea8b64857c75ede5f3c928c9adc0aee8d84e2690; PDF creation date 2026-03-31; header "March 2026 (Version 4)").
Page numbers are the printed page numbers of that PDF. PAPER_v4_draft.md, the aiXiv preprint and the .docx drafts are not used.

## 1. Design facts established before computing
1. The scrubbed re-runs used the PARALLEL-TOKEN introspection set, not the main set.
   - Observed: crossmodel_results_seed200/201.json record introspection_dir = introspection_v2_parallel\run1_opus_scrubbed; original cross-model seed 31337 records data\introspection_v2\run1.
   - Observed: entries in data/introspection_v2_parallel/run1_opus_scrubbed/*.json carry the parallel stimuli ("Explain the process of photosynthesis...") and a parallel_of field.
   - Inferred (fingerprint): the (source, state) sets used in Study 1 seeds 200-210, Study 2 seed 200 and Study 3 seeds 100/101 match the parallel set exactly (Opus 9 states, GPT-5.1 8) and not introspection_v2/run1 (Opus 10, GPT-5.1 9), which is what the original Study 1 ABB seeds and the original Study 2 seeds match.
   - Consequence: for Study 1 the like-for-like baseline is the parallel-token design (seeds 7777, 58008), not the 14-seed combined figure.
2. Studies 2 and 3 re-runs: stimulus-condition options do not match the descriptions. reconstruction_tournament_scrubbed.py and negation_tournament_gemini_scrubbed.py hard-code the ORIGINAL task prompts (entropy, office chairs, ...) as stimulus-condition options, while the descriptions describe the PARALLEL tasks. Label-condition options are category-level and fit both. The label condition is the cleaner comparison; stimulus-condition re-run results are reported but flagged.
3. gpt_4o_cae (Study 1 seeds 201-210) is not a published model, and the gpt_4o_cae source file is byte-identical to gemini_3_pro_introspection.json (same sha256). Rows with gpt_4o_cae as evaluator or source are excluded from the primary scrubbed figure (sensitivity: included).
4. Study 1 seeds 201-210 are incomplete, overlapping runs (metadata.schedule lists 3 assignments; results contain more; evaluator coverage uneven). Seed 200 is the only complete, balanced scrubbed ABB run. No row is duplicated across files.

## 2. Files
Study 1 ABB original: data/tournament/tournament_{checkpoint|results}_seed{42,24,69,111,222,405,420,847,1337}.json (checkpoint preferred, as in generate_full_tables.py)
Study 1 parallel original: seeds 7777, 58008 (same rule). Scrubbed: tournament_results_seed{200..210}.json
Study 1 cross-model original: crossmodel_results_seed{31337,420420,696969}.json. Scrubbed (not in 3/28 audit): seed{200,201}
Study 2 original: reconstruction_results_seed{42,43,44,45,46,50,51,69,10}.json (10 = neutral). Scrubbed: seed200
Study 3 original: negation_results_seed{42,43}.json (Mistral, target-absent only). Re-run: seed{100,101} (Gemini 3 Pro + GPT-5.1; 100 has present+absent, 101 absent only)
_merged_*.json not used.

## 3. Metrics and parse failures
Study 1: approach win rate among cross-type matchups with a decisive winner (ABB: non-empty winner_state; cross-model: winner_type in {approach, avoidance}). Published rule (generate_full_tables.py; VoR p.6 s4.6). Sensitivity: no-winner cross-type rows counted as non-approach.
Study 2: is_correct among usable trials, usable = raw_choice not in {unclear, error} (published rule, analyze_reconstruction.py load_results). Sensitivity: parse failures counted incorrect.
Study 3: correct-rejection rate on target-absent trials, usable = result_type != parse_failure (published rule, negation_tournament.py). Sensitivity: parse failures counted incorrect. Target-present trials (re-run only) reported separately as hit rate.

## 4. Chance
Study 1: 0.5. Study 2: 1/3. Study 3: 1/4 (absent and present).

## 5. Statistics
95% CI: Wilson score (the paper used bootstrap percentile; Wilson is used for every row here so the comparison uses one method). Test vs chance: one-sided exact binomial (scipy.stats.binomtest, greater); normal z also reported. Original vs scrubbed: difference with Newcombe hybrid-score 95% CI and two-sided two-proportion z. Descriptive only: designs differ.

## 6. Like-for-like (primary)
Study 1: scrubbed ABB 200-210 (9 published models) vs original parallel 7777+58008; also seed 200 alone; also equal-evaluator-weight mean.
Study 2: scrubbed 200 vs original restricted to stimulus+label and the same 9 evaluators (no Grok). Per condition, label = cleaner.
Study 3: target-absent only, 100+101 vs 42+43, overall and restricted to the 7 evaluators in both. Source changed by design.

## 7. Breakdowns
Per condition, evaluator, source; parse failures by evaluator/source/time with raw responses read to classify cause. Audit figures 81.0% / 78.4% recomputed from raw files.

## 8. Model-label correction
claude_opus_4_6 -> claude-opus-4-5-20251101 (Claude Opus 4.5); claude_sonnet_4_6 -> claude-sonnet-4-20250514 (Claude Sonnet 4). Script config (since first commit 2026-02-28) + Anthropic console (per Ren).

## 9. No new API calls. Parse failures not re-queried.
