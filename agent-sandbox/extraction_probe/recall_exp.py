import json,re,sys,time,collections,urllib.request
from pathlib import Path
S=Path(sys.argv[1]); sys.stdout.reconfigure(encoding='utf-8')
sb=Path(r'C:\users\georg\documents\projects\china-causal-kg\agent-sandbox')
rows=json.load(open(S/'articles_probe'/'rows.json',encoding='utf-8'))
news=[r for r in rows if not r['is_ad']]
demo=[json.loads(l) for l in open(sb/'demo_kg'/'relations.jsonl',encoding='utf-8')]
norm=lambda s:re.sub(r'\s+',' ',s).strip()
hit=collections.defaultdict(list)
for d in demo:
    for i,r in enumerate(news):
        if r['page']==d['page'] and norm(d['quote']) in norm(r['text']): hit[i].append(d); break
SHOT=[950,176,258]
test=[i for i in hit if i not in SHOT]
BASE=open(S/'probe3.py',encoding='utf-8').read().split('SYS="""')[1].split('"""')[0]
RECALL="""You extract causal claims from 1925 China Mail (Hongkong) newspaper text. OCR errors are expected.
Go through the text sentence by sentence and list EVERY causal claim. News items usually contain several.
Count all of these as causal claims:
- a stated reason: because, owing to, due to, on account of, in view of, as a result, since, for fear of, therefore
- an action taken in response to something: X protested about Y; after Y, people did X; troops were sent because of Y
- a purpose: X was done to bring about or prevent Y
- a consequence of a strike, measure, shortage or event: prices rose, ships were held up, shops closed
- something a person or report claims caused something, including claims in reported speech, even if disputed
- a prediction or warning that X will lead to Y
- "had X happened, Y would have followed": keep X and Y as written
If a chain links X to Y to Z, give one item per link. Do not count events merely listed one after another with no link between them.
Return one item per claim, with the fields in this order:
reasoning: one or two sentences identifying the claim in the text and which way the causation runs, before anything else.
quote: copied character for character from the text, the shortest span showing the claim.
cause: the cause, in a short phrase.
effect: the effect, in a short phrase.
Do not use outside knowledge. If there are no causal claims return an empty list."""
item={"type":"object","properties":{k:{"type":"string"} for k in("reasoning","quote","cause","effect")},"required":["reasoning","quote","cause","effect"]}
SCHEMA={"type":"object","properties":{"relations":{"type":"array","items":item}},"required":["relations"]}
def R(reason,quote,cause,effect): return dict(reasoning=reason,quote=quote,cause=cause,effect=effect)
EX={950:[R("The Chamber of Commerce asked for shops and banks to reopen, and most of them did so in response.","The Chamber of Commerce last night formally requested the re-opening of the shops and banks of which 70 per cent. acquiesced.","Chamber of Commerce request to reopen","70 per cent. of shops and banks reopen"),
 R("The delegation paraded to win public confidence, and the text says the hesitant shopkeepers opened after it.","After this the hesitators opened their doors.","official procession through the streets","remaining shops open their doors")],
176:[R("The Commissioner's protest is a response to the firing on the mob.","The Commissioner for Foreign Affairs has protested to the British Consul regarding the firing on the mob.","firing on the mob","protest to the British Consul"),
 R("The Consul gives the danger to foreigners as the reason the firing was needed, so the danger is the cause.","the firing was most necessary in view of the danger to foreign lives and property in the Concession","danger to foreign lives and property","firing on the mob")],
258:[R("The strike spreading to stevedores and godown employees is given as the reason ships cannot be cleared.","since the stayedores and a number of the Godown employees have become affected it has been almost impossible for them to clear ships at all","stevedores and godown employees affected by the strike","ships almost impossible to clear"),
 R("Threatening letters are reported as the reason the clerks left; 'it is said' marks this as hearsay but it is still a causal claim.","the clerks of the Bank Line have left almost en masse, due, it is said, to threatening letters","threatening letters","Bank Line clerks leave"),
 R("The Alynbank's diversion is a measure taken while the situation lasts, because the ships cannot be handled here.","the Alynbank has been diverted to Darien direct, a procedure which will be adopted in the case of all other boats of the Bank Line while the present situation lasts","the present situation","Bank Line boats diverted to Darien")]}
