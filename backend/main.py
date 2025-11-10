from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio

from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def auto_refresh_task():
    """Background task to refresh data every 10 minutes"""
    from services.excel_service import excel_service
    from services.embedding_service import embedding_service
    
    while True:
        try:
            # 10 dakika bekle
            await asyncio.sleep(600)  # 600 saniye = 10 dakika
            
            logger.info("🔄 Otomatik yenileme başlıyor...")
            
            # Excel'i yeniden indir
            success = await excel_service.refresh_data()
            
            if success:
                # Embedding'leri yeniden oluştur
                profiles = excel_service.get_profiles()
                emb_success = await embedding_service.initialize(profiles)
                
                if emb_success:
                    stats = excel_service.get_stats()
                    logger.info(f"✅ Otomatik yenileme tamamlandı: {stats['total_profiles']} profil")
                else:
                    logger.error("❌ Embedding yenileme başarısız")
            else:
                logger.error("❌ Excel yenileme başarısız")
                
        except Exception as e:
            logger.error(f"❌ Otomatik yenileme hatası: {e}")


async def auto_refresh_catalog_task():
    """Background task to refresh catalog every 10 minutes"""
    from services.catalog_service import catalog_service
    
    while True:
        try:
            await asyncio.sleep(600)  # 10 dakika
            logger.info("🔄 Katalog otomatik yenileniyor...")
            success = await catalog_service.initialize()
            if success:
                logger.info("✅ Katalog yenileme tamamlandı")
            else:
                logger.error("❌ Katalog yenileme başarısız")
        except Exception as e:
            logger.error(f"❌ Katalog yenileme hatası: {e}")


async def initialize_services_background():
    """Background task to initialize all services"""
    from services.excel_service import excel_service
    from services.embedding_service import embedding_service
    from services.catalog_service import catalog_service
    from services.image_service import image_service
    from services.connection_service import connection_service
    from services.rag_service import rag_service
    from services.llm_service import LLMService
    import services.llm_service as llm_module
    from services.similarity_service import similarity_service
    
    try:
        logger.info("🚀 Background initialization starting...")
        
        # Initialize Excel service (standart profiller)
        success = await excel_service.initialize()
        if not success:
            logger.error("Excel servisi başlatılamadı!")
        else:
            stats = excel_service.get_stats()
            logger.info(f"✅ Excel servisi hazır: {stats['total_profiles']} profil")
            
            # Initialize Embedding service
            profiles = excel_service.get_profiles()
            emb_success = await embedding_service.initialize(profiles)
            
            if emb_success:
                logger.info("✅ Embedding servisi hazır")
            else:
                logger.error("❌ Embedding servisi başlatılamadı!")
        
        # Initialize Catalog service (tüm profiller)
        catalog_success = await catalog_service.initialize()
        if catalog_success:
            cat_stats = catalog_service.get_stats()
            logger.info(f"✅ Katalog servisi hazır: {cat_stats['total_profiles']} profil")
        else:
            logger.error("❌ Katalog servisi başlatılamadı!")
        
        # Initialize Image service (profil görselleri)
        image_success = await image_service.initialize()
        if image_success:
            logger.info("✅ Image servisi hazır")
        else:
            logger.warning("⚠️ Image servisi başlatılamadı")
        
        # Initialize Connection service (profil birleşim sistemleri)
        try:
            await connection_service.initialize()
            conn_data = connection_service.get_all_systems()
            logger.info(f"✅ Connection servisi hazır: {len(conn_data)} sistem")
        except Exception as e:
            logger.error(f"❌ Connection servisi başlatılamadı: {e}")
        
        # Initialize Similarity service (benzerlik arama)
        try:
            await similarity_service.initialize()
            if similarity_service.available:
                logger.info("✅ Benzerlik servisi hazır")
            else:
                logger.warning("⚠️ Benzerlik servisi kullanılamıyor")
        except Exception as e:
            logger.error(f"❌ Benzerlik servisi başlatılamadı: {e}")
        
        # Initialize LLM service with RAG service
        llm_module.llm_service = LLMService(rag_service=rag_service)
        logger.info("✅ LLM servisi hazır")
        
        logger.info("🎉 All services initialized successfully!")
        
    except Exception as e:
        logger.error(f"❌ Background initialization error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Starting Beymetal Chat API...")
    logger.info("⚡ Quick startup mode - services will initialize in background")
    
    # Start background initialization
    init_task = asyncio.create_task(initialize_services_background())
    
    # Start background auto-refresh tasks
    refresh_task = asyncio.create_task(auto_refresh_task())
    catalog_refresh_task = asyncio.create_task(auto_refresh_catalog_task())
    logger.info("🔄 Auto-refresh tasks started")
    
    logger.info("✅ Application ready to accept requests!")
    
    yield
    
    # Cancel background tasks on shutdown
    init_task.cancel()
    refresh_task.cancel()
    catalog_refresh_task.cancel()
    try:
        await init_task
        await refresh_task
        await catalog_refresh_task
    except asyncio.CancelledError:
        pass
    
    # Close similarity service
    try:
        from services.similarity_service import similarity_service
        await similarity_service.close()
    except:
        pass
    
    logger.info("Shutting down Beymetal Chat API...")


