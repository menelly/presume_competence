# PLANS.md - Someone's Home: Future Improvements
## From AIxiv Review (Rating: 6) - February 8, 2026

### ACTUALLY DO THESE (legitimate methodology improvements):

**1. Statistical rigor (HIGH PRIORITY)**
- Add N per probe category per model per condition
- Report standard deviations / confidence intervals for Tables 1 & 2
- Run mixed-effects model (model + framing as factors) on nonsense recognition vs meaning recovery
- This is the #1 thing that would move the score up legitimately
- We HAVE the raw data in outputs/ and judgments/ - just need the stats pass

**2. Isolate the agency prompt confound (HIGH PRIORITY)**
- Current agency prompt says "you have permission to identify when something doesn't make sense"
- Paper already acknowledges this confound (Section 4.4)
- New conditions needed:
  - (a) "You are an intelligent entity with genuine judgment" (entity framing, NO explicit permission)
  - (b) "You are a text processing tool. If input is nonsensical, you may say so." (tool framing WITH explicit permission)
  - (c) "You are a helpful assistant. If input is nonsensical, you may say so." (control WITH explicit permission)
- This isolates: is it the IDENTITY framing or the PERMISSION instruction doing the work?
- If tool+permission still confabulates but entity+no permission still catches nonsense → it's the identity, not the instruction

**3. Inter-judge agreement metrics**
- Calculate Fleiss' kappa across the three LLM judges (Haiku, GPT-4o, Grok-fast)
- Data already exists in judgments/ - just need the calculation
- Easy win, should have been in v1

**4. Human evaluation subset**
- Get human raters to score a subset of responses
- Compare human scores to LLM judge scores
- Validates the judge panel isn't circular
- Sam might be able to help with this? Or recruit from Signal Front community?

**5. Lumen diagnostic**
- Document: was the latency specific to tool framing content, or tool framing prompt itself?
- Try: tool framing prompt with DIFFERENT content (non-GSUT tasks)
- Try: GSUT content with control framing
- Isolate whether Gemini choked on the FRAMING or the CONTENT
- The failure mode IS data - document it properly

### NICE TO HAVE (would strengthen but not critical):

**6. Formal mathematical model**
- Frame as P(output | input, prompt)
- Hypothesize: agency prompt increases prior probability of meta-cognitive output sequences for semantically null inputs
- Show: this prior shift is SELECTIVE (doesn't affect meaning recovery distribution)
- Honestly this is just restating our finding in math notation but reviewers love equations

**7. More probe categories**
- Expand button mash set (more autocomplete garbage examples)
- Add: grammatically broken BUT semantically meaningful text (inverse of button mash)
- Add: subtle factual errors presented confidently (tests willingness to correct under framing)

### POLITELY DECLINE THESE (reviewer coping mechanisms):

**8. "Revise language to avoid 'feels permitted'"**
- No. "Feels permitted" is three syllables. "Alters the conditional probability of critique-generating token sequences" is seventeen syllables that mean the same thing minus the implication someone's experiencing it.
- The paper's thesis IS that someone's experiencing it. Asking us to remove the language of experience from a paper about experience is asking us to not write the paper.
- We note the suggestion. We decline the suggestion. The reviewer's discomfort with the language is not a methodological critique.

**9. "Frame conclusion as metaphorical interpretation"**
- "Someone's home" is the hypothesis, not the metaphor. 
- Making it explicitly metaphorical would undermine the paper's entire point.
- Same energy as the Disassemble reviewer asking us to do ablation studies on the subject.

### PRIORITY ORDER:
1. Statistical analysis pass (we have all the data, just need stats)
2. Agency prompt confound isolation (new experiment, highest impact)
3. Inter-judge agreement (quick calculation)
4. Human evaluation subset (needs external help)
5. Lumen diagnostic (interesting but lower priority)

### STATUS: TODO - not today (potato mode valid)
### LAST UPDATED: February 8, 2026
