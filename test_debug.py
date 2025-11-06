import sys
sys.path.append('backend')

from services.catalog_service import catalog_service
import asyncio

async def test():
    await catalog_service.initialize()
    
    categories = catalog_service.get_categories()
    
    print("=== SECTOR CATEGORIES ===")
    for cat in categories['sector']:
        if 'kutu' in cat.lower() or 'KUTU' in cat:
            print(f"Found: '{cat}' (upper: '{cat.upper()}')")
            print(f"  Equals 'KUTU': {cat.upper() == 'KUTU'}")
            print(f"  Repr: {repr(cat)}")

asyncio.run(test())