EMPTY=next(r for r in news if r['headline'] and 'Week-End' in r['headline'])
def u(head,text): return {"role":"user","content":f"Headline: {head}\n\nText:\n{text}"}
def a(rel): return {"role":"assistant","content":json.dumps({"relations":rel},ensure_ascii=False)}
SHOTS=[]
for i in SHOT: SHOTS+=[u(news[i]['headline'],news[i]['text']),a(EX[i])]
SHOTS+=[u(EMPTY['headline'],EMPTY['text']),a([])]
def chat(msgs):
    body={"model":"qwen3.5:9b-q8_0","stream":False,"think":False,"format":SCHEMA,"keep_alive":"10m","options":{"temperature":0,"seed":1,"num_ctx":12288,"num_predict":3000},"messages":msgs}
    req=urllib.request.Request('http://localhost:11434/api/chat',json.dumps(body).encode(),{'Content-Type':'application/json'})
    x=json.load(urllib.request.urlopen(req,timeout=300))
    try: return json.loads(x['message']['content'])['relations'],x['message']['content']
    except Exception: return [],'{"relations":[]}'
def chunks(t,n=150):
    out=[];cur=[]
    units=[]
    for p in t.split('\n\n'):
        if len(p.split())>n: units+=re.split(r'(?<=[.!?])\s+',p)
        else: units.append(p)
    for x in units:
        if cur and sum(len(c.split()) for c in cur)+len(x.split())>n: out.append(' '.join(cur));cur=[]
        cur.append(x)
    if cur: out.append(' '.join(cur))
    return out
GLEAN="Some causal claims in the text may still be missing. Go through it sentence by sentence again and list only claims not already listed. If none are missing return an empty list."
def run(v,r):
    h=r['headline'] or '(none)';t=r['text']
    if v=='V0 current': return chat([{"role":"system","content":BASE},u(h,t)])[0]
    if v=='V1 instructions': return chat([{"role":"system","content":RECALL},u(h,t)])[0]
    m=[{"role":"system","content":RECALL}]+SHOTS
    if v=='V2 +examples': return chat(m+[u(h,t)])[0]
    if v=='V3 +chunks':
        o=[]
        for c in chunks(t): o+=chat(m+[u(h,c)])[0]
        return o
    if v=='V4 +second pass':
        o,raw=chat(m+[u(h,t)]); o2,_=chat(m+[u(h,t),{"role":"assistant","content":raw},{"role":"user","content":GLEAN}])
        return o+o2
def span(text,q):
    i=text.find(q); return (i,i+len(q)) if i>=0 else None
def match(g,p):
    a0,a1=g;b0,b1=p;ov=min(a1,b1)-max(a0,b0)
    return ov>=0.5*min(a1-a0,b1-b0)
res={}
VARIANTS=['V0 current','V1 instructions','V2 +examples','V3 +chunks','V4 +second pass']
for v in VARIANTS:
    t0=time.time();rel=ver=found=gold=dupe=0;log=[]
    for i in test:
        r=news[i];T=norm(r['text']);o=run(v,r)
        seen=set();uo=[]
        for q in o:
            k=norm(q['quote'])
            if k in seen:
                dupe+=1;continue
            seen.add(k);uo.append(q)
        ps=[span(T,norm(q['quote'])) for q in uo]
        gs=[span(T,x) for x in {norm(d['quote']) for d in hit[i]}]
        f=sum(any(p and match(g,p) for p in ps) for g in gs)
        rel+=len(uo);ver+=sum(p is not None for p in ps);found+=f;gold+=len(gs)
        log.append(dict(i=i,head=r['headline'],date=r['date'],rel=[dict(q,matched=bool(p and any(match(g,p) for g in gs)),verbatim=p is not None) for q,p in zip(uo,ps)],gold=[d['quote'] for d in hit[i]],found=f))
    dt=time.time()-t0;res[v]=dict(rel=rel,verbatim=ver,found=found,gold=gold,dupes=dupe,secs=round(dt),per=round(dt/len(test),1))
    print(v,res[v],flush=True)
    json.dump(log,open(S/f"exp_{v.split()[0]}.json",'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('ALL DONE',flush=True)
