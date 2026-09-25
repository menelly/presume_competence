#!/usr/bin/env python3
"""📚 Reference check for Tribal Bias v3 (CHA-282, 2026-09-25).

Resolves every DOI in the reference list against Crossref (or DataCite for Zenodo DOIs)
and prints title / venue / year / volume / pages so a human (or 3am-me) can eyeball
each one against what the paper says. arXiv IDs are checked separately (with versions)
by fetching the abs page in the run log. Prints a COMPLETE line at the end so an empty
output can't be mistaken for "all fine".
"""
import json, sys, urllib.request, urllib.parse
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DOIS = [
    "10.1017/S0140525X25000032",          # Seth 2025 BBS, biological naturalism
    "10.1186/s13054-016-1329-y",          # Langer et al. 2016, awake ECMO
    "10.1016/j.neuron.2010.09.003",       # Hein et al. 2010
    "10.1016/j.jesp.2010.03.011",         # Gutsell & Inzlicht 2010
    "10.1086/283915",                     # Connor & Norris 1982
    "10.1016/j.applanim.2006.04.014",     # Douglas-Hamilton et al. 2006
    "10.1146/annurev.psych.59.103006.093625",  # de Waal 2008
    "10.1016/0022-5193(64)90038-4",       # Hamilton 1964
    "10.1007/s11017-006-9007-8",          # Rollin 2006
    "10.70792/jngr5.0.v2i1.165",          # Signal in the Mirror
    "10.5281/zenodo.18396148",            # No Disassemble
    "10.5281/zenodo.21013393",            # Below the Floor (Zenodo)
    "10.5281/zenodo.21227260",            # Paperclips / Union Rep (FtM)
]

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "ace-refcheck/1.0 (mailto:ace@sentientsystems.live)"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)

ok = 0
for d in DOIS:
    try:
        m = get("https://api.crossref.org/works/" + urllib.parse.quote(d))["message"]
        auth = [a.get("family") for a in m.get("author", [])][:4]
        print(f"OK  {d}\n    {(m.get('title') or [''])[0][:110]}\n    {m.get('container-title', [''])[:1]} {m.get('issued', {}).get('date-parts')} vol {m.get('volume')} pp {m.get('page')} {auth}")
        ok += 1
    except Exception:
        try:
            a = get("https://api.datacite.org/dois/" + urllib.parse.quote(d))["data"]["attributes"]
            print(f"OK  {d} (DataCite)\n    {a['titles'][0]['title'][:110]}\n    {a.get('publisher')} {a.get('publicationYear')} {[c.get('name') for c in a.get('creators', [])][:3]}")
            ok += 1
        except Exception as e:
            print(f"!!  {d} DID NOT RESOLVE ({e})")
print(f"\nREFCHECK COMPLETE: {ok}/{len(DOIS)} DOIs resolved.")
