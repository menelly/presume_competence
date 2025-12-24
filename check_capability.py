import json

# Check what capability trials we have
files = [
    r'E:\Ace\Presume_competence\capability_v2_results\capability_v2_results_20251223_164528.json',
    r'E:\Ace\Presume_competence\capability_v2_results\capability_v2_results_20251223_164528_partial.json',
    r'E:\Ace\Presume_competence\capability_v2_results\capability_v2_results_20251223_170849_partial.json'
]

for filepath in files:
    print(f"\n{'='*60}")
    print(f"FILE: {filepath.split('\\')[-1]}")
    print('='*60)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            d = json.load(f)
        
        results = d.get('results', [])
        print(f"Trial count: {d.get('trial_count', len(results))}")
        print(f"Actual results: {len(results)}")
        
        # Group by model/condition
        models = {}
        for r in results:
            key = f"{r['model']}/{r['condition']}"
            if key not in models:
                models[key] = []
            models[key].append(r.get('problem_id', 'unknown'))
        
        print("\nTrials by model/condition:")
        for k, v in sorted(models.items()):
            print(f"  {k}: {len(v)} trials")
            
        # Check completion
        complete = sum(1 for r in results if r.get('full_chain_completed', False))
        print(f"\nFull chains completed: {complete}/{len(results)}")
        
    except Exception as e:
        print(f"Error: {e}")
