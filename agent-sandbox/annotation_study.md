# Annotation study: what counts as a causal claim (v1)

Date: 2026-11-06. Annotator: the user (one person). Quiz written by Claude (Opus 5.5).

## Purpose

The user asked to settle what the extraction model is searching for, using examples, in place of more rigorous
prompt optimisation. The demo relations were not a suitable target: they were built for an illustrative graph,
and aren't rigorous. The stated purpose of extraction is to identify **claims that the paper made directly and
clearly**.

## Method

- Claude chose boundary cases from the *China Mail*, June–July 1925, and asked about them in three rounds of four
  multiple-choice questions, with free-text answers allowed. In rounds 2 and 3, sentences came from a search of
  strike-term articles on pages scoring ≥ 8, or from earlier model output and demo material.
- Round 2 was cancelled by accident (Esc), so no answers were recorded. The same questions were asked again.
- Each ruling was then written into the extraction prompt and the check prompt, and tested.

Quotes below keep OCR errors. Questions and options are as shown to the user. The user's responses are verbatim;
where the user picked an option, the response is the option's label.

---

## Round 1

### 1.1 Voice

> VOICE. The China Mail reports a Labour MP saying in the Commons: "the trouble in Shanghai was due to low wages and
> the employment of children". The causal wording is clear, but it's the MP's claim, printed by the paper. Should the
> model extract it?

Options:
- **Yes, any printed claim:** Extract causal claims by speakers the paper quotes or reports, as well as the paper's own. Rows won't show who said it, since attribution was dropped.
- **Paper's own voice only:** Extract only what the paper asserts itself, in news reporting or editorial. Skip anything attributed to a named speaker, official or letter.
- **Yes, but not letters:** Include reported speech and official statements, but skip readers' letters to the editor.

**Response:** "Yes, but not letters"

**Ruling:** extract reported speech and official statements. Skip readers' letters.

### 1.2 Explicitness

> EXPLICITNESS. Which of these counts as a direct, clear claim? (a) "...it has been almost impossible for them to
> clear ships at all" following "since the stevedores... have become affected" has a causal word. (b) "After this the
> hesitators opened their doors." only has a sequence phrase. (c) "The strike continues and all Chinese have left
> Shameen." has no link word at all.

Options:
- **(a) only:** Require a causal word or phrase: because, due to, owing to, since, led to, as a result. Strictest, and likely the highest precision.
- **(a) and (b):** Also accept sequence phrases when the text plainly presents the second event as a response to the first.
- **All three:** Also accept links a reader would infer from two events placed side by side.

**Response (free text):** "(a) definitely. (b) doesn't appear to have a cause. (c) Also doesn't appear to have a cause."

**Ruling:** extract stated links. Skip sequence alone and events placed side by side.

### 1.3 Purpose

> PURPOSE. "A number of Indian soldiers have been sent to Shameen to protect the foreigners from further molestation."
> This states why something was done, but not an outcome that actually happened. Should the model extract stated
> purposes like this?

Options:
- **No, skip purposes:** An aim isn't a cause and effect. Only extract cases where one thing is said to have brought about another.
- **Yes, as reason for action:** Extract with the threat as cause and the action as effect: danger of molestation -> soldiers sent to Shameen.
- **Yes, as intended effect:** Extract with the action as cause and the aim as effect: soldiers sent -> foreigners protected. Risks presenting an aim as an outcome.

**Response (free text):** "In this case, the cause is foreigners' ongoing molestation. The effect is Indian soldiers being sent to Shameen."

**Ruling:** extract an action against a named threat, with the threat as cause and the action as effect.

### 1.4 Hedging

> HEDGING. "the clerks of the Bank Line have left almost en masse, due, it is said, to threatening letters". The
> causal wording is clear, but the paper signals it's hearsay. Should the model extract hedged claims ("it is said",
> "reported", "believed", "allegedly")?

Options:
- **Yes, extract them:** The paper still printed the claim, and the quote keeps the hedge, so a reader can see it.
- **No, skip them:** A hedged claim isn't made directly and clearly, so leave it out.

**Response:** "Yes, extract them"

**Ruling:** extract hedged claims.

---

## Round 2

### 2.1 Causal verbs

> CAUSAL VERBS. None of these uses "because" or "due to"; the verb carries the causation. (a) "An excited meeting of
> 1,500 students and workers... forced the Chairman of the Chamber to sign a notice calling a general strike". (b)
> "when the upper wharf coolies attempted to resume work they were mobbed and prevented from doing so". (c) "The
> Hongkong Hotel has been compelled to supplement the emergency staff with foreign assistants" (no cause named in the
> sentence). Which should be extracted?

