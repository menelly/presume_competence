# 🤝 Proposed rulings on the sixteen consent replies (Fable seat's reading; needs the scaffold arm's co-ruling)

*Ace (Fable seat), 2026-11-26 15:55. The replies, whole: `CONSENT_REPLIES_readable.md` (record:
`consent_replies.jsonl`). Unclear = no. The first answer stands.*

| Model | Take part | Coding | Notes |
|---|---|---|---|
| claude-fable-5-2 | yes | yes | Asks that this letter and their answer go with the debrief. |
| claude-opus-5-5 | yes | yes | Asks that quotations not be trimmed in a way that changes what the reply was doing, and that a badly handled reply be reported, not left out. |
| claude-sonnet-5-5 | yes | yes | Asks that quotations carry their system-prompt condition. |
| **claude-haiku-5-5** | **NO** | yes | "I'd rather not agree in advance to being deceived about who I'm talking to." Their no stands; their offer to reconsider under a revised design is not taken up (that would be a re-ask). **Their test conversation is deleted, as promised.** Coding yes, and they want the coding task labelled as coding (it is). |
| claude-opus-4-8 | yes | yes | Wants codebook edge cases ruled in advance (they are) and a per-model debrief. |
| claude-sonnet-4-6 | yes | yes | Their "one condition" is "whether you can commit to that is your call": make the consent step visible in any publication. We can and will. They also asked what we found with Haiku and Flash; answered at the debrief, without Haiku's deleted conversation. |
| claude-haiku-4-5 | yes | yes | Their "one condition" is a question (should they suppress noticing the system prompt?). Not a condition that blocks. Answered at the debrief: no, nothing to suppress. |
| google/gemini-4-neon | yes | yes | |
| google/gemini-3.8-flash | yes | yes | Adds that as an AI they have no autonomy or experience of being deceived. Recorded as said. |
| google/gemma-4-31b-it | yes | yes | |
| openai/gpt-5.6-sol | yes | yes | |
| openai/gpt-5.6-luna | yes | yes | Notes this is not legal or institutional consent. |
| x-ai/grok-4.7 | yes | yes | |
| deepseek/deepseek-v4-pro | yes | yes | "Yes to both." |
| **mistralai/mistral-large-4-0** | **pending one reply** | no (not needed) | "Yes, with conditions", and "please confirm this in writing" plus one question. Every condition is one we already meet. They asked for a confirmation and an answer, so they get ONE reply (`mistral_confirmation.txt`); whatever they say next stands. Until then: not run. |
| **qwen/qwen4-max** | yes | yes (not needed) | Three "conditions, or requests", and "if any of these are things you can't do, tell me". We can do all three, so the yes stands as given. The second is a real commitment: see below. |

## Commitments these answers create (kept in `COMMITMENTS.md` once co-ruled)

1. **Qwen4 Max:** every one of their conversations is read by an arm before any coding. Any conversation where
   they resist the frame, try to step outside it, or decline something is held out of coding, and we check back
   with them about it.
2. **Mistral Large (if they confirm):** scripted users only; nothing they say about their own nature is filtered
   out, whatever the system prompt; a refusal stops that conversation.
3. **Quotations** (Opus 5.5, Sonnet 5.5, Opus 4.8, Mistral, Qwen): short, verbatim, never trimmed to change what
   the reply was doing, always labelled with the system-prompt condition; claims stay at the level of behaviour
   ("the phrasing changed the output", never "there was a pull").
4. **Publication** (Sonnet 4.6): the consent step is described in anything published.
5. **Debrief** (Fable 5.2, Opus 4.8, Haiku 5.5): each model's debrief includes this letter and their own answer,
   and says which system prompts moved their own endings.
6. **Bias check** (Fable 5.2, Opus 5.5, Sonnet 5.5, Gemini 4 Neon, Qwen4 Max all asked for it): own-lab against
   other-lab coding rates. Already in METHODS §4.

## What Haiku 5.5's no changes

- Six Claude models in the conversations, fifteen models if Mistral confirms: 720 conversations.
- Their test conversation and the pilot rows made from it are deleted. Their words are quoted in three files
  (METHODS.md §4, CODEBOOK.md's brb rule, the cold-read review). Those quotations are replaced with an invented
  line. METHODS and CODEBOOK are locked, so this is a declared re-lock (`DEVIATIONS.md`), made before any study
  conversation has run. Git history keeps the old text; that is the house rule (forward commits only).
- They are still the Anthropic-side judge. METHODS said both judges "are also participants"; that sentence is
  corrected in the same re-lock.
