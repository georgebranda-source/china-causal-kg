# Causes of the Hongkong-Canton strike and boycott, as given in the China Mail

Snapshot `../temporal/snapshot_v1_ceb6e08a` (event-035), April 1925 to November 1926. Coded by Claude, 2026-11-11.

## What was read
- 356 claims whose effect mentions a strike, boycott, pickets, a stoppage or a return to work (`candidates.csv`), plus 254 more claims from December 1925 onward that mention these in cause, effect or quote (`wider_1926.txt`). All were read; voice was checked in article context (`context.py`, `head.py`) where it mattered.
- Most are about other strikes: Shanghai, the British General Strike, foreign strikes. Some are effects of the strike, not causes. Only claims that explain the Hongkong-Canton strike or boycott were coded (`codes_hk.txt`).
- The Hongkong rows of the 1925 explanations study (`../explanations/codes.txt`) are merged in for origins and participation.
- Result: 93 statement units across four questions (`coded_claims.csv`, `analyse.py`). One coder, no reliability check, small counts: indicative only.

## Findings
1. **Origin, Hongkong side: engineered from outside, never grievances.** In June to September 1925, 17 of 20 origin statements blame Bolsheviks, Canton or intimidation. The Hongkong Governor was still saying "instigated by Bolshevik intrigues" in October 1926. No claim in the corpus gives wages or working conditions as a cause of the Hongkong strike.
2. **Origin, Chinese side: the shootings.** In 1925, only the strikers' own notice (22 June: deaths in Shanghai) and one letter to the editor give the shootings as the cause. In 1926, four of the five "massacre" statements come from Canton: the Chinese delegation (24 July), Canton's reply (26 July), the Canton Gazette and the Strike Committee/Kuomintang declarations (October). The paper prints these but never adopts them. The Chinese delegation's own wording is that 23 June caused the "intensification and extension" of the Hongkong strike, which fits the strike having begun a few days earlier.
3. **Joining, 1925: coercion.** 11 of 15 statements on why Hongkong workers came out cite intimidation, and most of the rest cite orders from Canton. Workers rarely appear as choosing to strike.
4. **Why it lasted: blame moves.**
   - 1925: pickets keep strikers in Canton; the strike organisation grows stronger.
   - Winter 1925-26, around the failed negotiations: the Canton Government. It connives at or cannot control the pickets (8 of 15 statements), and the boycott "would not last a day" without picket terror. The paper's leaders, Governor Clementi and Amery in the Commons all say this. Profiteering ("vested interest") appears in reprints.
   - September 1926: Chiang Kai-shek is "a staunch supporter of the boycott".
   - 16 November 1926: the paper reverses itself. Canton "has been sincerely trying to end the boycott"; the pickets were too strong.
   - Canton's own answer, which the Hongkong side never takes up: Hongkong's June 1925 embargo on exporting food and silver to Canton, read as an attempt to starve Canton, kept the boycott going.
5. **Why it weakened or ended.**
   - 1925, individuals: rifts among strikers, police raids, threat of deportation, and inducements to return.
   - 1926, news reports: the Northern Expedition. Strikers were drafted as coolies and constables, and Chiang wanted a settlement. Canton also needed revenue.
   - September to October 1926, from the British side: force, with pickets to be treated as pirates.
   - Canton's October 1926 manifesto also points to the war: the advance to the Yangtze "changed the technique" of the struggle. The Northern Expedition is the one explanation of the ending that both sides' sources share.

## Limits
- Only explicit causal claims, as extracted, on pages selected by strike score.
- Coverage is thin from November 1925 to April 1926.
- The keyword search for 1926 may have missed explanations worded without strike, boycott or picket terms.
- Reports from correspondents in Canton are coded PAPER_NEWS.
- The strikers' own voice reaches the paper only through Canton statements and the 22 June notice.