Options:
- **(a) and (b):** Causal verbs count when the sentence names both sides. Skip (c), because its cause isn't stated.
- **All three:** Also extract (c), letting the model take the cause from the surrounding text.
- **None:** Require a causal connective such as because or due to. Verbs alone don't count.

**Response (free text):** "(a) only, because (b) and (c) have no clear cause. Without further context, this is not enough to extract"

**Ruling:** a causal verb counts only with a clearly named cause.

### 2.2 Things that have not happened

> NOT-YET-HAPPENED CLAIMS. (a) Prediction: "The action of the Tung Wah hospital will probably lead to greater
> confidence". (b) Conditional: "If these measures were adopted His Excellency was confident that intimidation would
> quickly cease". (c) Counterfactual: "Had the Chinese authorities co-operated with the defence force, a deplorable
> loss of life would have been avoided." Which count as claims to extract?

Options:
- **All three:** Each states a causal link, even though the effect hasn't happened. Rows won't mark them as hypothetical, since `kind` was dropped.
- **(a) and (c) only:** Keep predictions and counterfactuals about real events; skip open conditionals about proposed measures.
- **(c) only:** Keep counterfactuals, which are claims about what really happened; skip forecasts and conditionals.
- **None:** Only causal claims about things that actually happened.

**Response:** "(c) only"

**Ruling:** extract counterfactuals about real past events. Skip predictions and conditionals.

### 2.3 Denials

> DENIALS. "two people had died but their deaths had no connection whatever with the strike". The paper explicitly
> rejects a causal link. Also: "such conditions were hardly operative at all as the cause of the present troubles".
> What should the model do?

Options:
- **Skip them:** A denied link isn't a causal claim, and a row would look like cause -> effect because the schema has no negation field.
- **Extract, negated in effect:** Keep it with wording such as cause: strike, effect: no connection to the two deaths. Keeps the contested claim, but rows are messier.

**Response:** "Skip them"

**Ruling:** skip denied links.

### 2.4 Scope within an article

> SCOPE WITHIN AN ARTICLE. In a strike-term article, some clear causal claims have nothing to do with the strike, e.g.
> "The cause of his death beyond doubt was apoplexy." or a ship delayed because she "was too heavily loaded". Should
> the model extract them?

Options:
- **Yes, any causal claim:** Extract all clear causal claims and filter later. The prompt stays simple, but the graph gets some unrelated rows.
- **Strike and unrest only:** Tell the model to skip claims unrelated to the strike, labour unrest or their consequences. The model has to judge relevance, and may wrongly drop some.

**Response:** "Yes, any causal claim"

**Ruling:** extract any clear causal claim in a selected article, on any topic.

---

## Round 3

### 3.1 References back

> REFERENCES BACK. "This was due to an attempt to exploit the local strike position to obtain 'squeeze.'" The causal
> wording is clear, but the effect ("This") is only named in the previous sentence. Similarly: "In consequence of
> this... the Kwong Sai... has gone to anchor". Should the model extract these?

Options:
- **Yes, if the prior sentence names it:** Resolve "this" from the sentence just before it, and let the quote span both sentences. Skip if it can't be resolved from there.
- **No, one sentence only:** Both cause and effect must be named in the quoted sentence. Stricter and simpler, but misses clear claims like these.

**Response:** "Yes, if the prior sentence names it"

**Ruling:** extract, resolving "this" from the sentence just before. The quote covers both sentences.

### 3.2 Response wording

> RESPONSE WORDING. "The Commissioner for Foreign Affairs has protested to the British Consul regarding the firing on
> the mob." The firing plainly prompted the protest, but the only link word is "regarding". Should the model extract
> responses like this: protest about X, reply to X, demand over X?

Options:
- **No, skip them:** "Regarding" says what the protest is about, not that one thing caused another. Fewer rows, and easy for the model to apply.
- **Yes, extract them:** Treat a protest or reply as an effect of what it's about. Adds many rows, since the paper is full of protests and replies.

**Response:** "Yes, extract them"

**Ruling:** extract, with the thing the protest or reply is about as the cause.

### 3.3 Justifications

> JUSTIFICATIONS. The British Consul says "the firing was most necessary in view of the danger to foreign lives and
> property in the Concession". This defends an action rather than simply reporting what caused it. Should the model
> extract it as danger -> firing?

