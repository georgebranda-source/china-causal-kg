# Claim tagging codebook

Each row is one causal claim extracted from the China Mail (Hongkong), April-November 1925. Tag what the text says. Do not correct it from outside knowledge. Use the quote and article context, not only the short cause and effect labels. If a code is a close call, choose the best fit and set `confidence` to `low`.

Output one CSV row per claim, with exactly these columns:

`id,relevance,cause_type,effect_type,cause_actor,effect_actor,effect_mode,cause_place,effect_place,voice,stance,confidence`

## relevance
- `CORE`: the 1925 strikes, boycott or anti-foreign movement in China or Hongkong, including May 30, Shameen, and responses to them.
- `CONTEXT`: Chinese or Canton politics, war or economy in the same period, not directly about the movement.
- `LOCAL`: everyday Hongkong or China items unrelated to the movement (accidents, crime, health, weather, sport, courts).
- `FOREIGN`: events outside China and Hongkong with no China connection (Europe, Australia, South Africa, and so on).
- `AD_NOTICE`: advertisements, shipping or cargo notices, the paper's own delivery notices, business notices. Use this even when the notice mentions the strike.

## cause_type, effect_type
Pick one for each side:

`STRIKE_ACTION` (strikes, walkouts, stopping work) · `BOYCOTT_EMBARGO` · `PICKET_ENFORCEMENT` · `INTIMIDATION` (threats, coercion, terror) · `AGITATION_PROPAGANDA` · `BOLSHEVIK_INFLUENCE` (Soviet, Communist, Red influence as such) · `CANTON_POLICY` (acts or policy of the Canton government) · `PROTEST_DEMONSTRATION` · `RIOT_MOB_VIOLENCE` · `POLICE_MILITARY_FORCE` (firing, landing forces, dispersing crowds) · `CASUALTIES` · `ARREST_TRIAL_PUNISH` · `SECURITY_PRECAUTION` · `DIPLOMACY_NEGOTIATION` · `POLICY_DEMAND` (calls for action, resolutions asking for measures) · `CIVIL_WAR_MILITARY` (Chinese factional fighting) · `GOVERNANCE_WEAKNESS` (weak government, misrule, disorder as a condition) · `LABOUR_CONDITIONS_WAGES` · `ECONOMIC_HARM_TRADE` · `TRANSPORT_DISRUPTION` · `FOOD_SUPPLY` · `FINANCE_MONEY` · `RETURN_REPLACEMENT` (return to work, replacing strikers, volunteers) · `STRIKE_FUNDS_HARDSHIP` (strike pay, hunger, rifts among strikers) · `PUBLIC_SENTIMENT` (anti-foreign feeling, nationalism, excitement, fear) · `TREATY_SOVEREIGNTY` · `EDUCATION_MISSIONS` · `PRESS_RUMOUR` · `OTHER_EVENT`

## cause_actor, effect_actor
Who acts or who is the subject on that side:

`BRITISH_AUTH` (Hongkong Government, British ministers, British forces, consuls, and the Shanghai Municipal Council and its police) · `OTHER_FOREIGN_AUTH` (other foreign governments, consuls, forces, including Japan) · `FOREIGN_CIVIL` (foreign merchants, firms, shipowners, residents, missionaries) · `CHINESE_WORKERS` (strikers, labourers, seamen, servants, coolies) · `STUDENTS` · `AGITATORS_UNIONS` (agitators, unions, strike committees, pickets, intimidators) · `CANTON_GOV` (Canton government, Kuomintang, Whampoa cadets) · `BOLSHEVIK_SOVIET` · `CHINESE_OFFICIAL` (Peking, provincial officials, militarists) · `CHINESE_MERCHANTS` · `CHINESE_PUBLIC` (crowds, mobs, the people) · `IMPERSONAL` (conditions, economy, weather, no actor) · `OTHER`

## effect_mode
How the text frames what happens on the effect side:
- `VOLUNTARY`: an actor chooses or decides.
- `FORCED`: the actor is compelled, driven, obliged, left no option, or acts under threat.
- `RESPONSE`: an actor reacts to the cause, with no stress on compulsion.
- `HAPPENING`: harm, state or change with no actor choosing.

## cause_place, effect_place
Where that side takes place, judged separately for each side:

`HONGKONG` · `CANTON` (Canton, Shameen, Kwangtung) · `SHANGHAI` · `OTHER_CHINA` (a named place elsewhere) · `CHINA_GENERAL` (China as a whole) · `ABROAD` · `UNKNOWN`

## voice
Who is making the claim, as far as the context shows:
- `PAPER_LEADER`: the China Mail's own editorial comment.
- `PAPER_NEWS`: reporting with no other named source, including unattributed cables.
- `OFFICIAL`: British or foreign officials, ministers, MPs, police, councils.
- `BRIT_COMMUNITY`: foreign residents, merchants, company meetings, public meetings.
- `CHINESE`: Chinese officials, strikers, unions, merchants or writers.
- `OTHER_PRESS`: another newspaper or journal, named or clearly reprinted.
- `LETTER`: a letter to the Editor.
- `OTHER`: another named source (clergy, scholars, witnesses).
- `UNCERTAIN`: comment with no way to tell the source.

## stance
- `ASSERT`: the source states it as true.
- `REJECT`: the source denies or argues against this causal link.
- `REPORTED_DOUBT`: rumour, alleged, or reported with distance.
- `COUNTERFACTUAL`: what would have happened, or conditional and future statements.

## confidence
`high` or `low`.
