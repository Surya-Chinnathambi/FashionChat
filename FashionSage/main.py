import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import init_db
from routers import auth, chat, products
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events"""
    # Startup
    logger.info("Starting Fashion E-commerce Chatbot...")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Run data sync in background
    try:
        from sync_data import seed_sample_data, sync_products_to_search
        await seed_sample_data()
        await sync_products_to_search()
        logger.info("Data sync completed")
    except Exception as e:
        logger.error(f"Data sync failed: {e}")
        # Don't fail startup if sync fails
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")

# Create FastAPI app
app = FastAPI(
    title="Fashion E-commerce Chatbot",
    description="AI-powered fashion chatbot with vector search and order management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# API routes first (before static file mounting)
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        from database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        
        # Test Simple Search
        from services.simple_search import SimpleSearchService
        search_service = SimpleSearchService()
        stats = {"total_products": len(search_service.products)}
        
        return {
            "status": "healthy",
            "database": "connected",
            "search_products": stats.get("total_products", 0),
            "openrouter_configured": bool(settings.OPENROUTER_API_KEY)
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/api/info")
async def get_app_info():
    """Get application information"""
    return {
        "name": "Fashion E-commerce Chatbot",
        "version": "1.0.0",
        "description": "AI-powered chatbot with Simple Search and PostgreSQL data",
        "features": [
            "OpenRouter LLM integration",
            "Text-based product search",
            "PostgreSQL data storage",
            "JWT authentication",
            "Real-time chat interface",
            "Product recommendations",
            "Order tracking"
        ],
        "endpoints": {
            "auth": "/auth",
            "chat": "/chat",
            "products": "/products",
            "health": "/api/health"
        }
    }

# Include API routers after defining API endpoints
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(products.router)

# Serve frontend files last (catch-all)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.APP_HOST}:{settings.APP_PORT}")
    
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=False,  # Set to True for development
        log_level="info"
    )
