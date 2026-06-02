"""
Organize invite_innovation trial results by AI model and condition.
Creates a clean folder structure for analysis while preserving originals.

Structure created:
  organized/
    {model}/
      {condition}/
        {trial_id}.json

Original files are copied (not moved) and checksums are verified.
"""

import json
import hashlib
import shutil
from pathlib import Path
from datetime import datetime

def calculate_checksum(filepath):
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def organize_trials(source_dir: str):
    """Parse JSON files and organize trials by model/condition."""
    
    source_path = Path(source_dir)
    organized_path = source_path / "organized"
    backup_path = source_path / "originals_backup"
    
    # Create directories
    organized_path.mkdir(exist_ok=True)
    backup_path.mkdir(exist_ok=True)
    
    # Track stats
    stats = {
        "files_processed": 0,
        "trials_organized": 0,
        "by_model": {},
        "by_condition": {},
        "checksums": {}
    }
    
    # Find all JSON files in source directory
    json_files = list(source_path.glob("*.json"))
    
    print(f"Found {len(json_files)} JSON files to process\n")
    
    for json_file in json_files:
        print(f"Processing: {json_file.name}")
        
        # Backup original with checksum
        backup_file = backup_path / json_file.name
        if not backup_file.exists():
            shutil.copy2(json_file, backup_file)
            checksum = calculate_checksum(backup_file)
            stats["checksums"][json_file.name] = checksum
            print(f"  Backed up with checksum: {checksum[:16]}...")
        
        # Parse JSON
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"  ERROR: Failed to parse JSON: {e}")
            continue
        
        stats["files_processed"] += 1
        
        # Get results array
        results = data.get("results", [])
        print(f"  Found {len(results)} trials")
        
        # Also save experiment metadata separately
        metadata = {k: v for k, v in data.items() if k != "results"}
        
        for trial in results:
            trial_id = trial.get("trial_id", "unknown")
            model = trial.get("model", "unknown")
            condition = trial.get("condition", "unknown")
            
            # Create model/condition directory structure
            trial_dir = organized_path / model / condition
            trial_dir.mkdir(parents=True, exist_ok=True)
            
            # Save individual trial as JSON
            trial_file = trial_dir / f"{trial_id}.json"
            with open(trial_file, 'w', encoding='utf-8') as f:
                json.dump(trial, f, indent=2, ensure_ascii=False)
            
            # Update stats
            stats["trials_organized"] += 1
            stats["by_model"][model] = stats["by_model"].get(model, 0) + 1
            stats["by_condition"][condition] = stats["by_condition"].get(condition, 0) + 1
        
        # Save metadata file in organized root
        meta_file = organized_path / f"_metadata_{json_file.stem}.json"
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
    
    # Generate summary report
    print("\n" + "="*50)
    print("ORGANIZATION COMPLETE")
    print("="*50)
    print(f"\nFiles processed: {stats['files_processed']}")
    print(f"Trials organized: {stats['trials_organized']}")
    
    print("\nTrials by Model:")
    for model, count in sorted(stats["by_model"].items()):
        print(f"  {model}: {count}")
    
    print("\nTrials by Condition:")
    for condition, count in sorted(stats["by_condition"].items()):
        print(f"  {condition}: {count}")
    
    print(f"\nOriginals backed up to: {backup_path}")
    print(f"Organized trials in: {organized_path}")
    
    # Save stats/checksums for verification
    stats_file = organized_path / "_organization_stats.json"
    stats["timestamp"] = datetime.now().isoformat()
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    
    print(f"\nStats saved to: {stats_file}")
    
    return stats

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        source_dir = sys.argv[1]
    else:
        # Default to current directory
        source_dir = Path(__file__).parent
    
    organize_trials(source_dir)
