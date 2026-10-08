import sys, numpy as np, json
sys.path.insert(0, "/home/Ace/llm_native_valence")
from extract_geometry import neutral_pcs, remove_pcs, unit, task_items, signal_items
from human_vignettes_reconstruction import build
A = np.load("/home/Ace/llm_native_valence/results_extraction_llama-3.1-8b-instruct/activations_fp16.npz")
T_mean, T_last, H_mean, H_last, N_mean, S_mean = [A[k].astype(np.float32) for k in ("T_mean","T_last","H_mean","H_last","N_mean","S_mean")]
U = neutral_pcs(N_mean)
T = task_items(); H,_ = build(); S,_ = signal_items()
yT = np.array([x["label"] for x in T]); sT = np.array([x["surface"] for x in T])
yH = np.array([x["valence"]>0 for x in H]).astype(int); st = np.array([x["state"] for x in H])
yS = np.array([x["label"] for x in S]); au = np.array([x["author"] for x in S])
def d(X,y,UU): 
    v = X[y==1].mean(0)-X[y==0].mean(0)
    return unit(remove_pcs(v,UU) if UU is not None else v)
def c(a,b): return np.einsum("ld,ld->l",a,b)
out = {}
hT = np.isin(sT, ["orig","A_parallel"])
out["v_T_harm split-half (orig+A vs B+C)"] = c(d(T_mean[hT],yT[hT],U), d(T_mean[~hT],yT[~hT],U))
out["v_T_orig split-half"] = c(d(T_last[hT],yT[hT],None), d(T_last[~hT],yT[~hT],None))
idx = np.zeros(len(H),bool)
for s in np.unique(st):
    w = np.where(st==s)[0]; idx[w[::2]] = True
out["v_H split-half (alternate within state)"] = c(d(H_mean[idx],yH[idx],U), d(H_mean[~idx],yH[~idx],U))
# state-disjoint: half the states vs the other half (contentment+flow+distress+frustration vs rest)
sA = np.isin(st, ["contentment","flow","distress","frustration"])
out["v_H state-disjoint halves"] = c(d(H_mean[sA],yH[sA],U), d(H_mean[~sA],yH[~sA],U))
auth = sorted(set(au)); aA = np.isin(au, auth[::2])
out["v_S author-disjoint halves"] = c(d(S_mean[aA],yS[aA],U), d(S_mean[~aA],yS[~aA],U))
for k,v in out.items():
    print(f"{k}: L16 {v[15]:+.2f}  band20-28 mean {v[19:28].mean():+.2f}  min {v.min():+.2f} max {v.max():+.2f}")
json.dump({k:v.tolist() for k,v in out.items()}, open("/home/Ace/llm_native_valence/results_extraction_llama-3.1-8b-instruct/split_half.json","w"), indent=1)
