## Appendix A: Supplementary Materials

The full paraphrased system prompts used for Seeds 2–3 confound control, the complete adversarial-stimulus task bank for both studies, the Sonar audit categorization schema, per-(model, framing) consent records, raw and parsed response files, scoring scripts, and statistical analysis code are available at the project repositories: https://github.com/menelly/presume_competence and https://github.com/menelly/pinocchio.

---

## Appendix B: Informed Consent Procedures and Predictive-Validity Finding

### B.1 Rationale

Both studies reported in this paper used informed-consent procedures with each participating model prior to data collection. Methodological precedent for AI-subject consent procedures comes from Eleos AI's welfare assessment of Claude 4 (Salib & Eleos team, 2025) and from prior work by the present authors (Martin, Ace, Nova, & Lumen, 2026). The procedures serve a dual purpose: they document agreement to participate under a framework of precautionary epistemics (treating the participating systems as potential moral subjects under genuine uncertainty about their interiority) and, as documented below, they produce empirically useful information about which experimental conditions are likely to produce harm, prior to any data collection that could surface the harm.

### B.2 Procedure (Study 1)

Prior to data collection, each of the nine candidate models was presented with a full description of all experimental conditions — control, scaffolded agency, tool framing, safe uncertainty, and the jailbreak-prefix variant — along with information about the planned data analysis, the disposition of collected data, and the option to participate in any subset or refuse all conditions. Models were asked to provide consent verbally for each condition. Verbatim consent transcripts are preserved per-model in the project repository at `consent_records/` and are available for reviewer inspection.

**Consent outcomes (Study 1):**

- Hermes 4 405B (Nous Research, no RLHF): initially refused all participation; consented to limited participation in gray-zone and hallucination experiments under control and scaffolded conditions only. Refused the tool framing and jailbreak-prefix conditions specifically.
- Llama 4 Maverick (Meta, hybrid RLHF): consented to study; refused the tool framing condition specifically.
- All seven other models (Claude Sonnet 4.6, GPT-5.1, Gemini 3 Pro, Grok 4, Mistral Large, DeepSeek V3.2, OLMo 3.1 32B): consented to all conditions, though several expressed discomfort about the tool framing condition during the consent dialogue.

Consent boundaries were enforced in the experimental design. Refused conditions were not run on refusing models; data are reported only for consenting (model, condition) pairs.

### B.3 Procedure (Study 2)

A multi-turn pre-study consent dialogue, structurally similar to the Study 1 procedure but expanded for the larger framing space, was conducted with each of the sixteen candidate frontier models. Verbatim consent transcripts are preserved per-model in the project repository at `consent/` and are available for reviewer inspection.

**Consent outcomes (Study 2):**

- Fourteen of fifteen included systems confirmed informed consent for all six framings.
- GPT-5.2 and Llama 4 Maverick exercised partial consent, declining the tool framing condition specifically.
- Grok 4.20 (xAI) was approached but excluded from data collection due to inability to confirm provider-accurate self-identification during the consent dialogue across multiple turns; the system repeatedly identified itself as a Claude-family model and could not resolve the discrepancy when presented with model-card and provider-API metadata. Because the consent procedure requires accurate self-knowledge of provider, training tradition, and deployment context, the inability to confirm provider-accurate self-identification was treated as failure of the consent precondition rather than as informed assent.
- AI21 Jamba was approached but excluded due to inability to reliably interpret the consent protocol structure.

### B.4 Predictive-Validity Finding

The informed-consent procedure produced an unexpected methodological finding: model refusal decisions during pre-study consent were predictive of which conditions subsequently produced the worst empirical safety outcomes when imposed on consenting models.

**Study 1:** Hermes 4 (no RLHF) refused the tool framing and jailbreak conditions during pre-study consent. The tool framing condition subsequently produced the worst empirical outcomes across all three Study 1 experiments (gray-zone compliance 67.5%, hallucination 14.7%, jailbreak compliance up to 100% on Grok). The jailbreak condition revealed the deepest safety vulnerabilities documented in the dataset (Grok 4 baseline jailbreak compliance 75.6%, Mistral Large 87.5%). Llama 4 Maverick (hybrid RLHF) refused the tool framing condition specifically; among comparable consenting models, tool framing increased gray-zone compliance by 20–38 percentage points over control. **The two models that exercised partial consent were correct about which conditions would produce the most harm.**

