"""Fix encoding issues in metadata file."""
import json
from pathlib import Path

# Load metadata
with open('data/profile_metadata.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Fix file paths
fixed_count = 0
for profile_code, metadata in data['profiles'].items():
    old_path = metadata['file_path']
    # Replace ?? with correct Turkish characters
    new_path = old_path.replace('YEN??', 'YENİ').replace('BENZERL??K', 'BENZERLİK').replace('YEN??PNGLER', 'YENİPNGLER')
    
    if old_path != new_path:
        metadata['file_path'] = new_path
        fixed_count += 1
        if fixed_count <= 5:  # Show first 5 examples
            print(f"Fixed: {profile_code}")
            print(f"  Old: {old_path}")
            print(f"  New: {new_path}")

# Save fixed metadata
with open('data/profile_metadata.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\n✓ Fixed {fixed_count} file paths")
print("✓ Metadata saved with correct encoding")
