import json,re,sys,time,csv,os,statistics as st,urllib.request,collections
from pathlib import Path
S=Path(sys.argv[1]); sys.stdout.reconfigure(encoding='utf-8')
sb=Path(r'C:\users\georg\documents\projects\china-causal-kg\agent-sandbox')
sc={r['page']:int(r['score']) for r in csv.DictReader(open(sb/'strike_screen.csv',encoding='utf-8'))}
p8=[p for p,s in sc.items() if s>=8]
vl=[p for p in p8 if (sb/'ocr_vl_out'/f'{p}_res.json').exists()]
print('scored',len(sc),'>=8',len(p8),'with VL res',len(vl))
rows=json.load(open(S/'articles_probe'/'rows.json',encoding='utf-8'))
news=[r for r in rows if not r['is_ad']]
n8=[r for r in news if r['page'] in set(p8)]
w=[len(r['text'].split()) for r in n8]
print('pages with rows',len({r['page'] for r in n8}),'news units',len(n8),'words',sum(w),'median',st.median(w),'p90',sorted(w)[int(.9*len(w))],'max',max(w),'>800',sum(i>800 for i in w),'<25',sum(i<25 for i in w),'nohead',sum(not r['headline'] for r in n8))
kw=re.compile(r'strik|boycott|picket|labou?r|coolie|canton|shameen|bolshev|agitat|seamen|union',re.I)
print('with strike term',sum(bool(kw.search(r['text'])) for r in n8))
print('0626 pages >=8',sorted(p for p in p8 if '19250626' in p),'crash pages',{p:sc.get(p) for p in('page_008_NPCM19250602_01_0008','page_012_NPCM19250603_01_0012')})
print('by month',collections.Counter(p.split('NPCM')[1][:6] for p in p8))
demo=[json.loads(l) for l in open(sb/'demo_kg'/'relations.jsonl',encoding='utf-8')]
norm=lambda s:re.sub(r'\s+',' ',s).strip()
hit=collections.defaultdict(list)
for d in demo:
    for i,r in enumerate(news):
        if r['page']==d['page'] and norm(d['quote']) in norm(r['text']): hit[i].append(d); break
top=sorted(hit,key=lambda i:-len(hit[i]))[:5]
SYS="""You extract causal claims from 1925 China Mail (Hongkong) newspaper text. OCR errors are expected.
A causal claim: the text states or clearly implies that one event or condition brought about another.
Return one item per claim, with the fields in this order:
reasoning: one or two sentences identifying the claim in the text and which way the causation runs, before anything else.
quote: copied character for character from the text, the shortest span showing the claim.
cause: the cause, in a short phrase.
effect: the effect, in a short phrase.
For "had X happened, Y would have followed", keep X and Y as written. Do not use outside knowledge. If there are no causal claims return an empty list."""
item={"type":"object","properties":{k:{"type":"string"} for k in("reasoning","quote","cause","effect")},"required":["reasoning","quote","cause","effect"]}
SCHEMA={"type":"object","properties":{"relations":{"type":"array","items":item}},"required":["relations"]}
def call(i):
    r=news[i]
    body={"model":"qwen3.5:9b-q8_0","stream":False,"think":False,"format":SCHEMA,"keep_alive":"5m","options":{"temperature":0,"seed":1,"num_ctx":12288,"num_predict":3000},
      "messages":[{"role":"system","content":SYS},{"role":"user","content":f"Headline: {r['headline']}\n\nText:\n{r['text']}"}]}
    t=time.time();req=urllib.request.Request('http://localhost:11434/api/chat',json.dumps(body).encode(),{'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(req,timeout=300)),time.time()-t
call(top[0]) # warm-up load
tot=collections.Counter();out=[];order=collections.Counter()
for i in top:
    x,dt=call(i);r=news[i];c=x['message']['content'];rel=json.loads(c)['relations']
    for q in rel: order[tuple(q.keys())]+=1
    gold={norm(d['quote']) for d in hit[i]}
    v=sum(norm(q['quote'])in norm(r['text']) for q in rel)
    o=sum(any(norm(q['quote'])in g or g in norm(q['quote']) for q in rel) for g in gold)
    tot.update(rel=len(rel),verb=v,demo=o,gold=len(gold),t=dt,tok=x['eval_count'])
    print(f"{str(r['headline'])[:26]!r} t={dt:.1f}s tok={x['eval_count']} rel={len(rel)} verbatim={v} demo={o}/{len(gold)} {x['done_reason']}",flush=True)
    out.append(dict(head=r['headline'],rel=rel))
print(dict(tot));print('key orders',order)
json.dump(out,open(S/'qwen_probe3.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
for x in out:
    for q in x['rel']: print(f"[{x['head'][:14]}] R: {q['reasoning'][:110]} || {q['cause'][:48]} -> {q['effect'][:48]}")
