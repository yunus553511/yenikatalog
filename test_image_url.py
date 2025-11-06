#!/usr/bin/env python3
"""
Görsel URL'lerini test et
"""
import requests

# Test profil kodları
test_codes = ['LR3101-1', 'LR-3101-1', 'LR3152-A', 'LR-3152-A']

for code in test_codes:
    # Backend URL
    backend_url = f"http://localhost:8001/api/profile-image/{code}"
    
    print(f"\n🔍 Test: {code}")
    print(f"   Backend URL: {backend_url}")
    
    try:
        response = requests.get(backend_url, allow_redirects=False)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 302:
            redirect_url = response.headers.get('Location')
            print(f"   ✅ Redirect: {redirect_url}")
            
            # Supabase URL'ini test et
            supabase_response = requests.head(redirect_url)
            print(f"   Supabase Status: {supabase_response.status_code}")
            
            if supabase_response.status_code == 200:
                print(f"   ✅ Görsel mevcut!")
            else:
                print(f"   ❌ Görsel bulunamadı!")
        else:
            print(f"   ❌ Redirect yok")
            
    except Exception as e:
        print(f"   ❌ Hata: {e}")
