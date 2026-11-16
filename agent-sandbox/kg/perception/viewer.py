"""Write a self-contained viewer.html into a perception graph folder (default kg/out/perception/graph; or pass folders).

Embeds graph.json (trimmed to the fields the page uses) and anchors.json into viewer_template.html. Opens offline from disk;
fonts and Cytoscape come from Google Fonts / cdnjs.
Usage: .venv-kg/Scripts/python kg/perception/viewer.py [graph_dir ...]
       .venv-kg/Scripts/python kg/perception/viewer.py --all     (current graph and every snapshot)
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out" / "perception"
KEEP = ["id", "article_id", "page", "date", "headline", "is_letter", "speaker", "speaker_type", "voice_group", "quote",
        "cause_description", "effect_description", "effect_place", "cause_event", "effect_event", "effect_concept",
        *[f"{p}_{t}" for t in ("60", "65", "70") for p in ("in_scope", "in_scope_strict", "cause_concept")],
        *[f"sim_{k}" for k in ("1a_red_agitators", "1b_strikers_red", "2_canton_support", "3T_shootings", "3M_patriotic_motive",
                               "C_intimidation", "C_labour")]]


def build(gdir: Path):
    g = json.loads((gdir / "graph.json").read_text(encoding="utf-8"))
    anchors = json.loads((gdir / "anchors.json").read_text(encoding="utf-8"))
    claims = [{k: c[k] for k in KEEP} for c in g["claims"]]
    used = {c["cause_event"] for c in claims} | {c["effect_event"] for c in claims}
    events = [{**{k: e[k] for k in ("event", "label", "size", "concept")}, "members": e["members"][:26]} for e in g["events"] if e["event"] in used]
    meta = {"pages": len({c["page"] for c in claims}), "articles": len(g["articles"]),
            "basis": "that yielded claims", "built": time.strftime("%Y-%m-%d %H:%M", time.localtime((gdir / "graph.json").stat().st_mtime))}
    data = json.dumps({"meta": meta, "anchors": anchors, "claims": claims, "events": events}, ensure_ascii=False)
    data = data.replace("</", "<\\/")
    html = (HERE / "viewer_template.html").read_text(encoding="utf-8").replace("__GRAPH_JSON__", data)
    (gdir / "viewer.html").write_text(html, encoding="utf-8")
    print(f"{gdir / 'viewer.html'}: {len(claims)} claims, {len(events)} events, {len(html) / 1e6:.1f} MB")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--all"]:
        dirs = [OUT / "graph"] + sorted(p for p in (OUT / "snapshots").iterdir() if (p / "graph.json").exists())
    else:
        dirs = [Path(a) for a in args] or [OUT / "graph"]
    for d in dirs:
        build(d)
