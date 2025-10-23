import asyncio
from services.excel_service import excel_service

async def main():
    await excel_service.initialize()
    
    # K=2.0 olan kutuları bul
    profiles = [p for p in excel_service.get_profiles() 
                if 'KUTU' in p.category 
                and 'K' in p.dimensions 
                and abs(p.dimensions['K'] - 2.0) < 0.1]
    
    print(f"Toplam {len(profiles)} profil bulundu (K=2.0 kutu):\n")
    
    for i, p in enumerate(profiles, 1):
        marker = " <-- YUNUS!" if p.code == 'yunus' else ""
        print(f"{i:2d}. {p.code:15s} K={p.dimensions['K']}{marker}")

asyncio.run(main())
