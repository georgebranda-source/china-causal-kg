"""Tabulate explanations of the Hongkong-Canton strike and boycott by question, period and voice.
Merges codes_hk.txt (this study) with the Hongkong rows of ../explanations/codes.txt (1925 origins, participation)."""
from pathlib import Path
import pandas as pd
HERE = Path(__file__).parent
claims = pd.read_csv(HERE.parent / "temporal/snapshot_v1_ceb6e08a/event-035/claims.csv", usecols=["id", "date", "cause", "effect", "quote"])
cols = ["id", "q", "families", "voice", "stance", "stmt", "note"]
new = pd.read_csv(HERE / "codes_hk.txt", sep="|", comment="#", names=cols, dtype=str).fillna("")
old = pd.read_csv(HERE.parent / "explanations/codes.txt", sep="|", comment="#",
                  names=["id", "families", "voice", "stance", "level", "place", "stmt", "note"], dtype=str).fillna("")
old = old[old.place == "HK"].assign(q=lambda d: d.level.map({"ORIGIN": "O", "PARTICIPATION": "J"}))[cols]
codes = pd.concat([old.assign(src="explanations"), new.assign(src="strike_causes")])
codes["full"] = codes.id.map(lambda p: claims.id[claims.id.str.startswith(p)].iloc[0])
d = codes.merge(claims, left_on="full", right_on="id", suffixes=("", "_c"))
d["date"] = pd.to_datetime(d.date)
d["period"] = pd.cut(d.date, pd.to_datetime(["1925-01-01", "1925-10-01", "1926-04-01", "1926-08-01", "1926-12-01"]),
                     labels=["1 Jun-Sep 1925", "2 Oct 1925-Mar 1926", "3 Apr-Jul 1926", "4 Aug-Nov 1926"], right=False)
d["unit"] = d.stmt.where(d.stmt != "", d.full)
u = d.assign(family=d.families.str.split("+")).explode("family").drop_duplicates(["unit", "family"])
u = u[u.stance != "REJECT"]
d.drop(columns=["id_c"]).to_csv(HERE / "coded_claims.csv", index=False)
for q, name in [("O", "WHY IT STARTED"), ("J", "WHY PEOPLE JOINED (1925)"), ("P", "WHY IT LASTED"), ("E", "WHY IT WEAKENED OR ENDED")]:
    x = u[u.q == q]
    print(f"\n== {name}: {x.unit.nunique()} statements")
    print(pd.crosstab(x.family, x.period, margins=True).to_string())
    print(pd.crosstab(x.family, x.voice).to_string())
