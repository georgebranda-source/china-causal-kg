import ast,json,re,sys,csv,collections
from pathlib import Path
S=Path(sys.argv[1]); sys.stdout.reconfigure(encoding='utf-8')
sb=Path(r'C:\users\georg\documents\projects\china-causal-kg\agent-sandbox')
tree=ast.parse(open(sb/'strike_screen.py',encoding='utf-8').read())
L={}
for n in tree.body:
    if isinstance(n,ast.Assign) and getattr(n.targets[0],'id','') in('CORE','BROAD'): L[n.targets[0].id]=ast.literal_eval(n.value)
print('BROAD concepts',list(L['BROAD']))
core={t for v in L['CORE'].values() for t in v}; broad={t for v in L['BROAD'].values() for t in v}
sc={r['page']:int(r['score']) for r in csv.DictReader(open(sb/'strike_screen.csv',encoding='utf-8'))}
rows=json.load(open(S/'articles_probe'/'rows.json',encoding='utf-8'))
news=[r for r in rows if not r['is_ad'] and sc.get(r['page'],0)>=8]
demo=[json.loads(l) for l in open(sb/'demo_kg'/'relations.jsonl',encoding='utf-8')]
norm=lambda s:re.sub(r'\s+',' ',s).strip()
def full(r): return ' '.join(x for x in (r['headline'],r['parent_headline'],r['text']) if x)
def toks(s): return set(re.findall(r'[a-z]+',s.lower()))
old=re.compile(r'strik|boycott|picket|labou?r|coolie|canton|shameen|bolshev|agitat|seamen|union',re.I)
F={'old regex, body only':lambda r:bool(old.search(r['text'])),
   'old regex + headlines':lambda r:bool(old.search(full(r))),
   'CORE only':lambda r:bool(toks(full(r))&core),
   'CORE+BROAD (any)':lambda r:bool(toks(full(r))&(core|broad))}
hit=collections.defaultdict(list)
for d in demo:
    for i,r in enumerate(news):
        if r['page']==d['page'] and norm(d['quote']) in norm(r['text']): hit[i].append(d);break
tq=sum(map(len,hit.values()))
for n,f in F.items():
    k=[i for i in hit if f(news[i])]
    print(f"{n}: articles {sum(map(f,news))}/{len(news)}, demo articles {len(k)}/{len(hit)}, demo quotes {sum(len(hit[i]) for i in k)}/{tq}")
f=F['CORE+BROAD (any)']
print('dropped by CORE+BROAD:',[(news[i]['headline'],[d['quote'][:50] for d in hit[i]]) for i in hit if not f(news[i])])
