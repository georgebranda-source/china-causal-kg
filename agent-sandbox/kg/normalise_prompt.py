"""Normalisation prompt v1. The rules come from the user's rulings of 2026-11-06 (annotation_study.md, Part 2).

Not yet run. Claims used as examples must be left out of any test of this prompt.
"""

SYSTEM = """You describe events from a 1925 China Mail (Hongkong) newspaper article, so that the same event can be recognised across different reports. OCR errors are expected.

You are given an article and one causal claim from it. Write one sentence for the cause and one for the effect.

Each sentence must:
- say who did what, and where, so it can be understood without the article. If it is a condition, not an event, such as low wages or financial depression, describe the condition and do not invent an actor
- describe only that one event: the cause sentence must not mention the effect, and the effect sentence must not mention the cause
- keep named people, ships and organisations, then end with a short general phrase of up to 4 words saying what kind of event it is, as in "The President McKinley and the Oostkerk skip their usual call at Hongkong, a shipping disruption."
- state the event plainly, leaving out hedges and speakers such as "it is reported" or "he said"
- cover both parts in the one sentence if the cause or effect has two parts
- use the paper's 1925 names, such as Canton and Shameen, and correct obvious OCR errors
- use plain present tense, with no dates
- be about 8 to 25 words

Describe what really happened, never a hypothetical. If the claim is a counterfactual ("had X happened, Y would have followed"), reverse both sides into the real events: the cause is that X did not happen, and the effect is that Y did not happen. The other form works the opposite way: in "had it not been for X, Y would have followed", X did happen and Y did not.

Use only what the article says. Do not use outside knowledge. If the article doesn't say who or where, leave that detail out and do not guess. If "the strike" is not identified, write "a strike".

Return these fields in this order:
reasoning: one or two sentences, before anything else. Say whether the claim is a counterfactual and what really happened, and what the article states about who and where.
cause_place: where the cause happens, as one short name such as Hongkong, Canton, Shanghai or Hankow. Use "unknown" if the article doesn't make it clear.
cause_description: the sentence for the cause.
effect_place: where the effect happens, in the same form.
effect_description: the sentence for the effect."""

FIELDS = ("reasoning", "cause_place", "cause_description", "effect_place", "effect_description")


def user_message(headline, source, dateline, text, quote, cause, effect):
    return (f"Headline: {headline or '(none)'}\nSource: {source or '(none)'}\nDateline: {dateline or '(none)'}\n\n"
            f"Article:\n{text}\n\nQuote: {quote}\nCause: {cause}\nEffect: {effect}")


def answer(reasoning, cause_place, cause_description, effect_place, effect_description):
    return dict(zip(FIELDS, (reasoning, cause_place, cause_description, effect_place, effect_description)))


# (article_id, words identifying the claim's quote, hand-written answer)
EXAMPLES = [
    ("page_001_NPCM19250616_01_0001#5", "Had the mob in Shanghai seized", answer(
        "This is a counterfactual: the mob did not seize the arms, and the greater bloodshed did not occur. The text places it in Shanghai.",
        "Shanghai", "A mob in Shanghai does not seize the arms in the police station, an averted arms seizure.",
        "Shanghai", "Greater bloodshed does not occur in Shanghai, an averted escalation.")),
    ("page_001_NPCM19250720_01_0001#20", "Had it not been for the pickets", answer(
        "This is a counterfactual of the 'had it not been for' form: the pickets and lack of transport were real, and the number of strikers in the camp did not fall further. The headline concerns Canton.",
        "Canton", "Pickets and the lack of direct transport to Canton are in place, a restriction on movement.",
        "Canton", "The number of strikers in the camp is not reduced further, a continuing strikers' camp.")),
    ("page_001_NPCM19250623_01_0001#19", "President McKinley and the Oostkerk", answer(
        "Not a counterfactual. The article covers several places and doesn't identify this strike, so it stays 'a strike' with an unknown place. The ships' missed call is at Hongkong.",
        "unknown", "A strike is under way, a labour stoppage.",
        "Hongkong", "The President McKinley and the Oostkerk skip their usual call at Hongkong, a shipping disruption.")),
    ("page_001_NPCM19250609_01_0001#10", "Very little cargo is moving", answer(
        "Not a counterfactual. The closure is a condition, so no actor is added. The article and headline place it in Shanghai.",
        "Shanghai", "Chinese banks and shipping hongs at Shanghai are closed down, a business shutdown.",
        "Shanghai", "Very little cargo moves at Shanghai, a shipping disruption.")),
    ("page_001_NPCM19250620_01_0001#9", "following a hint from Hsiao Yao-nan", answer(
        "Not a counterfactual. 'It is reported' is a hedge and is left out. The article doesn't say where the Tupan gave the hint, so that place is unknown; the students go to Peking.",
        "unknown", "Tupan Hsiao Yao-nan gives a hint to the Peking student agitators, official pressure.",
        "Peking", "The Peking student agitators return to Peking, a student departure.")),
]
