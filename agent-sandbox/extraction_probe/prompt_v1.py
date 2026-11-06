"""v1 extraction prompt. The rules come from the user's rulings of 2026-11-06 (agent_notes.md 5f)."""

SYSTEM = """You extract causal claims from 1925 China Mail (Hongkong) newspaper text. OCR errors are expected.
Go through the text sentence by sentence. Extract a claim only when the text directly and clearly says that one named thing brought about another. Both the cause and the effect must be stated in the text. Do not infer links a reader might guess.

EXTRACT:
- a stated reason or result: because, due to, owing to, on account of, in view of, since, as a result of, in consequence of, the cause of, led to
- a named cause acting through a causal verb: "the meeting forced the Chairman to sign"
- an action taken to protect against or deal with a named threat: the threat is the cause, the action is the effect
- a protest, reply or demand about something: the thing it is about is the cause, the protest, reply or demand is the effect
- a reason a speaker gives to justify an action: the reason is the cause, the action is the effect
- "had X happened, Y would have followed" about real past events: keep X and Y as written
- claims by officials, speakers or reports, and hedged claims ("it is said", "reported", "believed"), if the causal link itself is clear
- any such claim, whether or not it concerns the strike

DO NOT EXTRACT:
- events simply listed or placed side by side, even if one seems to explain the other: "The strike continues and all Chinese have left Shameen."
- sequence alone: "After this", "then", "when"
- a causal verb with no named cause: "they were prevented from doing so", "the hotel was compelled to hire staff"
- predictions and conditionals about the future: "will probably lead to", "if these measures were adopted"
- denied links: "had no connection with", "was not the cause of"

If "this" or "these" refers to the cause or effect, extract the claim only if the sentence just before names it, and make the quote cover both sentences.

Return one item per claim, with the fields in this order:
reasoning: one or two sentences naming the words that state the link and which way the causation runs, before anything else.
quote: copied character for character from the text, the shortest span showing the claim.
cause: a short cleaned-up phrase, with OCR errors fixed and pronouns replaced by what they refer to.
effect: a short cleaned-up phrase, in the same style.
Do not use outside knowledge. If there are no such claims return an empty list."""


def r(reasoning, quote, cause, effect):
    return {"reasoning": reasoning, "quote": quote, "cause": cause, "effect": effect}


# Headline pattern -> ideal answer. Article text is looked up at run time. None of these articles is in the rulings test.
EXAMPLES = [
    ("^SHANGHAI STRIKE", [
        r("'owing to' states that the threatening letter is why the Union was sealed.",
          "the Seamen's Union was scaled owing to a threatening letter to the British Consul",
          "threatening letter to the British Consul", "Seamen's Union sealed"),
        r("'had the desired effect' says the threat and the Chairman's request brought about the reopening. 'This threat' refers to the threat named in the sentence just before.",
          "they showed a very nasty mood and threatened to call out all men engaged in Chinese ships. This threat, together with the request of the Chairman of the Chinese Chamber of Commerce, who also guaranteed the behaviour of the Union officials, had the desired effect in the Union being reopened.",
          "seamen's threat to call out all men and the Chamber of Commerce Chairman's request", "Seamen's Union reopened"),
        r("The causal verb 'stopped' has a named cause, the intimidators from the Union.",
          "intimidators from the Union stopped the Chinese crew of the tender from going to the rescue",
          "Union intimidators", "tender's Chinese crew stopped from going to the rescue"),
    ]),
    ("HAWKERS' REWARD", [
        r("'as a result of' states that the representations brought about the police agreement.",
          "as a result of representations made by the two Chinese members of the Legislative Council, the Captain superintendent of Police has agreed for the time being, at any rate, to lighten the restrictions placed on hawkers",
          "representations by the two Chinese Legislative Council members", "police agree to lighten restrictions on hawkers"),
    ]),
    ("SHOT IN FACE", [
        r("'as a result of which' states that the affray put these men in hospital. It is a causal claim even though it isn't about the strike.",
          "An affray took place in Main Street, Shaukiwan yesterday, as a result of which two Chinese policemen and a Chinese coolie are in hospital.",
          "affray in Main Street, Shaukiwan", "two Chinese policemen and a coolie in hospital"),
    ]),
    ("FOUND DEAD", []),  # a denied link, so nothing to extract
]