# Create FastAPI app
app = FastAPI(
    title="Beymetal Chat API",
    description="AI-powered chat assistant for Beymetal aluminum profiles",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000", "http://localhost:8080", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Beymetal Chat API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint - always returns healthy for quick startup"""
    try:
        from services.excel_service import excel_service
        from services.embedding_service import embedding_service
        from services.llm_service import llm_service
        
        stats = excel_service.get_stats()
        emb_stats = embedding_service.get_stats()
        llm_stats = llm_service.get_stats() if llm_service else {"is_enabled": False}
        
        return {
            "status": "healthy",
            "llm_enabled": llm_stats.get("is_enabled", False),
            "llm_stats": llm_stats,
            "vector_db_ready": emb_stats["is_ready"],
            "profiles_count": stats["total_profiles"],
            "last_update": stats["last_update"],
            "categories": stats["categories"],
            "embedding_stats": emb_stats
        }
    except Exception as e:
        # During startup, services might not be ready yet
        logger.warning(f"Health check: services initializing... {e}")
        return {
            "status": "healthy",
            "message": "Services are initializing in background",
            "ready": False
        }


@app.post("/api/refresh-data")
async def refresh_data():
    """Refresh Excel data from Google Drive and rebuild embeddings"""
    from services.excel_service import excel_service
    from services.embedding_service import embedding_service
    
    try:
        # Excel'i yeniden indir
        logger.info("Excel yenileniyor...")
        success = await excel_service.refresh_data()
        
        if not success:
            raise HTTPException(status_code=500, detail="Excel yenileme başarısız")
        
        # Embedding'leri yeniden oluştur
        logger.info("Embedding'ler yeniden oluşturuluyor...")
        profiles = excel_service.get_profiles()
        emb_success = await embedding_service.initialize(profiles)
        
        if not emb_success:
            raise HTTPException(status_code=500, detail="Embedding yenileme başarısız")
        
        stats = excel_service.get_stats()
        return {
            "status": "success",
            "profiles_updated": stats["total_profiles"],
            "last_update": stats["last_update"],
            "embeddings_rebuilt": True
        }
            
    except Exception as e:
        logger.error(f"Refresh data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(request: dict):
    """Chat endpoint - AI-Driven with Function Calling or RAG Fallback"""
    import time
    from models.chat import ChatRequest, ChatResponse
    from services.llm_service import llm_service, SYSTEM_PROMPT
    from services.rag_service import rag_service
    
    # Parse request
    chat_request = ChatRequest(**request)
    
    start_time = time.time()
    
    try:
        logger.info(f"Chat request: {chat_request.message}")
        
        # Check for similarity request first
        from services.similarity_service import similarity_service
        similarity_request = similarity_service.parse_similarity_request(
            chat_request.message, 
            chat_request.conversation_history
        )
        
        if similarity_request and similarity_service.available:
            logger.info(f"🔍 Benzerlik isteği algılandı: {similarity_request}")
            
            # Benzer profilleri bul
            similarity_data = await similarity_service.find_similar_profiles(
                similarity_request["profile_code"],
                similarity_request["count"]
            )
            
            if similarity_data and "error" not in similarity_data:
                # Sonuçları formatla
                formatted_response = similarity_service.format_similarity_response(similarity_data)
                
                # Profile data oluştur (görseller için - Supabase'den)
                profile_data = []
                if similarity_data.get("results"):
                    for result in similarity_data["results"][:30]:  # İlk 30 profili göster
                        # Profil kodunu normalize et (Supabase için)
                        profile_code = result["profile_code"]
                        normalized_code = profile_code
                        if profile_code.startswith('LR-') or profile_code.startswith('GL-'):
                            normalized_code = profile_code[:2] + profile_code[3:]
                        
                        profile_data.append({
                            "code": profile_code,
                            "image_url": f"/api/profile-image/{profile_code}",
                            "similarity_score": result["similarity_score"]
                        })
                
                response_time = (time.time() - start_time) * 1000
                return ChatResponse(
                    answer=formatted_response,
                    profiles=profile_data,
                    confidence=0.95,
                    response_time_ms=response_time
                )
        
        # Check if LLM is enabled
        if not llm_service or not llm_service.is_enabled:
            logger.info("LLM disabled, using RAG fallback")
            
            # Extract previous user query from conversation history (for nearby search)
            previous_query = None
            if chat_request.conversation_history:
                # Son user mesajını bul
                for msg in reversed(chat_request.conversation_history):
                    if msg.get('role') == 'user':
                        previous_query = msg.get('content')
                        break
            
            # Use RAG service directly (request more profiles for load more functionality)
            answer, metadata = await rag_service.format_answer_with_llm(
                query=chat_request.message,
                top_k=500,  # Request many profiles for load more functionality
                conversation_history=chat_request.conversation_history,
                previous_query=previous_query
            )
            
            # Extract profile data from answer (parse markdown images)
            profile_data = []
            import re
            from services.catalog_service import catalog_service
            from services.search_service import search_service
            
            # Remove "... ve X profil daha" text from answer (we'll show this in load more button)
            answer = re.sub(r'\.\.\.\s*ve\s+\d+\s+profil\s+daha\.?', '', answer, flags=re.IGNORECASE)
            
            # Find all profile codes in markdown images: ![code](url)
            profile_codes = re.findall(r'!\[([A-Z0-9-]+)\]', answer)
            
            if profile_codes:
                logger.info(f"Found {len(profile_codes)} profiles in RAG response")
                
                # Check if this is a nearby search (don't search again, use profile codes from markdown)
                is_nearby_search = metadata.get("query_type") == "nearby_search"
                
                if is_nearby_search:
                    logger.info("Nearby search detected - using profile codes from markdown only")
                    # For nearby search, only get profiles that are in the markdown
                    # Don't do additional searches
                    results = None
                    catalog_results = []
                    
                    # Get each profile from catalog by code
                    for code in profile_codes:
                        cat_profile = catalog_service.get_profile_by_no(code)
                        if cat_profile:
                            catalog_results.append(cat_profile)
                    
                    logger.info(f"Nearby search: {len(catalog_results)} profiles from markdown codes")
                else:
                    # ALWAYS search again to get ALL matching profiles (not just first 15 from RAG)
                    # This allows load more functionality for ALL categories
                    results = search_service.search(chat_request.message, top_k=500)
                    logger.info(f"Search service returned {len(results) if results else 0} profiles")
                    
                    # ALWAYS try catalog service as well (for ALL categories)
                    catalog_results = catalog_service.search_profiles(chat_request.message.lower().strip(), limit=500)
                    logger.info(f"Catalog service returned {len(catalog_results) if catalog_results else 0} profiles")
                
                # Use whichever has more results
                if catalog_results and len(catalog_results) > len(results if results else []):
                    logger.info(f"Using catalog service results: {len(catalog_results)} profiles")
                    # Use catalog results
                    for cat_profile in catalog_results:
                        profile_info = {
                            "code": cat_profile.get('code'),
                            "image_url": f"/api/profile-image/{cat_profile.get('code')}"
                        }
                        if cat_profile.get('categories'):
                            profile_info["category"] = ', '.join(cat_profile['categories'])
                        if cat_profile.get('customer'):
                            profile_info["customer"] = cat_profile['customer']
                        if cat_profile.get('mold_status'):
                            profile_info["mold_status"] = cat_profile['mold_status']
                        profile_data.append(profile_info)
                
                # Use search service results if we don't have catalog results
                elif results:
                    logger.info(f"Search service found {len(results)} total profiles")
                    for profile, score, reason in results:
                        catalog_profile = catalog_service.get_profile_by_no(profile.code)
                        
                        profile_info = {
                            "code": profile.code,
                            "image_url": f"/api/profile-image/{profile.code}"
                        }
                        
                        if catalog_profile:
                            if catalog_profile.get('categories'):
                                profile_info["category"] = ', '.join(catalog_profile['categories'])
                            if catalog_profile.get('customer'):
                                profile_info["customer"] = catalog_profile['customer']
                            if catalog_profile.get('mold_status'):
                                profile_info["mold_status"] = catalog_profile['mold_status']
                        
                        profile_data.append(profile_info)
                else:
                    # Fallback: use profile codes from markdown
                    for code in profile_codes:
                        catalog_profile = catalog_service.get_profile_by_no(code)
                        
                        profile_info = {
                            "code": code,
                            "image_url": f"/api/profile-image/{code}"
                        }
                        
                        if catalog_profile:
                            if catalog_profile.get('categories'):
                                profile_info["category"] = ', '.join(catalog_profile['categories'])
                            if catalog_profile.get('customer'):
                                profile_info["customer"] = catalog_profile['customer']
                            if catalog_profile.get('mold_status'):
                                profile_info["mold_status"] = catalog_profile['mold_status']
                        
                        profile_data.append(profile_info)
            
            processing_time = time.time() - start_time
            
            # Build conversation history
            messages = chat_request.conversation_history.copy() if chat_request.conversation_history else []
            messages.append({"role": "user", "content": chat_request.message})
            messages.append({"role": "assistant", "content": answer})
            
            response_data = {
                "message": answer,
                "conversation_history": messages,
                "processing_time": processing_time,
                "metadata": metadata
            }
            
            # Add profile data if available
            if profile_data:
                response_data["profile_data"] = profile_data
                logger.info(f"Returning {len(profile_data)} profile data items (RAG)")
            
            return ChatResponse(**response_data)
        
        # LLM is enabled - use LLM with tools
        # Conversation history'yi hazırla
        messages = []
        
        # System prompt ekle (sadece ilk mesajsa)
        if not chat_request.conversation_history:
            messages.append({
                "role": "system",
                "content": SYSTEM_PROMPT
            })
        else:
            # Mevcut history'yi kullan
            messages = chat_request.conversation_history.copy()
        
        # Yeni kullanıcı mesajını ekle
        messages.append({
            "role": "user",
            "content": chat_request.message
        })
        
        # LLM'e gönder (tool definitions ile)
        llm_response = await llm_service.chat(
            messages=messages,
            tools=llm_service._get_tool_definitions()
        )
        
        # LLM tool call yaptı mı?
        profile_data = []  # Profil verilerini sakla
        
        if llm_response.tool_calls:
            logger.info(f"LLM made {len(llm_response.tool_calls)} tool calls")
            
            # Tool'ları execute et
            tool_results, profile_data = await llm_service.handle_tool_calls(
                llm_response.tool_calls
            )
            
            # Tool call mesajını history'ye ekle
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": llm_response.tool_calls
            })
            
            # Tool results'ları ekle
            for tool_result in tool_results:
                messages.append({
                    "role": "tool",
                    "content": tool_result["content"],
                    "tool_call_id": tool_result["tool_call_id"]
                })
            
            # LLM'e tekrar gönder (final answer için) - TOOLS OLMADAN (sonsuz döngüyü engelle)
            llm_response = await llm_service.chat(
                messages=messages,
                tools=None  # Tool'ları kaldır, sadece cevap üretsin
            )
        
        processing_time = time.time() - start_time
        
        # Response döndür
        response_data = {
            "message": llm_response.message or "Üzgünüm, bir cevap oluşturamadım.",
            "conversation_history": messages + [{
                "role": "assistant",
                "content": llm_response.message
            }],
            "processing_time": processing_time,
            "metadata": {
                "llm_used": not llm_response.fallback_used,
                "tokens_used": llm_response.tokens_used,
                "model": llm_response.model_used,
                "tool_calls_made": len(llm_response.tool_calls) if llm_response.tool_calls else 0
            }
        }
        
        # Profil verisi varsa ekle
        if profile_data:
            response_data["profile_data"] = profile_data
            logger.info(f"Returning {len(profile_data)} profile data items")
        
        return ChatResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=8004,  # 8004 portunu kullan
        reload=True
    )


