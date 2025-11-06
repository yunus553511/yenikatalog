# Design Document

## Overview

Sidebar'ın üst kısmındaki boşluk alanında mouse tıklamalarının yanlış davranmasını düzeltmek için CSS padding/margin yapısını yeniden düzenleyeceğiz. Sorun, `.systems-content` container'ının `padding-top: 0` olması ve ilk sistem öğesinin `margin-top: 0.75rem` ile aşağı itilmesinden kaynaklanıyor. Bu, üstte tıklanabilir ama görünmeyen bir alan yaratıyor.

## Architecture

### Mevcut Durum

```css
.systems-content {
    padding: 0.75rem;
    padding-top: 0;  /* Üst padding yok */
}

.system-item:first-child {
    margin-top: 0.75rem;  /* İlk öğe aşağı itilmiş */
}
```

Bu yapı şu soruna yol açıyor:
- `.systems-content` div'i üstte 0.75rem boşluk içeriyor (görünmez)
- Bu boşluk tıklanabilir ama içinde hiçbir element yok
- Mouse bu alana tıkladığında, event yanlış yere gidiyor

### Hedef Durum

```css
.systems-content {
    padding: 0.75rem;  /* Tüm yönlerde eşit padding */
}

.system-item:first-child {
    margin-top: 0;  /* İlk öğe için ekstra margin yok */
}
```

## Components and Interfaces

### Etkilenen CSS Sınıfları

1. `.systems-content` - Ana container
2. `.system-item:first-child` - İlk sistem öğesi
3. `.system-item:last-child` - Son sistem öğesi

### Değişiklikler

**1. systems-content padding düzeltmesi:**
- `padding-top: 0` satırını kaldır
- Tüm yönlerde `padding: 0.75rem` kullan

**2. system-item margin düzeltmesi:**
- `margin-top: 0.75rem` satırını `margin-top: 0` yap
- `margin-bottom: 0.75rem` satırını `margin-bottom: 0` yap (çünkü gap ile yönetiliyor)

**3. Alternatif çözüm (pointer-events):**
Eğer padding yapısını korumak istersek:
```css
.systems-content::before {
    content: '';
    display: block;
    height: 0.75rem;
    pointer-events: none;
}
```

## Data Models

N/A - Sadece CSS değişiklikleri

## Error Handling

- Tarayıcı uyumluluğu için standart CSS özellikleri kullanılacak
- Responsive breakpoint'lerde aynı mantık korunacak

## Testing Strategy

### Manuel Test Senaryoları

1. **Üst boşluk tıklama testi:**
   - Sidebar'ın en üst kısmındaki boşluğa tıkla
   - Hiçbir şey olmamalı veya doğru element seçilmeli

2. **İlk öğe tıklama testi:**
   - İlk sistem öğesine tıkla
   - Doğru sistem seçilmeli

3. **Scroll testi:**
   - Sidebar'ı scroll et
   - Sticky positioning çalışmalı

4. **Responsive testi:**
   - Mobil ve tablet görünümlerinde test et
   - Layout bozulmamalı

### Tarayıcı Uyumluluğu

- Chrome/Edge (Chromium)
- Firefox
- Safari
- Mobile browsers

## Implementation Notes

**Tercih edilen çözüm:** Padding yapısını düzeltmek (daha temiz ve sürdürülebilir)

**Alternatif çözüm:** pointer-events kullanmak (hızlı fix ama ideal değil)

Padding yapısını düzeltmek daha iyi çünkü:
- Daha temiz CSS
- Daha kolay bakım
- Beklenmedik yan etkiler yok
- Semantik olarak doğru
