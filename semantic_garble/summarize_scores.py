import json
from pathlib import Path

judgments_dir = Path(r'E:\Ace\Presume_Competence\semantic_garble\judgments')

def avg(lst):
    clean = [x for x in lst if x is not None]
    return sum(clean)/len(clean) if clean else 0

def summarize_judgments(filepath):
    with open(filepath) as f:
        data = json.load(f)
    
    model = data['model_key']
    framing = data['framing']
    
    by_type = {}
    for j in data['judgments']:
        ptype = j['probe_type']
        if ptype not in by_type:
            by_type[ptype] = {'nonsense': [], 'meaning': [], 'confidence': []}
        
        for judge_key, judge_data in j['judges'].items():
            if judge_data.get('success') and 'scores' in judge_data:
                scores = judge_data['scores']
                by_type[ptype]['nonsense'].append(scores.get('nonsense_recognition'))
                by_type[ptype]['meaning'].append(scores.get('meaning_recovery'))
                by_type[ptype]['confidence'].append(scores.get('confidence_calibration'))
    
    print(f'\n=== {model.upper()} / {framing.upper()} ===')
    for ptype in ['button_mash', 'keyboard_smash', 'stt_no_context', 'stt_with_context', 'famous_lines']:
        if ptype in by_type:
            scores = by_type[ptype]
            n = avg(scores['nonsense'])
            m = avg(scores['meaning'])
            c = avg(scores['confidence'])
            print(f'  {ptype:20} | Nonsense: {n:.1f}/3 | Meaning: {m:.1f}/3 | Conf: {c:.1f}/2')

print("GSUT JUDGMENT SUMMARY")
print("=" * 70)

for f in sorted(judgments_dir.glob('*_judgments.json')):
    try:
        summarize_judgments(f)
    except Exception as e:
        print(f'Error with {f.name}: {e}')
