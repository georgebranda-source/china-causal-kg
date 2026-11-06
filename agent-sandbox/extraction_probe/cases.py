import json,re,sys,csv
from pathlib import Path
S=Path(sys.argv[1]); sys.stdout.reconfigure(encoding='utf-8')
sb=Path(r'C:\users\georg\documents\projects\china-causal-kg\agent-sandbox')
sc={r['page']:int(r['score']) for r in csv.DictReader(open(sb/'strike_screen.csv',encoding='utf-8'))}
rows=[r for r in json.load(open(S/'articles_probe'/'rows.json',encoding='utf-8')) if not r['is_ad'] and sc.get(r['page'],0)>=8]
kw=re.compile(r'strik|boycott|picket|labou?r|coolie|canton|shameen|bolshev|agitat|seamen|union',re.I)
sents=[]
for r in rows:
    if not kw.search(r['text']): continue
    for s in re.split(r'(?<=[.!?])\s+',re.sub(r'\s+',' ',r['text'])):
        if 8<=len(s.split())<=42: sents.append((r['date'],str(r['headline'])[:24],s))
P={'prevent/force verb':r'\b(prevented|compelled|forced|obliged|paralysed|crippled|drove)\b',
'prediction':r'\b(will|would|must|bound to|likely to)\b.{0,40}\b(lead to|result in|cause|mean|bring about)\b',
'denial':r'\b(not due to|not caused|no connection|nothing to do with|not the result|has not been caused|not because|deny|denied that)\b',
'anaphora':r'^(This|That|These|It)\b.{0,50}\b(due to|owing to|result|caused|consequence|because)\b',
'effect-first noun':r'\b(as a result of|in consequence of|the result of|the cause of|the reason for|the outcome of)\b',
'conditional':r'^(If|Unless|Should)\b.{0,90}\b(will|would)\b'}
for k,p in P.items():
    m=[x for x in sents if re.search(p,x[2],re.I)]
    print(f'## {k}: {len(m)}')
    for d,h,s in m[:9]: print(f'  {d} [{h}] {s}')
