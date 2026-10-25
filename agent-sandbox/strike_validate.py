import json, re, glob
from pathlib import Path
STRONG = re.compile(r"strik|walk-?out|walked out|boycott|picket|lock-?out|general strike", re.I)
WIDE = re.compile(r"strik|walk-?out|boycott|picket|lock-?out|labou?r|workers|coolie|union|wages|unemploy|agitat", re.I)
print("page  libchars lib_strong | paddle_chars paddle_strong paddle_wide  lib_text_head")
for f in sorted(glob.glob("agent-sandbox/ocr_vl_out/page_*NPCM*[0-9].md")):
    stem = Path(f).stem; ed = stem.split("_")[2]; pg = int(stem.split("_")[1])
    m = json.load(open(glob.glob(f"data/raw/hkpl/china_mail_june_july_1925/{ed}*/metadata.json")[0], encoding="utf-8"))
    lib = next((p["ocrContent"] or "" for p in m["ocrList"] if p["sequence"] == pg), None)
    t = open(f, encoding="utf-8").read()
    print(f"{ed[-4:]} p{pg:<2} {('-' if lib is None else len(lib)):>6} {('-' if lib is None else len(STRONG.findall(lib))):>4} | {len(t):>6} {len(STRONG.findall(t)):>4} {len(WIDE.findall(t)):>4}  {(lib or '')[:50]!r}")
