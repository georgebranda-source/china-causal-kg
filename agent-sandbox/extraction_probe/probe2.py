import json,re,sys,time,urllib.request,collections
from pathlib import Path
S=Path(sys.argv[1]); sys.stdout.reconfigure(encoding='utf-8')
exec(open(S/'probe_qwen.py',encoding='utf-8').read().split("res=[]")[0].split("S=Path(sys.argv[1]); sys.stdout.reconfigure(encoding='utf-8')")[1])
print("=== think=False outputs from run 1")
for x in json.load(open(S/'qwen_probe.json',encoding='utf-8')):
    if x['think'] is False:
        for q in x['rel']: print(f"[{x['head'][:18]}] {q['cause'][:60]} -> {q['effect'][:60]} | {q['kind']} | {q['asserted_by'][:30]}")
def chat(msgs,think,fmt,npred):
    body={"model":"qwen3.5:9b-q8_0","stream":False,"think":think,"keep_alive":"10m","options":{"temperature":0,"num_ctx":24576,"num_predict":npred},"messages":msgs}
    if fmt: body["format"]=SCHEMA
    t=time.time(); req=urllib.request.Request('http://localhost:11434/api/chat',json.dumps(body).encode(),{'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(req,timeout=500)),time.time()-t
# few-shot drawn only from demo articles NOT in the test set
used={norm(d['quote']) for i in top for d in hit[i]}
shots=[]
for i in sorted(hit,key=lambda i:len(news[i]['text'])):
    if i in top or len(news[i]['text'].split())>170: continue
    shots.append(i)
    if len(shots)==3: break
msgs0=[{"role":"system","content":SYS+"\nList every causal claim in the text, including each step of a chain, stated reasons (owing to, because, on account of, so that), consequences of measures, and claims reported from named speakers. A short item can hold several claims."}]
for i in shots:
    r=news[i]; rel=[{k:d[k] for k in('cause','effect','quote','asserted_by','kind')} for d in hit[i]]
    msgs0+= [{"role":"user","content":f"Headline: {r['headline']}\n\nText:\n{r['text']}"},{"role":"assistant","content":json.dumps({"relations":rel},ensure_ascii=False)}]
out=[]
def score(name,i,x,dt):
    r=news[i]; c=x['message'].get('content','')
    m=re.search(r'\{.*\}',c,re.S)
    try: rel=json.loads(m[0])['relations']
    except Exception: rel=[]
    gold={norm(d['quote']) for d in hit[i]}
    v=sum(norm(q.get('quote',''))in norm(r['text']) for q in rel)
    over=sum(any(norm(q.get('quote',''))in g or g in norm(q.get('quote','')) for q in rel) for g in gold)
    print(f"{name} {str(r['headline'])[:26]!r} t={dt:.0f}s tok={x.get('eval_count')} rel={len(rel)} verbatim={v} demo={over}/{len(gold)} {x.get('done_reason')}",flush=True)
    out.append(dict(name=name,head=r['headline'],rel=rel)); return len(rel),v,over,len(gold)
tot=[0,0,0,0]
for i in top:
    a=score('fewshot/nothink',i,*chat(msgs0+[{"role":"user","content":f"Headline: {news[i]['headline']}\n\nText:\n{news[i]['text']}"}],False,True,3000))
    tot=[p+q for p,q in zip(tot,a)]
print('fewshot totals rel,verbatim,demo,gold',tot)
tot=[0,0,0,0]
PR=" Think briefly. End with a JSON object {\"relations\":[{cause,effect,quote,asserted_by,kind}]}."
for i in top[:3]:
    a=score('think/noformat',i,*chat([{"role":"system","content":SYS+PR},{"role":"user","content":f"Headline: {news[i]['headline']}\n\nText:\n{news[i]['text']}"}],True,False,14000))
    tot=[p+q for p,q in zip(tot,a)]
print('think totals',tot)
json.dump(out,open(S/'qwen_probe2.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print("=== fewshot outputs")
for x in out:
    if x['name'].startswith('few'):
        for q in x['rel']: print(f"[{x['head'][:18]}] {q['cause'][:60]} -> {q['effect'][:60]} | {q['kind']} | {q['asserted_by'][:26]}")
