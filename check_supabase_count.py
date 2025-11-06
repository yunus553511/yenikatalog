#!/usr/bin/env python3
"""
Supabase'deki toplam dosya sayısını kontrol et
"""
from supabase import create_client

SUPABASE_URL = "https://aobyiaswancktpscujrp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFvYnlpYXN3YW5ja3Rwc2N1anJwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTkxMzQ1MSwiZXhwIjoyMDc3NDg5NDUxfQ.46f8CLJW3ofkfQLFHqPqBkR__EhIjCoMxoPsD-e6VO8"
BUCKET_NAME = "profile-images"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Tüm dosyaları listele (pagination ile)
all_files = []
offset = 0
limit = 1000

while True:
    files = supabase.storage.from_(BUCKET_NAME).list(
        path="",
        options={"limit": limit, "offset": offset}
    )
    
    if not files:
        break
    
    all_files.extend(files)
    offset += limit
    
    if len(files) < limit:
        break

print(f"📊 Supabase'de toplam {len(all_files)} dosya var")

# LR5220 ile başlayanları kontrol et
lr5220_files = [f for f in all_files if 'LR5220' in f['name']]
print(f"\n🔍 LR5220 ile ilgili dosyalar ({len(lr5220_files)} adet):")
for f in lr5220_files:
    print(f"  - {f['name']}")

# LR3533-A kontrol et
lr3533_files = [f for f in all_files if 'LR3533-A' in f['name']]
print(f"\n🔍 LR3533-A dosyası:")
if lr3533_files:
    print(f"  ✅ Var: {lr3533_files[0]['name']}")
else:
    print(f"  ❌ Yok")
