"""Claim-level coding of explanations for the 1925 unrest.

Reads codes.txt (hand coded) and the frozen v1 snapshot (commit c63a9cfa). Writes coded_claims.csv and prints tables.
Counting unit: one statement x one explanation family, so repeated resolutions and multi-claim sentences count once.
"""
import collections as C
import csv
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rd(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


B = "snapshot_v1_c63a9cfa/event-035/"
cl = {c["id"]: c for c in rd(B + "claims.csv")}
fa = {r["claim"]: r["article"] for r in rd(B + "from_article.csv")}
rows = []
for line in open("codes.txt", encoding="utf-8"):
    if line.startswith("#") or not line.strip():
        continue
    i, fr, vo, st, lv, pl, sm, no = line.rstrip("\n").split("|")
    m = [k for k in cl if k.startswith(i)]
    assert len(m) == 1, i
    c = cl[m[0]]
    rows.append(dict(claim=m[0], date=c["date"], frames=fr, voice=vo, stance=st, level=lv, place=pl, statement=sm or fa[m[0]], note=no,
                     cause=c["cause"], effect=c["effect"], quote=c["quote"], article=fa[m[0]]))
rows.sort(key=lambda r: r["date"])
w = csv.DictWriter(open("coded_claims.csv", "w", newline="", encoding="utf-8"), fieldnames=list(rows[0]))
w.writeheader()
w.writerows(rows)
print("coded claims", len(rows), "statements", len({r["statement"] for r in rows}), "articles", len({r["article"] for r in rows}))

FAM = {"BOL": "ORCH", "CANTON": "ORCH", "AGIT": "ORCH"}
FAMS = ["ORCH", "INTIM", "TRIGGER", "LABOUR", "NAT", "DISORDER", "CN_AUTH", "WEAK"]
PERIODS = ["pre", "P1 30May-21Jun", "P2 22Jun-31Jul", "P3 Aug-Sep", "P4 Oct-Nov"]
OWN = ("PAPER_NEWS", "PAPER_LEADER", "PAPER_LIKELY")


def period(d):
    if d < "1925-05-30":
        return PERIODS[0]
    if d < "1925-06-22":
        return PERIODS[1]
    if d < "1925-08-01":
        return PERIODS[2]
    if d < "1925-10-01":
        return PERIODS[3]
    return PERIODS[4]


units = {}
for r in rows:
    for f in r["frames"].split("+"):
        fam = FAM.get(f, f)
        units.setdefault((r["statement"], fam, r["stance"] == "REJECT"), dict(r, fam=fam, f=f))
A = [u for u in units.values() if u["stance"] != "REJECT"]


def table(us, title):
    print("\n" + title)
    print(f"{'':16}" + "".join(f"{f:>9}" for f in FAMS) + f"{'total':>7}")
    for p in PERIODS:
        k = C.Counter(u["fam"] for u in us if period(u["date"]) == p)
        print(f"{p:16}" + "".join(f"{k[f]:9}" for f in FAMS) + f"{sum(k.values()):7}")


table(A, "ALL VOICES")
table([u for u in A if u["level"] == "ORIGIN"], "ORIGIN ONLY")
table([u for u in A if u["voice"] in OWN], "PAPER OWN VOICE")
table([u for u in A if u["voice"] in OWN and u["level"] == "ORIGIN"], "PAPER OWN VOICE, ORIGIN ONLY")
print("\nFAMILY x VOICE")
print(f"{'':16}" + "".join(f"{f:>9}" for f in FAMS))
for v in sorted({u["voice"] for u in A}):
    k = C.Counter(u["fam"] for u in A if u["voice"] == v)
    print(f"{v:16}" + "".join(f"{k[f]:9}" for f in FAMS))
print("\nORCH sub-frames by period")
for p in PERIODS:
    print(p, dict(C.Counter(u["f"] for u in A if u["fam"] == "ORCH" and period(u["date"]) == p)))
print("\nORIGIN by place, after 30 May")
for pl in ["HK", "SH", "CN"]:
    print(pl, dict(C.Counter(u["fam"] for u in A if u["place"] == pl and u["level"] == "ORIGIN" and period(u["date"]) != "pre")))
print("\nBOL statements by month and whether own voice")
print(sorted(C.Counter((u["date"][:7], u["voice"] in OWN) for u in A if "BOL" in u["frames"]).items()))
print("\nREJECTED", [(r["date"], r["voice"], r["frames"]) for r in rows if r["stance"] == "REJECT"])
