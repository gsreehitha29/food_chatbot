"""
=============================================================
MAIN APPLICATION ENTRY POINT
=============================================================
This is the heart of the FastAPI application. It:

1. Creates the FastAPI app instance
2. Registers all route modules (menu, order, review, etc.)
3. Creates database indexes on startup
4. Provides a health-check root endpoint

TO RUN THIS SERVER:
    uvicorn main:app --reload

Then open your browser at:
    http://127.0.0.1:8000/docs   ← Swagger UI (test APIs here)
    http://127.0.0.1:8000/redoc  ← ReDoc (alternative docs)
=============================================================
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middleware.logging_middleware import log_request_middleware
from database import create_indexes

# Import all route modules
from routes.menu import router as menu_router
from routes.order import router as order_router
from routes.review import router as review_router
from routes.recommendation import router as recommendation_router
from routes.user import router as user_router
from routes.ai_search import router as ai_search_router

# =============================================================
# FIX #8: LIFESPAN CONTEXT MANAGER (replaces deprecated @app.on_event)
# =============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup logic before yield, teardown logic after."""
    import asyncio
    print("🚀 Starting Food Chatbot Backend...")
    create_indexes()

    # Auto-index menu embeddings into Qdrant on startup (runs in background)
    async def _run_indexing():
        try:
            from index_menu_embeddings import run_pipeline
            print("📦 Auto-indexing menu embeddings into Qdrant...")
            await asyncio.to_thread(run_pipeline, True)  # rebuild=True: always fresh
            print("✅ Menu embeddings indexed successfully!")
        except BaseException as e:
            print(f"⚠️  Auto-indexing failed (search may return no results): {e}")

    asyncio.create_task(_run_indexing())
    print("✅ Server is ready! Visit http://127.0.0.1:8000/docs")
    yield
    # Shutdown logic can go here if needed


# =============================================================
# CREATE THE FASTAPI APPLICATION
# =============================================================
app = FastAPI(
    title="🍔 Food Chatbot Backend API",
    description=(
        "A scalable food ordering chatbot backend built with "
        "FastAPI and MongoDB Atlas. Features include menu browsing, "
        "cart management, order processing, sentiment analysis, "
        "and AI-powered food recommendations."
    ),
    version="1.0.0",
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc
    lifespan=lifespan,      # FIX #8: use lifespan instead of @app.on_event
)

# =============================================================
# CORS MIDDLEWARE
# =============================================================
# CORS (Cross-Origin Resource Sharing) allows your frontend
# (running on a different port/domain) to call this backend.
# In production, replace "*" with your actual frontend URL.
# =============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Allow all origins (restrict in production)
    allow_credentials=True,
    allow_methods=["*"],          # Allow all HTTP methods
    allow_headers=["*"],          # Allow all headers
)

# =============================================================
# REQUEST LOGGING MIDDLEWARE
# =============================================================
app.middleware("http")(log_request_middleware)

# =============================================================
# REGISTER ALL ROUTERS
# =============================================================
# Each router handles a specific domain of the application.
# The prefix and tags are defined inside each router file.
# =============================================================
app.include_router(menu_router)
app.include_router(order_router)
app.include_router(review_router)
app.include_router(recommendation_router)
app.include_router(user_router)
app.include_router(ai_search_router)


# NOTE: Startup logic has been moved to the lifespan() context manager above.


# =============================================================
# ROOT ENDPOINT (Health Check)
# =============================================================
@app.get(
    "/",
    tags=["Health"],
    summary="Health check",
    description="Returns a simple message to confirm the API is running."
)
def root():
    """
    GET /
    
    A simple health-check endpoint to verify the server is alive.
    
    Response:
    {
        "status": "success",
        "message": "Food Chatbot Backend is running!",
        "docs": "http://127.0.0.1:8000/docs"
    }
    """
    return {
        "status": "success",
        "message": "🍔 Food Chatbot Backend is running!",
        "docs": "http://127.0.0.1:8000/docs",
        "version": "1.0.0"
    }
