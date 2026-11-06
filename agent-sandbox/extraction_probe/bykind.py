import json,re,sys,glob,collections
from pathlib import Path
S=Path(sys.argv[1]); sys.stdout.reconfigure(encoding='utf-8')
sb=Path(r'C:\users\georg\documents\projects\china-causal-kg\agent-sandbox')
rows=json.load(open(S/'articles_probe'/'rows.json',encoding='utf-8'))
news=[r for r in rows if not r['is_ad']]
demo=[json.loads(l) for l in open(sb/'demo_kg'/'relations.jsonl',encoding='utf-8')]
norm=lambda s:re.sub(r'\s+',' ',s).strip()
cue=re.compile(r"\b(because|owing to|due to|on account of|in view of|as a result|result(ed|s|ing)?|caus(e|ed|es|ing)|led to|lead to|leads to|therefore|consequen|in consequence|for fear|through|since|so that|in order to|by reason of|brought about|thanks to|forced|compelled|prevent)",re.I)
def span(t,q):
    i=t.find(q);return (i,i+len(q)) if i>=0 else None
def m(g,p):
    return min(g[1],p[1])-max(g[0],p[0])>=0.5*min(g[1]-g[0],p[1]-p[0])
kinds={}
for d in demo: kinds[(d['page'],norm(d['quote']))]=d['kind']
tot=None
for f in sorted(glob.glob(str(S/'exp_V*.json'))):
    L=json.load(open(f,encoding='utf-8'));c=collections.Counter();n=collections.Counter();miss=[]
    for a in L:
        r=news[a['i']];T=norm(r['text'])
        ps=[span(T,norm(q['quote'])) for q in a['rel']]
        for gq in {norm(x) for x in a['gold']}:
            k=kinds[(r['page'],gq)];g=span(T,gq);ok=any(p and m(g,p) for p in ps)
            lab=[k]+(['explicit+cue'] if k=='explicit' and cue.search(gq) else [])+(['explicit no cue'] if k=='explicit' and not cue.search(gq) else [])
            for x in lab:
                n[x]+=1;c[x]+=ok
            if not ok and k=='explicit' and cue.search(gq): miss.append(gq[:95])
    print(Path(f).stem,{x:f"{c[x]}/{n[x]}" for x in('explicit','explicit+cue','explicit no cue','implicit','counterfactual')})
    if 'V0' in f: print(' V0 missed with cue (sample):',*miss[:8],sep='\n   ')