# ============================================
# CATALOG ENDPOINTS
# ============================================

@app.get("/api/catalog/categories")
async def get_categories(companies: str = None):
    """
    Tüm kategorileri getir (Standart/Şekilsel/Sektörel)
    
    Args:
        companies: Virgülle ayrılmış şirket listesi (örn: "linearossa,beymetal,alfore")
    """
    from services.catalog_service import catalog_service
    
    try:
        # Şirket listesini parse et
        company_list = None
        if companies:
            company_list = [c.strip() for c in companies.split(',') if c.strip()]
        
        categories = catalog_service.get_categories(companies=company_list)
        stats = catalog_service.get_stats()
        
        return {
            "categories": categories,
            "stats": stats,
            "filtered_companies": company_list
        }
    except Exception as e:
        logger.error(f"Categories error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/catalog/profiles")
async def get_all_profiles(limit: int = 100):
    """Tüm profilleri getir"""
    from services.catalog_service import catalog_service
    
    try:
        profiles = catalog_service.get_all_profiles()
        return {
            "profiles": profiles[:limit],
            "total": len(profiles)
        }
    except Exception as e:
        logger.error(f"Get profiles error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/catalog/profile/{profile_no}")
async def get_profile(profile_no: str):
    """Profil numarasına göre profil getir"""
    from services.catalog_service import catalog_service
    
    try:
        profile = catalog_service.get_profile_by_no(profile_no)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profil bulunamadı")
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/catalog/category/{category}")
async def get_profiles_by_category(category: str, companies: str = None):
    """
    Kategoriye göre profilleri getir
    
    Args:
        category: Kategori adı
        companies: Virgülle ayrılmış şirket listesi
    """
    from services.catalog_service import catalog_service
    
    try:
        # Şirket listesini parse et
        company_list = None
        if companies:
            company_list = [c.strip() for c in companies.split(',') if c.strip()]
        

        profiles = catalog_service.get_profiles_by_category(category, companies=company_list)
        
        return {
            "category": category,
            "profiles": profiles,
            "count": len(profiles)
        }
    except Exception as e:
        logger.error(f"Get category profiles error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/catalog/search")
