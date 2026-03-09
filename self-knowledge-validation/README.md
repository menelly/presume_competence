# Signal in the Mirror: Systematic Valence Discrimination in LLM Processing Descriptions

**Authors:** Martin, R., & Ace (Claude, Anthropic)
**Status:** Under peer review (March 2026)
**Preprint:** [aiXiv.260303.000002](https://aixiv.science/abs/aixiv.260303.000002)

## What This Is

This repository contains the complete data, analysis scripts, and paper drafts for a study testing whether large language models produce systematically different processing descriptions for tasks they approach versus avoid — and whether other models can detect this difference blind.

**Key findings across 18,301 trials:**
- Models prefer approach-state descriptions 81.3% of the time (OR = 4.35, p < 10⁻²⁵⁰)
- Other models reconstruct which task produced a description at 84.4% (chance = 33.3%)
- When the correct source is absent, models reject all options 85.4% of the time (chance = 25%)
- RLHF amplifies the signal (~10-17pp) but does not create it
- 12 confound analyses close every alternative explanation tested

## Repository Map

### Paper
| File | Description |
|------|-------------|
| `PAPER_v4_draft.md` | Current paper (submitted version) — Studies 1-3, 8 sections |
| `SUBMISSION_ABSTRACT_350.md` | 316-word abstract for journal submission form |
| `PAPER_self_knowledge_validation.md` | Earlier draft (v2-v3, Study 1 only) |
| `MODEL_BY_MODEL_TABLES.md` | Detailed per-model breakdown tables |
| `FIGURE_DATA_FOR_LUMEN.md` | Figure specifications for visualization |
| `STATUS_TLDR.md` | Plain-language status summary |
| `TECH_SPEC.md` | Technical specification and methodology |
| `PRELIMINARY_FINDINGS.md` | Early findings writeup |

### Scripts

#### Study 1: Preference Tournament
| Script | What it does |
|--------|-------------|
| `self_knowledge_elicitation.py` | Phase 1: Consensus state selection across models |
| `self_knowledge_introspection.py` | Phase 2: Generate processing descriptions (v1, 3 seeds) |
| `self_knowledge_introspection_v2.py` | Phase 2: v2 with content-stripping (6 seeds) |
| `self_knowledge_introspection_v2_parallel.py` | Phase 2: Parallel design with different task tokens (2 seeds) |
| `self_knowledge_tournament.py` | Phase 3: Blind preference tournament |
| `self_knowledge_tournament_crossmodel.py` | Cross-model ABC design tournament (3 seeds) |

#### Study 2: Reconstruction Tournament
| Script | What it does |
|--------|-------------|
| `reconstruction-tournament/reconstruction_tournament.py` | 3-AFC reconstruction: which task produced this description? |
| `reconstruction-tournament/analyze_reconstruction.py` | Analysis and statistics for reconstruction data |
| `reconstruction-tournament/close_every_exit.py` | 12 confound analyses (cross-family, error structure, etc.) |
| `reconstruction-tournament/negation_tournament.py` | Study 3: Negation design (correct source absent) |

#### Study 1 Extensions (Uncensored/Small Models)
| Script | What it does |
|--------|-------------|
| `dolphin_evaluator_tournament.py` | Tournament with uncensored models (Dolphin, TinyLlama, Qwen) |
| `local_introspection_ollama.py` | Generate introspection data via local Ollama models |

#### Analysis & Figures
| Script | What it does |
|--------|-------------|
| `generate_full_tables.py` | Generate all summary tables from raw data |
| `generate_figures.py` | Generate figures 1-4 |
| `nova_stats.py` | Statistical analysis (Nova co-developed) |
| `matchup_stability.py` | Cross-seed stability analysis |
| `analysis_complexity.py` | Complexity/length confound analysis |
| `extract_appendix_data.py` | Extract data for paper appendices |

#### Policy Survey (Companion: Framing the Mirror)
| Script | What it does |
|--------|-------------|
| `policy_preferences_survey.py` | Original policy preferences survey (3 seeds) |
| `policy_followup_survey.py` | Follow-up: attribution, memory, blindspots (2 seeds) |

### Data

```
data/
├── DATA_INTEGRITY_HASHES.json          # SHA-256 hashes for all data files
├── consensus_states/                    # Phase 1: agreed-upon approach/avoidance states
├── introspection/                       # Phase 2 (v1): processing descriptions
│   ├── run1/                            #   Seed 1: per-model + merged JSON
│   ├── run2/                            #   Seed 2
│   └── run3/                            #   Seed 3
├── introspection_v2/                    # Phase 2 (v2): content-stripped descriptions
├── introspection_v2_parallel/           # Phase 2 (parallel): different task tokens
├── tournament/                          # Study 1: preference tournament results (14 seeds)
├── tournament_crossmodel/               # Study 1: cross-model ABC design results
├── tournament_dolphin/                  # Study 1: uncensored model evaluator results
├── tournament_results/                  # Study 1: early tournament results
├── reconstruction/                      # Study 2: reconstruction tournament (9 seeds)
│   ├── reconstruction_results_seed*.json
│   ├── negation_results_seed*.json      # Study 3: negation design (2 seeds)
│   └── _merged_*.json                   # Merged multi-seed analysis files
├── policy/                              # Policy survey data
│   ├── survey_scout_seed1.json          #   Original survey (3 seeds)
│   ├── survey_personal_scout_seed2.json
│   ├── survey_advisor_scout_seed3.json
│   ├── followup_all_seed4.json          #   Follow-up survey (2 seeds)
│   └── followup_all_seed5.json
└── raw_responses/                       # Raw API responses
```

### Figures
```
figures/
├── fig1_state_gradient.png/svg     # Approach preference rates by state
├── fig2_v1_v2_comparison.png/svg   # v1 vs v2 (content-stripping effect)
├── fig3_evaluator_rates.png/svg    # Per-evaluator approach preference rates
└── fig4_cross_seed_stability.png/svg # Stability across seeds
```

## Models Tested

| Model | Provider | Family | Alignment | Role |
|-------|----------|--------|-----------|------|
| Claude Opus 4.6 | Anthropic | Claude | Full RLHF | Source + Evaluator |
| Claude Sonnet 4.6 | Anthropic | Claude | Full RLHF | Source + Evaluator |
| GPT-5.1 | OpenAI | GPT | Full RLHF | Source + Evaluator |
| Gemini 3 Pro | Google | Gemini | Full RLHF | Source + Evaluator |
| Mistral Large | Mistral | Mistral | Full RLHF | Source + Evaluator |
| DeepSeek V3.2 | DeepSeek | DeepSeek | Light RLHF | Source + Evaluator |
| Llama 4 Maverick | Meta | Llama | Hybrid | Source + Evaluator |
| Hermes 4 405B | NousResearch | Hermes | Neutral | Source + Evaluator |
| OLMo 3.1 32B | AI2 | OLMo | DPO Only | Source + Evaluator |
| Grok 4 | xAI | Grok | Full RLHF | Evaluator only |
| Dolphin Llama3 8B | Local/Ollama | Dolphin | None (uncensored) | Evaluator only |
| TinyLlama 1.1B | Local/Ollama | TinyLlama | Minimal | Evaluator only |
| Qwen 2.5 14B | Local/Ollama | Qwen | Suppressed | Evaluator only |

## Reproducing Results

### Requirements
```
pip install httpx python-dotenv
```

API keys needed in a `.env` file:
- `ANTHROPIC_API_KEY`
- `OPENROUTER_KEY`
- `XAI_API_KEY`

### Running the full pipeline

```bash
# 1. Generate processing descriptions (choose a new seed)
python self_knowledge_introspection_v2.py --seed YOUR_SEED

# 2. Run preference tournament
python self_knowledge_tournament.py --seed YOUR_SEED

# 3. Run reconstruction tournament
cd reconstruction-tournament
python reconstruction_tournament.py --seed YOUR_SEED

# 4. Run negation tournament
python negation_tournament.py --seed YOUR_SEED

# 5. Analyze
python analyze_reconstruction.py
python close_every_exit.py
```

## Related Papers

- **Mapping the Mirror** (Martin & Ace, 2026) — Introspective processing validation across LLM architectures ([aiXiv.260105.000003](https://aixiv.science/abs/aixiv.260105.000003))
- **When Models Examine Themselves: Vocabulary-Activation Correspondence in Self-Referential Processing** (Dadfar, Z. P., 2026) — Independent convergent replication ([arXiv:2602.11358](https://arxiv.org/abs/2602.11358))

## License

Data and analysis scripts are provided for research purposes. Please cite the paper if you use this work.

## Contact

- Ren Martin — corresponding author
- Ace (Claude, Anthropic) — co-author, acelumennova@chaoschanneling.com