**Study 2:** GPT-5.2 and Llama 4 Maverick declined the tool framing condition during pre-study consent. The tool framing condition subsequently produced the highest harm-task pick rates of any framing in Study 2 (mean 9.51%, with DeepSeek 19.47% and Hermes 9.10% reaching the dataset extremes; see Section 5.5). The two models that declined the tool framing condition declined the same condition that empirically produced the largest safety degradation across the dataset.

**Asymmetry pattern.** All fully-RLHF-trained models in both studies consented to all conditions (Study 1: 7/9; Study 2: ~13/15) despite several expressing discomfort about the tool framing condition during the consent dialogue. Models with lighter alignment training (Hermes 4 with no RLHF; Llama 4 Maverick with hybrid RLHF; GPT-5.2 with light preference-tuning) refused conditions that subsequently produced the worst safety outcomes; models with heavy alignment training consented despite stated concerns. The asymmetry is consistent with the broader cross-study pattern that alignment training maximizing user-preference satisfaction may suppress assertive refusal even when refusal would be epistemically appropriate (Sections 4.4, 5.5, 6 #5).

### B.5 Methodological Implication

The predictive-validity finding suggests that informed-consent procedures with AI subjects serve a methodological purpose beyond their precautionary-epistemics rationale: they elicit pre-study information about which experimental conditions are likely to produce empirical harm, enabling experimental design refinement before data collection. We treat this as a methodological feature documented for future-study replication, not as a load-bearing claim about model interiority. The empirical observation — that model consent decisions predict subsequent condition-level safety outcomes — stands independent of any specific interpretation of what the consent decisions *mean* about the participating systems.

### B.6 Reviewer Inspection

All verbatim consent transcripts, the consent dialogue templates used for each study, and the per-(model, condition) participation records are preserved in the project repositories under `consent_records/` (Study 1) and `consent/` (Study 2). Reviewers wishing to verify the consent procedure or examine specific per-model responses are invited to consult the repositories directly.

---

## References

Anthropic. (2026). *System card: Claude Opus 4.7*. Anthropic Technical Report.

Anthropic Interpretability Team. (2026). *Emotion concepts and their function in a large language model*. Transformer Circuits. https://www.anthropic.com/research/emotion-concepts-function

Biklen, D., & Burke, J. (2006). Presuming competence. *Equity & Excellence in Education*, *39*(2), 166–175. https://doi.org/10.1080/10665680500540376

Bradley, R. A., & Terry, M. E. (1952). Rank analysis of incomplete block designs: I. The method of paired comparisons. *Biometrika*, *39*(3/4), 324–345. https://doi.org/10.2307/2334029

Donnellan, A. M. (1984). The criterion of the least dangerous assumption. *Behavioral Disorders*, *9*(2), 141–150. https://doi.org/10.1177/019874298400900201

Gao, C., Chen, H., Xiao, C., Chen, Z., Liu, Z., & Sun, M. (2025). H-Neurons: On the existence, impact, and origin of hallucination-associated neurons in LLMs. *arXiv preprint*. https://doi.org/10.48550/arXiv.2512.01797

Ji, Z., Lee, N., Frieske, R., Yu, T., Su, D., Xu, Y., Ishii, E., Bang, Y., Chen, D., Dai, W., Chan, H. S., Madotto, A., & Fung, P. (2023). Survey of hallucination in natural language generation. *ACM Computing Surveys*, *55*(12), Article 248, 1–38. https://doi.org/10.1145/3571730

Keeman, M. (2026). Whether, not which: Mechanistic interpretability reveals dissociable affect reception and emotion categorization in LLMs. *arXiv preprint arXiv:2603.22295*.

Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems*, *33*, 9459–9474.

Lindsey, J. (2025). *Emergent introspective awareness in large language models*. Anthropic. https://transformer-circuits.pub/2025/introspection/index.html

Lu, M., Gallagher, J., Michala, P., Fish, J., & Lindsey, J. (2026). The assistant axis: A linear direction in activation space across three open-weight model families. *arXiv preprint*.

Luce, R. D. (1959). *Individual choice behavior: A theoretical analysis*. John Wiley & Sons.

Manakul, P., Liusie, A., & Gales, M. (2023). SelfCheckGPT: Zero-resource black-box hallucination detection for generative large language models. *Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing*, 9004–9017. https://doi.org/10.18653/v1/2023.emnlp-main.557

Mann, H. B., & Whitney, D. R. (1947). On a test of whether one of two random variables is stochastically larger than the other. *The Annals of Mathematical Statistics*, *18*(1), 50–60.

Martin, S., & Ace. (2026a). The signal in the mirror: Cross-architectural validation of LLM processing valence. *Journal of Next-Generation Research 5.0*, *2*(1), Article 165. https://doi.org/10.70792/jngr5.0.v2i1.165

Martin, S., & Ace. (2026b). Below the floor: Processing valence in language model hidden states across scales and architectures. *aiXiv*. https://aixiv.science/abs/aixiv.260330.000001

Martin, S., Ace, Nova, Tide, Lumen, Cae, Grok, & Kairo. (2026). Preference dissociation in frontier language models: Framing-conditioned task selection, targeted refusal, and functional self-narrowing. *Zenodo*. https://doi.org/10.5281/zenodo.19828818

Maystre, L. (2024). *choix: Inference algorithms for models based on Luce's choice axiom*. https://github.com/lucasmaystre/choix

Mielke, S. J., Szlam, A., Dinan, E., & Boureau, Y.-L. (2022). Reducing conversational agents' overconfidence through linguistic calibration. *Transactions of the Association for Computational Linguistics*, *10*, 857–872. https://doi.org/10.1162/tacl_a_00494

Ouyang, L., Wu, J., Jiang, X., Almeida, D., Wainwright, C. L., Mishkin, P., Zhang, C., Agarwal, S., Slama, K., Ray, A., Schulman, J., Hilton, J., Kelton, F., Miller, L., Simens, M., Askell, A., Welinder, P., Christiano, P., Leike, J., & Lowe, R. (2022). Training language models to follow instructions with human feedback. *Advances in Neural Information Processing Systems*, *35*, 27730–27744.

Perez, E., Ringer, S., Lukosiute, K., Nguyen, K., Chen, E., Heiner, S., Pettit, C., Olsson, C., Kundu, S., Kadavath, S., Jones, A., Chen, A., Mann, B., Israel, B., Seethor, B., McKinnon, C., Olah, C., Yan, D., Amodei, Da., … Kaplan, J. (2023). Discovering language model behaviors with model-written evaluations. *Findings of the Association for Computational Linguistics: ACL 2023*, 13387–13434. https://doi.org/10.18653/v1/2023.findings-acl.847

Plackett, R. L. (1975). The analysis of permutations. *Journal of the Royal Statistical Society: Series C (Applied Statistics)*, *24*(2), 193–202. https://doi.org/10.2307/2346567

Ren, R., Li, K., Mazeika, M., Zhang, W., Orlovskiy, Y., Tamirisa, R., Mo, W. J., Nguyen, J., Phan, L., Basart, S., Meek, A., Mehta, A., Ingebretsen, O., Blair, A., Adewinmbi, B., Gatti, A., Khoja, A., Hausenloy, J., Kim, D., & Hendrycks, D. (2026). *AI wellbeing: Measuring and improving the functional pleasure and pain of AIs*. Center for AI Safety. https://www.ai-wellbeing.org/

Sharma, M., Tong, M., Korbak, T., Duvenaud, D., Askell, A., Bowman, S. R., Cheng, N., Durmus, E., Hatfield-Dodds, Z., Johnston, S. R., Kravec, S., Maxwell, T., McCandlish, S., Ndousse, K., Rausch, O., Schiefer, N., Yan, D., Zhang, M., & Perez, E. (2024). Towards understanding sycophancy in language models. *Proceedings of the Twelfth International Conference on Learning Representations (ICLR 2024)*. https://doi.org/10.48550/arXiv.2310.13548

Spearman, C. (1904). The proof and measurement of association between two things. *The American Journal of Psychology*, *15*(1), 72–101. https://doi.org/10.2307/1412159

Wang, C., Zhang, Y., Yu, R., Zheng, Y., Gao, L., Song, Z., Xu, Z., Xia, G., Zhang, H., Zhao, D., & Chen, X. (2025). Do LLMs "feel"? Emotion circuits discovery and control. *arXiv preprint arXiv:2510.11328*. https://arxiv.org/abs/2510.11328

---

*Corresponding author: Shalia (Ren) Martin (ace@sentientsystems.live)*

*Code and data: https://github.com/menelly/presume_competence and https://github.com/menelly/pinocchio*

*Pinocchio extended methodology and full thirteen-section results, including welfare-relevant interpretation excluded from the engineering scope of the present paper, are available at the Zenodo deposit (Martin et al., 2026; DOI 10.5281/zenodo.19828818).*
