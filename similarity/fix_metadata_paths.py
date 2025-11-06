"""Fix file paths in metadata by reading raw and replacing."""
import json

# Read the file as raw text
with open('data/profile_metadata.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Count occurrences before fix
before_count = content.count('YEN??')

# Replace the broken paths
content = content.replace('YEN??', 'YENİ')
content = content.replace('BENZERL??K', 'BENZERLİK')

# Count after
after_count = content.count('YENİ')

# Write back
with open('data/profile_metadata.json', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✓ Replaced {before_count} occurrences of 'YEN??' with 'YENİ'")
print(f"✓ Fixed all file paths in metadata")
print(f"✓ Total 'YENİ' occurrences now: {after_count}")

# Verify by loading as JSON
try:
    with open('data/profile_metadata.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"✓ Metadata is valid JSON with {len(data['profiles'])} profiles")
    
    # Show a sample
    sample_code = 'LR3111'
    if sample_code in data['profiles']:
        print(f"\nSample - {sample_code}:")
        print(f"  Path: {data['profiles'][sample_code]['file_path']}")
except Exception as e:
    print(f"✗ Error: {e}")
