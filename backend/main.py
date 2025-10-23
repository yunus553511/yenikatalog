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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting Beymetal Chat API...")
    
    # Initialize Excel service
    from services.excel_service import excel_service
    from services.embedding_service import embedding_service
    
    success = await excel_service.initialize()
    
    if not success:
        logger.error("Excel servisi başlatılamadı!")
    else:
        stats = excel_service.get_stats()
        logger.info(f"Excel servisi hazır: {stats['total_profiles']} profil")
        
        # Initialize Embedding service
        profiles = excel_service.get_profiles()
        emb_success = await embedding_service.initialize(profiles)
        
        if emb_success:
            logger.info("Embedding servisi hazır")
        else:
            logger.error("Embedding servisi başlatılamadı!")
    
    # Start background auto-refresh task
    refresh_task = asyncio.create_task(auto_refresh_task())
    logger.info("🔄 Otomatik yenileme aktif (her 10 dakikada bir)")
    
    yield
    
    # Cancel background task on shutdown
    refresh_task.cancel()
    try:
        await refresh_task
    except asyncio.CancelledError:
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
    allow_origins=settings.cors_origins_list,
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
    """Health check endpoint"""
    from services.excel_service import excel_service
    from services.embedding_service import embedding_service
    
    stats = excel_service.get_stats()
    emb_stats = embedding_service.get_stats()
    
    return {
        "status": "healthy",
        "lm_studio_connected": False,  # TODO: Check LM Studio connection
        "vector_db_ready": emb_stats["is_ready"],
        "profiles_count": stats["total_profiles"],
        "last_update": stats["last_update"],
        "categories": stats["categories"],
        "embedding_stats": emb_stats
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
    """Chat endpoint - LLM olmadan direkt cevap"""
    import time
    from models.chat import ChatRequest, ChatResponse, ProfileContext
    from services.rag_service import rag_service
    from services.search_service import search_service
    
    # Parse request
    chat_request = ChatRequest(**request)
    
    start_time = time.time()
    
    try:
        logger.info(f"Chat request: {chat_request.message}")
        
        # Direkt cevap oluştur (LLM olmadan) - top_k artırıldı
        answer = rag_service.format_direct_answer(chat_request.message, top_k=15)
        
        # Context profilleri al
        results = search_service.search(chat_request.message, top_k=15)
        context = [
            ProfileContext(
                code=profile.code,
                category=profile.category,
                dimensions=profile.dimensions,
                match_reason=reason
            )
            for profile, score, reason in results
        ]
        
        processing_time = time.time() - start_time
        
        return ChatResponse(
            message=answer,
            context=context,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True
    )