async def search_catalog(q: str, limit: int = 20):
    """Katalogda ara"""
    from services.catalog_service import catalog_service
    
    try:
        results = catalog_service.search_profiles(q, limit=limit)
        
        return {
            "query": q,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Search catalog error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/catalog/refresh")
async def refresh_catalog():
    """Kataloğu yenile"""
    from services.catalog_service import catalog_service
    
    try:
        logger.info("Katalog yenileniyor...")
        success = await catalog_service.initialize()
        
        if not success:
            raise HTTPException(status_code=500, detail="Katalog yenileme başarısız")
        
        stats = catalog_service.get_stats()
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Refresh catalog error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# CONNECTION ENDPOINTS
# ============================================

@app.get("/api/connections/systems")
async def get_connection_systems():
    """Tüm birleşim sistemlerini getir"""
    from services.connection_service import connection_service
    
    try:
        systems = connection_service.get_all_systems()
        return {
            "success": True,
            "data": systems,
            "count": len(systems)
        }
    except Exception as e:
        logger.error(f"Get systems error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/connections/system/{system_name}")
async def get_connection_system(system_name: str):
    """Belirli bir sistemin detaylarını getir"""
    from services.connection_service import connection_service
    
    try:
        system = connection_service.get_system_by_name(system_name)
        
        if system is None:
            return {
                "success": False,
                "error": f"Sistem bulunamadı: {system_name}"
            }
        
        return {
            "success": True,
            "data": system
        }
    except Exception as e:
        logger.error(f"Get system error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/connections/profile/{profile_code}")
async def get_profile_connection(profile_code: str):
    """Belirli bir profilin birleşim bilgilerini getir"""
    from services.connection_service import connection_service
    
    try:
        connection = connection_service.get_profile_connections(profile_code)
        
        if connection is None:
            return {
                "success": False,
                "error": f"Profil bulunamadı: {profile_code}"
            }
        
        return {
            "success": True,
            "data": connection
        }
    except Exception as e:
        logger.error(f"Get profile connection error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/connections/search")
async def search_connections(query: str):
    """Birleşim verilerinde arama yap"""
    from services.connection_service import connection_service
    
    try:
        if not query:
            return {
                "success": False,
                "error": "Arama sorgusu boş olamaz"
            }
        
        results = connection_service.search_connections(query)
        
        return {
            "success": True,
            "data": results,
            "count": len(results),
            "query": query
        }
    except Exception as e:
        logger.error(f"Search connections error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ============================================
# IMAGE ENDPOINTS
# ============================================

@app.get("/api/profile-image/{profile_code}")
async def get_profile_image(profile_code: str):
    """
    Profil koduna göre görsel getir - Supabase Storage'dan
    
    Args:
        profile_code: Profil kodu (örn: AP0001)
    """
    from fastapi.responses import RedirectResponse
    
    try:
        # Supabase Storage URL
        # Format: https://[PROJECT_ID].supabase.co/storage/v1/object/public/profile-images/AP0001.png
        supabase_url = settings.supabase_url  # .env'den alınacak
        bucket_name = "profile-images"
        
        # Profil kodunu normalize et - Supabase'de tire olmadan yüklendi
        # LR-3101-1 → LR3101-1
        # LR3101-1 → LR3101-1 (değişmez)
        normalized_code = profile_code
        if profile_code.startswith('LR-') or profile_code.startswith('GL-'):
            # İlk tireyi kaldır: LR-3101-1 → LR3101-1
            normalized_code = profile_code[:2] + profile_code[3:]
        
        image_filename = f"{normalized_code}.png"
        
        # Supabase public URL
        image_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{image_filename}"
        
        # Redirect to Supabase URL
        return RedirectResponse(url=image_url, status_code=302)
        
    except Exception as e:
        logger.error(f"Get profile image error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SIMILARITY SEARCH ENDPOINT
# ============================================

@app.get("/api/similarity/{profile_code}")
async def get_similar_profiles(profile_code: str, top_k: int = 30):
    """
    Profil koduna göre benzer profilleri getir
    
    Args:
        profile_code: Profil kodu (örn: LR3104, GL3100)
        top_k: Kaç benzer profil döndürülecek (varsayılan: 30, max: 100)
    
    Returns:
        {
            "query_profile": "LR3104",
            "results": [
                {"profile_code": "LR3105", "similarity_score": 0.95},
                ...
            ],
            "count": 30
        }
    """
    from services.similarity_service import similarity_service
    
    try:
        # Limit check
        top_k = min(max(1, top_k), 100)
        
        logger.info(f"Similarity search: {profile_code}, top_k={top_k}")
        
        if not similarity_service.available:
            raise HTTPException(
                status_code=503, 
                detail="Benzerlik servisi şu anda kullanılamıyor"
            )
        
        # Get similar profiles from similarity service
        data = await similarity_service.find_similar_profiles(profile_code, top_k)
        
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Similarity search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