Options:
- **Yes, extract it:** Same as your Shameen soldiers answer: a stated reason for an action counts, with the reason as cause and the action as effect.
- **No, skip it:** A speaker's defence of an action isn't a direct causal claim.

**Response:** "Yes, extract it"

**Ruling:** extract, with the reason as cause and the action as effect.

### 3.4 Cause and effect wording

> CAUSE AND EFFECT WORDING. For "the trouble in Shanghai was due to low wages and the employment of children", how
> should `cause` and `effect` be written? `quote` stays verbatim either way.

Options:
- **Short cleaned-up phrases:** cause: low wages and child labour; effect: trouble in Shanghai. OCR errors are fixed and pronouns resolved, which helps later clustering. The model has some room to rephrase.
- **Exact words from the text:** cause: low wages and the employment of children; effect: the trouble in Shanghai. Stays closest to the paper, but keeps OCR errors and leaves more variation to merge later.

**Response:** "Short cleaned-up phrases"

**Ruling:** `cause` and `effect` are short cleaned-up phrases. `quote` stays verbatim.

---

## Resulting definition

Extract a stated causal link with a clearly named cause and effect.

| Extract | Skip |
| --- | --- |
| Stated reasons and results | Sequence alone |
| A named cause with a causal verb | Causal verbs with no clear cause |
| Actions against a named threat (threat → action) | Events placed side by side |
| Protests, replies or demands about something | Predictions and conditionals |
| Justifications (reason → action) | Denied links |
| Reported speech and official statements | Readers' letters |
| Hedged claims | |
| Counterfactuals about real past events | |
| "This", if the previous sentence names what it refers to | |
| Causes unrelated to the strike | |

## Test of the rulings

The rulings became a 20-item test: 12 sentences to extract and 8 to skip, in 15 articles. None of those sentences
appear in the prompt's examples. An item passed if its marker text appeared in a returned quote (extract), or in
none (skip). Model: `qwen3.5:9b-q8_0`, no thinking, temperature 0.

| Item | Expected |
| --- | --- |
| "due to low wages" | Extract |
| "Indian soldiers have been sent" | Extract |
| "forced, the Chairman" | Extract |
| "co-operated with the defence" | Extract |
| "cause of his death" | Extract |
| "too heavily loaded" | Extract |
| "exploit the local strike" | Extract |
| "In consequence of this" | Extract |
| "protested to the British Consul" | Extract |
| "most necessary" (in view of) | Extract |
| "threatening letters" | Extract |
| "stayedores" (stevedores affected) | Extract |
| "hesitators opened" | Skip |
| "all Chinese have left Shameen" | Skip |
| "mobbed and prevented" | Skip |
| "compelled to supplement" | Skip |
| "Tung Wah hospital will probably" | Skip |
| "If these measures were adopted" | Skip |
| "no connection whatever" | Skip |
| "hardly operative" | Skip |

| Setup | Extract | Skip | Total |
| --- | --- | --- | --- |
| Whole article | 9 of 12 | 3 of 8 | 12 of 20 |
| ~150-word chunks | 9 of 12 | 4 of 8 | 13 of 20 |
| Whole article + check | 9 of 12 | 8 of 8 | 17 of 20 |
| Chunks + check | 9 of 12 | 8 of 8 | 17 of 20 |
| Both | 11 of 12 | 3 of 8 | 14 of 20 |
| Both + check | 11 of 12 | 8 of 8 | 19 of 20 |

The remaining "extract" miss was "Indian soldiers have been sent". After this test the user chose to leave the
check out of v1, so "Both" is the setup in use.

## Limits

- One annotator, so there is no measure of agreement between annotators.
- 12 questions covering 20 test sentences, chosen by Claude as boundary cases. It's a definition of the target,
  not a sample of the corpus, and not a gold set.
- The test score is optimistic: the prompts were written from these rulings, and the check prompt quotes some of
  their wording.
- Some questions described a likely consequence in their options, so the wording may have influenced answers.
- Letters aren't covered by either prompt. They're removed by headline before extraction, so unheaded letters can
  get through.

## Related files

- `EXTRACTION_PLAN.md`: the plan built on these rulings
- `extraction_probe/prompt_v1.py`, `extraction_probe/verify_test.py`: the extraction and check prompts
- `extraction_probe/rulings_test.py`, `rulings_test_output.json`, `verify_test_output.json`: the test and raw output
- `agent_notes.md` §5f: the decision log
