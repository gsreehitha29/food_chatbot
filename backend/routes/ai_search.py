"""
=============================================================
AI SEARCH ROUTES
=============================================================
FastAPI APIRouter for semantic search, hybrid search, conversational
search, recommendation engine, indexing, and health checks.
=============================================================
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from typing import Dict, Any
import traceback
from models.ai_models import (
    SearchRequest, 
    SearchResponse, 
    RecommendationRequest, 
    RecommendationResponse,
    ConversationRequest, 
    ConversationResponse,
    QueryFilters
)
from services.ai_retrieval_service import AIRetrievalService
from index_menu_embeddings import run_pipeline
import config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["AI Search & Recommendations"])

# Single shared orchestrator service
try:
    ai_service = AIRetrievalService()
except Exception as e:
    logger.error(f"Failed to initialize AIRetrievalService: {str(e)}")
    ai_service = None


@router.post(
    "/semantic",
    response_model=SearchResponse,
    summary="Semantic vector search",
    description="Finds food items using Gemini text-embedding-004 vectors in Qdrant, without strict metadata filtering."
)
def semantic_search(request: SearchRequest):
    if not ai_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Retrieval Service is not initialized."
        )
    
    try:
        results = ai_service.search_semantic(request.query, request.user_id)
        return SearchResponse(
            query=request.query,
            query_understanding=QueryFilters(semantic_intent=request.query),
            total_results=len(results),
            items=results
        )
    except Exception as e:
        logger.error(f"Error in semantic search endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search failed: {str(e)}"
        )


@router.post(
    "/hybrid",
    response_model=SearchResponse,
    summary="Hybrid metadata + semantic search",
    description="Leverages Gemini LLM to extract structured filters (cuisine, price, veg) and performs Qdrant semantic search matching constraints."
)
def hybrid_search(request: SearchRequest):
    if not ai_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Retrieval Service is not initialized."
        )

    try:
        data = ai_service.search_hybrid(request.query, request.user_id)
        return SearchResponse(
            query=request.query,
            query_understanding=data["query_understanding"],
            total_results=len(data["items"]),
            items=data["items"]
        )
    except Exception as e:
        logger.error(f"Error in hybrid search endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hybrid search failed: {str(e)}"
        )


@router.post(
    "/conversation",
    response_model=ConversationResponse,
    summary="Conversational search",
    description="Context-aware chat assistant that accumulates preferences (spicy, cheap, veg) across dialogue turns and responds conversationally."
)
def conversational_search(request: ConversationRequest):
    if not ai_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Retrieval Service is not initialized."
        )

    try:
        data = ai_service.search_conversational(request.query, request.session_id, request.user_id)
        return ConversationResponse(
            session_id=data["session_id"],
            query=data["query"],
            accumulated_filters=data["accumulated_filters"],
            response_text=data["response_text"],
            items=data["items"]
        )
    except Exception as e:

        logger.error(traceback.format_exc())

        raise HTTPException(
            status_code=500,
            detail=f"Conversational search failed: {str(e)}"
        )


@router.post(
    "/recommendations",
    response_model=RecommendationResponse,
    summary="AI-powered recommendations",
    description="Generates personalized suggestions using cart contents and profile preferences with Gemini recommendation reasoning."
)
def recommendations(request: RecommendationRequest):
    if not ai_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Retrieval Service is not initialized."
        )

    try:
        results = ai_service.get_recommendations(request.user_id, request.limit)
        return RecommendationResponse(
            user_id=request.user_id,
            recommendations=results
        )
    except Exception as e:
        logger.error(f"Error in recommendations endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendations failed: {str(e)}"
        )


@router.post(
    "/embeddings/index",
    summary="Incremental embedding update",
    description="Runs the indexing pipeline in the background to vectorize and index only new or modified MongoDB documents in Qdrant."
)
def index_embeddings(background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(run_pipeline, False)
        return {
            "status": "success",
            "message": "Incremental indexing pipeline started in the background."
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start incremental indexing: {str(e)}"
        )


@router.post(
    "/embeddings/rebuild",
    summary="Full embedding rebuild",
    description="Deletes the current Qdrant collection and re-indexes all menu items from MongoDB in the background."
)
def rebuild_embeddings(background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(run_pipeline, True)
        return {
            "status": "success",
            "message": "Full embedding rebuild pipeline started in the background."
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start rebuild indexing: {str(e)}"
        )


@router.get(
    "/health",
    summary="AI engine health check",
    description="Verifies the operational status of Qdrant, Gemini Embeddings, and Redis Caching."
)
def health_check():
    health = {
        "status": "healthy",
        "qdrant": "connected",
        "gemini": "available",
        "caching": "disabled"
    }
    
    # Check Qdrant status
    try:
        if ai_service and ai_service.vector_service:
            # Simple check by getting collection details
            ai_service.vector_service.client.get_collection(config.QDRANT_COLLECTION)
        else:
            health["qdrant"] = "not initialized"
            health["status"] = "degraded"
    except Exception as e:
        health["qdrant"] = f"error: {str(e)}"
        health["status"] = "degraded"
        
    # Check Gemini status
    if not config.GEMINI_API_KEY:
        health["gemini"] = "API key missing"
        health["status"] = "degraded"
        
    # Check Caching status
    if ai_service and ai_service.cache_service:
        if ai_service.cache_service.use_redis:
            health["caching"] = "Redis active"
        else:
            health["caching"] = "In-memory active"
            
    return health
