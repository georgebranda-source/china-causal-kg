import sys,json,re,glob,os,statistics as st,collections,traceback
from pathlib import Path
sb=Path(r'C:\users\georg\documents\projects\china-causal-kg\agent-sandbox'); sys.path.insert(0,str(sb))
import build_articles as b
out=Path(sys.argv[1])/'articles_probe'; out.mkdir(exist_ok=True)
b.OUT_DIR=out; b.render_overlay=lambda *a,**k:None
import builtins; p0=builtins.print; b.print=lambda *a,**k:None
pages=sorted(os.path.basename(p)[:-9] for p in glob.glob(str(sb/'ocr_vl_out'/'page_*NPCM19250[67]*_res.json')))
rows=[];fail=[]
for p in pages:
    try: rows+=b.process(p)
    except Exception as e: fail.append((p,type(e).__name__,str(e)[:80]))
json.dump(rows,open(out/'rows.json','w',encoding='utf-8'),ensure_ascii=False)
n=[r for r in rows if not r['is_ad']]; w=[len(r['text'].split()) for r in n]
print('pages',len(pages),'fail',len(fail),fail[:8])
print('units',len(rows),'news',len(n),'words',sum(w),'median',st.median(w),'p90',sorted(w)[int(.9*len(w))],'max',max(w))
print('>800w',sum(i>800 for i in w),'<25w',sum(i<25 for i in w),'noheadline',sum(1 for r in n if not r['headline']))
print('news/page',len(n)/len(pages))
kw=re.compile(r'strik|boycott|picket|labou?r|coolie|canton|shameen|bolshev|agitat|seamen|union',re.I)
print('news with strike-ish term',sum(bool(kw.search(r['text'])) for r in n))
hd=collections.Counter(re.sub(r'\W+',' ',(r['headline'] or '')).strip().upper()[:40] for r in n)
print(hd.most_common(25))
