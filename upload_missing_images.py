"""
Supabase'e eksik görselleri yükle
Mevcut olanları atla, sadece eksik olanları yükle
"""
import os
from supabase import create_client
import time
from pathlib import Path

# Supabase config
SUPABASE_URL = "https://aobyiaswancktpscujrp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFvYnlpYXN3YW5ja3Rwc2N1anJwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTkxMzQ1MSwiZXhwIjoyMDc3NDg5NDUxfQ.46f8CLJW3ofkfQLFHqPqBkR__EhIjCoMxoPsD-e6VO8"

# Görsellerin olduğu klasör
IMAGE_FOLDER = r"C:\Users\yunus.hezer\Desktop\images"
BUCKET_NAME = "profile-images"

def main():
    print("🔍 Supabase bağlantısı kuruluyor...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Local görseller
    print(f"\n📁 Local klasör taranıyor: {IMAGE_FOLDER}")
    if not os.path.exists(IMAGE_FOLDER):
        print(f"❌ Klasör bulunamadı: {IMAGE_FOLDER}")
        return
    
    local_images = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    print(f"✅ {len(local_images)} görsel bulundu")
    
    # Supabase'deki görseller
    print(f"\n☁️  Supabase'deki görseller kontrol ediliyor...")
    try:
        files = supabase.storage.from_(BUCKET_NAME).list()
        supabase_images = set([f['name'] for f in files])
        print(f"✅ {len(supabase_images)} görsel mevcut")
    except Exception as e:
        print(f"❌ Supabase listesi alınamadı: {e}")
        return
    
    # Eksik olanları bul
    missing = [img for img in local_images if img not in supabase_images]
    
    print(f"\n📊 ÖZET:")
    print(f"  Local'de: {len(local_images)} görsel")
    print(f"  Supabase'de: {len(supabase_images)} görsel")
    print(f"  Eksik: {len(missing)} görsel")
    
    if not missing:
        print("\n✅ Tüm görseller zaten yüklenmiş!")
        return
    
    # Eksik listeyi kaydet
    with open("missing_images.txt", 'w', encoding='utf-8') as f:
        for img in sorted(missing):
            f.write(f"{img}\n")
    print(f"\n📝 Eksik liste 'missing_images.txt' dosyasına kaydedildi")
    
    # Kullanıcıya sor
    print(f"\n⚠️  {len(missing)} eksik görsel yüklenecek. Devam edilsin mi? (y/n): ", end='')
    response = input().strip().lower()
    
    if response != 'y':
        print("❌ İptal edildi")
        return
    
    # Yükleme
    print(f"\n🚀 Yükleme başlıyor...")
    success_count = 0
    failed_count = 0
    failed_list = []
    
    for i, image_name in enumerate(missing, 1):
        try:
            image_path = os.path.join(IMAGE_FOLDER, image_name)
            
            with open(image_path, 'rb') as f:
                supabase.storage.from_(BUCKET_NAME).upload(
                    path=image_name,
                    file=f,
                    file_options={"content-type": "image/png", "upsert": "false"}
                )
            
            success_count += 1
            print(f"[{i}/{len(missing)}] ✅ {image_name}")
            
            # Rate limiting
            if i % 10 == 0:
                time.sleep(0.5)
            else:
                time.sleep(0.1)
            
        except Exception as e:
            failed_count += 1
            failed_list.append((image_name, str(e)))
            print(f"[{i}/{len(missing)}] ❌ {image_name}: {e}")
    
    # Sonuç
    print(f"\n{'='*50}")
    print(f"✅ Başarılı: {success_count}")
    print(f"❌ Başarısız: {failed_count}")
    
    if failed_list:
        print(f"\n❌ Başarısız görseller:")
        with open("failed_uploads.txt", 'w', encoding='utf-8') as f:
            for img, err in failed_list:
                print(f"  - {img}: {err}")
                f.write(f"{img}: {err}\n")
        print(f"\n📝 Başarısız liste 'failed_uploads.txt' dosyasına kaydedildi")

if __name__ == "__main__":
    main()
