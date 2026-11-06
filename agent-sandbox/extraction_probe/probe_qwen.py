import json,re,sys,time,urllib.request,collections
from pathlib import Path
S=Path(sys.argv[1]); sys.stdout.reconfigure(encoding='utf-8')
sb=Path(r'C:\users\georg\documents\projects\china-causal-kg\agent-sandbox')
rows=json.load(open(S/'articles_probe'/'rows.json',encoding='utf-8'))
news=[r for r in rows if not r['is_ad']]
print('fail check: pages in rows',len({r['page'] for r in rows}))
demo=[json.loads(l) for l in open(sb/'demo_kg'/'relations.jsonl',encoding='utf-8')]
norm=lambda s:re.sub(r'\s+',' ',s).strip()
# articles containing the most demo quotes = silver test items
hit=collections.defaultdict(list)
for d in demo:
    for i,r in enumerate(news):
        if r['page']==d['page'] and norm(d['quote']) in norm(r['text']): hit[i].append(d); break
print('demo quotes located inside one article:',sum(map(len,hit.values())),'of',len(demo))
top=sorted(hit,key=lambda i:-len(hit[i]))[:5]
neg=[i for i,r in enumerate(news) if 60<len(r['text'].split())<250 and re.search(r'cricket|racing|tennis|police court|shipping|bowls',r['text'],re.I) and i not in hit][:2]
SYS="""You extract causal claims from 1925 China Mail (Hongkong) newspaper text. OCR errors are expected.
A causal claim: the text states or clearly implies that one event or condition brought about another.
kind: explicit (a causal word such as because, due to, owing to, caused, led to, as a result), implicit (causation clear from context with no causal word), counterfactual (had X happened, Y would have followed).
Rules: quote must be copied character for character from the text, shortest span showing the claim. asserted_by is who makes the claim, not who acts: a named speaker, or "China Mail" if the paper itself reports it. Do not use outside knowledge. If there are no causal claims return an empty list."""
SCHEMA={"type":"object","properties":{"relations":{"type":"array","items":{"type":"object","properties":{"cause":{"type":"string"},"effect":{"type":"string"},"quote":{"type":"string"},"asserted_by":{"type":"string"},"kind":{"type":"string","enum":["explicit","implicit","counterfactual"]}},"required":["cause","effect","quote","asserted_by","kind"]}}},"required":["relations"]}
def call(text,head,think):
    body={"model":"qwen3.5:9b-q8_0","stream":False,"think":think,"format":SCHEMA,"keep_alive":"10m",
      "options":{"temperature":0,"num_ctx":12288,"num_predict":6000},
      "messages":[{"role":"system","content":SYS},{"role":"user","content":f"Headline: {head}\n\nText:\n{text}"}]}
    t=time.time()
    req=urllib.request.Request('http://localhost:11434/api/chat',json.dumps(body).encode(),{'Content-Type':'application/json'})
    r=json.load(urllib.request.urlopen(req,timeout=400)); return r,time.time()-t
res=[]
for think in (False,True):
    tt=0;toks=0;nq=0;ok=0;bad=0
    for i in top+neg:
        r=news[i]; x,dt=call(r['text'],r['headline'] or '(none)',think)
        m=x['message']; tt+=dt; toks+=x.get('eval_count',0)
        try: rel=json.loads(m['content'])['relations']
        except Exception as e: rel=[]; bad+=1
        v=[norm(q['quote']) in norm(r['text']) for q in rel]
        gold={norm(d['quote']) for d in hit.get(i,[])}
        over=sum(any(norm(q['quote'])in g or g in norm(q['quote']) for q in rel) for g in gold)
        nq+=len(rel);ok+=sum(v)
        print(f"think={think} {r['date']} {str(r['headline'])[:34]!r} w={len(r['text'].split())} t={dt:.1f}s tok={x.get('eval_count')} rel={len(rel)} verbatim={sum(v)} demo_found={over}/{len(gold)} done={x.get('done_reason')}")
        res.append(dict(think=think,head=r['headline'],text=r['text'],rel=rel,gold=sorted(gold)))
    print(f"== think={think}: {tt:.0f}s, {toks} tokens, {toks/max(tt,1):.0f} tok/s, rel={nq}, verbatim={ok}, parsefail={bad}")
json.dump(res,open(S/'qwen_probe.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
