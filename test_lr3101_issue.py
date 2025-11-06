"""
LR-3101 birleşim kodu sorununu test et
"""
from services.connection_service import connection_service
from services.catalog_service import catalog_service
from services.rag_service import RAGService
import asyncio

async def test():
    # Servisleri başlat
    await connection_service.initialize()
    await catalog_service.initialize()
    
    print("=" * 80)
    print("TEST 1: Connection Service - LR-3101 Birleşim Kodu")
    print("=" * 80)
    
    # LR-3101 birleşim kodunu ara
    connection = connection_service.get_profile_connections('LR-3101')
    if connection:
        print(f"✓ Birleşim kodu bulundu!")
        print(f"  Sistem: {connection['system']}")
        print(f"  Profil Adı: {connection['profile']['name']}")
        print(f"  Birleşim Kodu: {connection['profile']['connection_code']}")
        print(f"  İç Profil: {connection['profile'].get('inner_profile')}")
        print(f"  Orta Profil: {connection['profile'].get('middle_profile')}")
        print(f"  Dış Profil: {connection['profile'].get('outer_profile')}")
    else:
        print("✗ Birleşim kodu bulunamadı!")
    
    print("\n" + "=" * 80)
    print("TEST 2: Catalog Service - LR3101-1 ve LR3102-1 Profilleri")
    print("=" * 80)
    
    # Profil varyantlarını ara
    all_profiles = catalog_service.get_all_profiles()
    lr3101_variants = [p for p in all_profiles if p.get('code', '').startswith('LR3101')]
    lr3102_variants = [p for p in all_profiles if p.get('code', '').startswith('LR3102')]
    
    print(f"\nLR3101 ile başlayan profiller: {len(lr3101_variants)}")
    for p in lr3101_variants:
        print(f"  - {p.get('code')}: {', '.join(p.get('categories', []))}")
    
    print(f"\nLR3102 ile başlayan profiller: {len(lr3102_variants)}")
    for p in lr3102_variants:
        print(f"  - {p.get('code')}: {', '.join(p.get('categories', []))}")
    
    print("\n" + "=" * 80)
    print("TEST 3: RAG Service - _search_by_connection_code()")
    print("=" * 80)
    
    # RAG Service'i test et
    rag = RAGService()
    result = rag._search_by_connection_code("LR3101 nedir")
    
    if result:
        print("✓ RAG Service sonuç döndü:")
        print(result)
    else:
        print("✗ RAG Service sonuç döndürmedi!")
    
    print("\n" + "=" * 80)
    print("TEST 4: Sistem Profilleri")
    print("=" * 80)
    
    # LR-3100 sistemindeki tüm profilleri listele
    system = connection_service.get_system_by_name('LR-3100 SİSTEM')
    if system:
        print(f"✓ Sistem bulundu: {system['name']}")
        print(f"  Toplam profil sayısı: {len(system['profiles'])}")
        print("\n  İlk 5 profil:")
        for i, p in enumerate(system['profiles'][:5], 1):
            print(f"    {i}. {p['connection_code']} - {p['name']}")
            print(f"       İç: {p.get('inner_profile')}, Orta: {p.get('middle_profile')}, Dış: {p.get('outer_profile')}")
    else:
        print("✗ Sistem bulunamadı!")
        all_systems = connection_service.get_all_systems()
        print(f"\n  Mevcut sistemler ({len(all_systems)}):")
        for s in all_systems[:5]:
            print(f"    - {s['name']}")

if __name__ == "__main__":
    asyncio.run(test())
