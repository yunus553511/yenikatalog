#!/usr/bin/env python3
"""
Eksik sistem görsellerini yükle
"""
import os
from supabase import create_client

SUPABASE_URL = "https://aobyiaswancktpscujrp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFvYnlpYXN3YW5ja3Rwc2N1anJwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTkxMzQ1MSwiZXhwIjoyMDc3NDg5NDUxfQ.46f8CLJW3ofkfQLFHqPqBkR__EhIjCoMxoPsD-e6VO8"
BUCKET_NAME = "profile-images"

# Görsellerin olduğu klasör
IMAGE_FOLDER = r"C:\Users\yunus.hezer\Desktop\images"

# Eksik dosyalar
missing_files = [
    "LR3152-A.png",
    "LR3152-B.png",
    "LR3153.png",
    "LR3155.png",
    "LR3156.png",
    "LR3151.png"
]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print(f"📁 Klasör: {IMAGE_FOLDER}")
print(f"🎯 {len(missing_files)} dosya yüklenecek\n")

success_count = 0
failed = []

for filename in missing_files:
    image_path = os.path.join(IMAGE_FOLDER, filename)
    
    if not os.path.exists(image_path):
        print(f"❌ {filename}: Dosya bulunamadı")
        failed.append((filename, "Dosya bulunamadı"))
        continue
    
    try:
        with open(image_path, 'rb') as f:
            supabase.storage.from_(BUCKET_NAME).upload(
                path=filename,
                file=f,
                file_options={"content-type": "image/png", "upsert": "false"}
            )
        
        success_count += 1
        print(f"✅ {filename}")
        
    except Exception as e:
        error_msg = str(e)
        failed.append((filename, error_msg))
        print(f"❌ {filename}: {error_msg}")

print(f"\n{'='*50}")
print(f"✅ Başarılı: {success_count}")
print(f"❌ Başarısız: {len(failed)}")

if failed:
    print(f"\n❌ Başarısız dosyalar:")
    for filename, error in failed:
        print(f"  {filename}: {error}")
