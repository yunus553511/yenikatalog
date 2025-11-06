#!/usr/bin/env python3
"""
Sistem profillerinin görsellerini kontrol et
"""
from supabase import create_client
import json

SUPABASE_URL = "https://aobyiaswancktpscujrp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFvYnlpYXN3YW5ja3Rwc2N1anJwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTkxMzQ1MSwiZXhwIjoyMDc3NDg5NDUxfQ.46f8CLJW3ofkfQLFHqPqBkR__EhIjCoMxoPsD-e6VO8"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Tüm dosyaları al
print("📥 Supabase'den dosyalar alınıyor...")
all_files = []
offset = 0
limit = 1000

while True:
    files = supabase.storage.from_("profile-images").list(
        path="",
        options={"limit": limit, "offset": offset}
    )
    
    if not files:
        break
    
    all_files.extend(files)
    offset += limit
    
    if len(files) < limit:
        break

print(f"✅ Toplam {len(all_files)} dosya bulundu")

# Dosya adlarını set'e çevir (hızlı arama için)
file_names = {f['name'].replace('.png', '') for f in all_files}

# Sistem profillerini kontrol et
print("\n🔍 LR-3100 Sistem profilleri kontrol ediliyor...")

system_profiles = [
    "LR3101-1",
    "LR-3102-1",
    "LR3152-A",
    "LR3152-B",
    "LR-3153",
    "LR-3154",
    "LR3155",
    "LR-3156",
    "LR-3151"
]

missing = []
found = []

for profile in system_profiles:
    # Tire varsa kaldır
    normalized = profile
    if profile.startswith('LR-'):
        normalized = profile[:2] + profile[3:]
    
    if normalized in file_names:
        found.append(f"✅ {profile} → {normalized}.png")
    else:
        missing.append(f"❌ {profile} → {normalized}.png BULUNAMADI")

print("\n📊 Sonuçlar:")
print(f"✅ Bulunan: {len(found)}")
print(f"❌ Eksik: {len(missing)}")

if found:
    print("\n✅ Bulunan dosyalar:")
    for f in found:
        print(f"  {f}")

if missing:
    print("\n❌ Eksik dosyalar:")
    for m in missing:
        print(f"  {m}")
