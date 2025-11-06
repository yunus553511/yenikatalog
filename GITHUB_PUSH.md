# GitHub'a Push Etme Komutları

## Adım 1: GitHub'da repository oluşturduktan sonra

Repository URL'inizi alın (örnek):
```
https://github.com/KULLANICI_ADINIZ/beymetal-chat.git
```

## Adım 2: Bu komutları çalıştırın

```bash
# Remote ekle (URL'i kendi repository URL'iniz ile değiştirin)
git remote add origin https://github.com/KULLANICI_ADINIZ/beymetal-chat.git

# Branch adını main yap
git branch -M main

# Push et
git push -u origin main
```

## Adım 3: Render.com'a Deploy

1. https://render.com adresine git
2. GitHub ile giriş yap
3. **"New +"** → **"Blueprint"** seç
4. **beymetal-chat** repository'sini seç
5. `render.yaml` dosyasını otomatik bulacak
6. **"Apply"** tıkla

## Adım 4: Deploy Tamamlandı!

Render.com size 2 URL verecek:
- **Backend:** https://beymetal-backend.onrender.com
- **Frontend:** https://beymetal-frontend.onrender.com

Frontend URL'ini aç ve test et! 🎉

## Not:
İlk deploy 5-10 dakika sürebilir. Render.com dashboard'dan logs'u izleyebilirsiniz.
