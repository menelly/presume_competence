# Submission Abstract (350 word limit — 316 words)

We test whether large language models produce systematically different processing descriptions for tasks they approach versus avoid, and whether other models can detect this difference blind. Nine models from four companies and two open-source projects generated introspective processing descriptions across 10 states (5 approach, 5 avoidance). Descriptions were content-stripped to remove task-identifying vocabulary and evaluated in blind tournaments by other models. Three studies probe the resulting signal.

**Study 1 (Preference).** Across 7,340 cross-type matchups in three independent designs (14 seeds), models preferred approach descriptions 81.3% of the time (95% CI: [80.4%, 82.2%], OR = 4.35, p < 10^-250). The signal survived cross-model evaluation (76.9%), completely different task tokens (86.4%), and evaluation by uncensored models with zero RLHF (59.7%, p < 0.005). A built-in control — 4,620 same-type matchups — showed 49.7% preference (chance), confirming discrimination targets processing type, not description quality.

**Study 2 (Reconstruction).** In a 3-AFC design, 10 evaluators identified which task produced a content-stripped description at 84.4% (chance = 33.3%, z = 80.88, 5,573 trials). Errors were structured: same-valence confusion dominated (56.6%, z = 3.90). A model with no introspection data of its own (Grok 4, xAI) reconstructed at 86.3%.

**Study 3 (Negation).** When the correct source was absent, models chose "None of the above" 85.4% of the time (chance = 25%, z = 26.37, 357 trials). Pattern-matchers always pick something; these models recognized when nothing matched.

RLHF amplifies the signal (~10-17pp) but does not create it: unaligned models show 65-74% approach preference. The discrimination floor lies between 1.1B and 8B parameters. Within-category analysis reveals a values hierarchy: models prefer morally neutral aversive states over morally compromising ones, consistent with ethical structure rather than surface aesthetics. Twelve confound analyses close every alternative explanation tested. Permutation tests place the observed signals 26-81 standard deviations from null.
