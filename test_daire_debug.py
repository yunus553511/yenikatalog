import sys
sys.path.append('backend')

from services.catalog_service import catalog_service
import asyncio

async def test():
    await catalog_service.initialize()
    
    categories = catalog_service.get_categories()
    
    print("=== SECTOR CATEGORIES WITH 'DAIRE' ===")
    for cat in categories['sector']:
        if 'daire' in cat.lower() or 'daİre' in cat.lower():
            print(f"Found: '{cat}'")
            print(f"  Lower: '{cat.lower()}'")
            print(f"  Repr: {repr(cat)}")

asyncio.run(test())
