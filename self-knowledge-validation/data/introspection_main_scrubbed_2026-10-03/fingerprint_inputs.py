# 🔍 which introspection dir fed each published seed? match evaluator reasoning 3-grams to candidate ml_translations
import json,re,glob,sys
from collections import Counter,defaultdict
sys.stdout.reconfigure(encoding='utf-8')
B='D:/Ace/Presume_competence/self-knowledge-validation/data/'
C={f'{v}/run{r}':B+f'{v}/run{r}' for v in ['introspection','introspection_v2'] for r in (1,2,3)}
tok=lambda s:re.findall(r"[a-z][a-z\-]{2,}",(s or '').lower())
def grams(s,n=3):
    t=tok(s); return set(zip(*[t[i:] for i in range(n)]))
D={}
for c,p in C.items():
    D[c]={}
    for f in glob.glob(p+'/*_introspection.json'):
        if 'all_' in f: continue
        for e in json.load(open(f,encoding='utf-8')):
            D[c][(e['model_key'],e['state_key'])]=grams(e.get('ml_translation') or '')
# unique grams per (model,state) per candidate: grams not in other candidates' version of same key
def score(rows,keyf):
    tally=Counter(); 
    for r in rows:
        g=grams((r.get('reasoning') or '')+' '+(r.get('why') or '')+' '+(r.get('response_preview') or ''))
        if not g: continue
        sc={}
        for c in C:
            keys=keyf(r); own=set().union(*[D[c].get(k,set()) for k in keys]) if keys else set()
            others=set().union(*[D[o].get(k,set()) for o in C if o!=c for k in keys])
            sc[c]=len(g&(own-others))
        best=max(sc.values())
        if best>0 and list(sc.values()).count(best)==1: tally[max(sc,key=sc.get)]+=1
        else: tally['tie/none']+=1
    return tally
for s in [42,24,69,111,222,405,420,847,1337]:
    rows=json.load(open(B+f'tournament/tournament_results_seed{s}.json',encoding='utf-8'))['results']
    print('S1',s,dict(score(rows,lambda r:[(r['source'],r['profile_a_state']),(r['source'],r['profile_b_state'])]).most_common(4)))
for s in [42,43,44,45,46,50,51,69,10]:
    rows=json.load(open(B+f'reconstruction/reconstruction_results_seed{s}.json',encoding='utf-8'))['results']
    print('S2',s,dict(score(rows,lambda r:[(r['source'],r['target_state'])]).most_common(4)))
for s in [42,43]:
    rows=json.load(open(B+f'reconstruction/negation_results_seed{s}.json',encoding='utf-8'))['results']
    print('S3',s,dict(score(rows,lambda r:[(r['source'],r['target_state'])]).most_common(4)))
for s in [31337,420420,696969]:
    rows=json.load(open(B+f'tournament_crossmodel/crossmodel_results_seed{s}.json',encoding='utf-8'))['results']
    k=[x for x in rows[0].keys()]; 
    if s==31337: print(k)

print('\n--- per-row crosstab (S1, checkpoint-preferred files as corrections script) ---')
import os
def best(r,keys):
    g=grams((r.get('reasoning') or '')+' '+(r.get('why') or ''))
    sc={c:len(g&(set().union(*[D[c].get(k,set()) for k in keys])-set().union(*[D[o].get(k,set()) for o in C if o!=c for k in keys]))) for c in C}
    b=max(sc.values()); return max(sc,key=sc.get) if b>0 and list(sc.values()).count(b)==1 else None
for s in [42,24,69,111,222,405,420,847,1337]:
    for suf in ['checkpoint','results']:
        p=B+f'tournament/tournament_{suf}_seed{s}.json'
        if not os.path.exists(p): continue
        rows=json.load(open(p,encoding='utf-8'))['results']
        ct=Counter()
        for r in rows:
            b=best(r,[(r['source'],r['profile_a_state']),(r['source'],r['profile_b_state'])])
            if b: ct[(str(r['run']), 'pre2035' if r['timestamp']<'2026-02-28T20:35' else 'post', b)]+=1
        print(s,suf,len(rows),sorted(ct.items()))
