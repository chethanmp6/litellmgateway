#!/usr/bin/env python3
"""
LLM Traceability API Service
FastAPI service for querying and analyzing LiteLLM proxy logs
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncpg
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection pool
db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db_pool
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://litellm:changeme@localhost:5432/litellm')

    try:
        db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
            command_timeout=60
        )
        logger.info("Database connection pool created successfully")
        yield
    finally:
        # Shutdown
        if db_pool:
            await db_pool.close()
            logger.info("Database connection pool closed")

app = FastAPI(
    title="LLM Traceability API",
    description="API service for LiteLLM proxy traceability and analytics",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database connection
async def get_db():
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")
    async with db_pool.acquire() as conn:
        yield conn

# Pydantic models for API responses
class SessionMessage(BaseModel):
    request_id: str
    message_sequence: int
    timestamp: datetime
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    response_time_seconds: float
    messages_length: int
    response_length: int
    response_type: str
    cache_hit: bool

class SessionSummary(BaseModel):
    session_id: str
    user_id: str
    agent_name: str
    conversation_name: str
    total_messages: int
    session_start: datetime
    session_end: datetime
    total_duration_seconds: float
    total_tokens: int
    total_cost: float
    avg_response_time: float
    function_calls_count: int
    cache_hit_rate: float
    models_used: List[str]

class AgentPerformance(BaseModel):
    agent_name: str
    unique_sessions: int
    total_interactions: int
    avg_response_time: float
    total_tokens_used: int
    total_cost: float
    avg_conversation_length: float
    function_calls: int
    cache_hit_rate: float

class SearchFilters(BaseModel):
    agent_name: Optional[str] = None
    user_id: Optional[str] = None
    model: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_cost: Optional[float] = None
    max_cost: Optional[float] = None

# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "LLM Traceability API",
        "docs": "/docs",
        "health": "/health"
    }

# =============================================================================
# SESSION TRACEABILITY ENDPOINTS
# =============================================================================

@app.get("/api/v1/sessions/{session_id}/messages", response_model=List[SessionMessage])
async def get_session_messages(
    session_id: str,
    conn=Depends(get_db)
):
    """Get all messages for a specific session with full traceability"""
    query = """
    SELECT
        request_id,
        ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY "startTime") as message_sequence,
        "startTime" as timestamp,
        model,
        prompt_tokens,
        completion_tokens,
        total_tokens,
        spend as cost,
        EXTRACT(EPOCH FROM ("endTime" - "startTime")) as response_time_seconds,
        LENGTH(messages::text) as messages_length,
        LENGTH(response::text) as response_length,
        CASE
            WHEN response::text LIKE '%tool_call%' OR response::text LIKE '%function_call%' THEN 'function_call'
            ELSE 'regular_response'
        END as response_type,
        CASE WHEN cache_hit = 'True' THEN true ELSE false END as cache_hit
    FROM "LiteLLM_SpendLogs"
    WHERE session_id = $1
    ORDER BY "startTime"
    """

    try:
        rows = await conn.fetch(query, session_id)
        if not rows:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting session messages: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/sessions/{session_id}/summary", response_model=SessionSummary)
async def get_session_summary(
    session_id: str,
    conn=Depends(get_db)
):
    """Get session summary with aggregated metrics"""
    query = """
    SELECT
        session_id,
        COALESCE("user", 'unknown') as user_id,
        COALESCE(metadata->>'agent_name', 'unknown') as agent_name,
        COALESCE(metadata->>'conversation_name', 'default') as conversation_name,
        COUNT(*) as total_messages,
        MIN("startTime") as session_start,
        MAX("endTime") as session_end,
        EXTRACT(EPOCH FROM (MAX("endTime") - MIN("startTime"))) as total_duration_seconds,
        SUM(total_tokens) as total_tokens,
        SUM(spend) as total_cost,
        AVG(EXTRACT(EPOCH FROM ("endTime" - "startTime"))) as avg_response_time,
        COUNT(CASE WHEN response::text LIKE '%tool_call%' OR response::text LIKE '%function_call%' THEN 1 END) as function_calls_count,
        ROUND(100.0 * COUNT(CASE WHEN cache_hit = 'True' THEN 1 END) / COUNT(*), 2) as cache_hit_rate,
        array_agg(DISTINCT model) as models_used
    FROM "LiteLLM_SpendLogs"
    WHERE session_id = $1
    GROUP BY session_id, "user", metadata->>'agent_name', metadata->>'conversation_name'
    """

    try:
        row = await conn.fetchrow(query, session_id)
        if not row:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        return dict(row)
    except Exception as e:
        logger.error(f"Error getting session summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/sessions/search", response_model=List[SessionSummary])
async def search_sessions(
    filters: SearchFilters,
    limit: int = Query(default=50, le=1000, description="Maximum number of sessions to return"),
    offset: int = Query(default=0, ge=0, description="Number of sessions to skip"),
    conn=Depends(get_db)
):
    """Search sessions with various filters"""
    conditions = ["session_id IS NOT NULL"]
    params = []

    # Build dynamic WHERE clause
    if filters.agent_name:
        params.append(filters.agent_name)
        conditions.append(f"metadata->>'agent_name' = ${len(params)}")

    if filters.user_id:
        params.append(filters.user_id)
        conditions.append(f'"user" = ${len(params)}')

    if filters.model:
        params.append(filters.model)
        conditions.append(f'model = ${len(params)}')

    if filters.start_date:
        # Convert to UTC if timezone-aware, or treat as UTC if naive
        start_date = filters.start_date
        if start_date.tzinfo is not None:
            start_date = start_date.replace(tzinfo=None)  # Remove timezone info for comparison
        params.append(start_date)
        conditions.append(f'"startTime" >= ${len(params)}')

    if filters.end_date:
        # Convert to UTC if timezone-aware, or treat as UTC if naive
        end_date = filters.end_date
        if end_date.tzinfo is not None:
            end_date = end_date.replace(tzinfo=None)  # Remove timezone info for comparison
        params.append(end_date)
        conditions.append(f'"startTime" <= ${len(params)}')

    if filters.min_cost:
        params.append(filters.min_cost)
        conditions.append(f'spend >= ${len(params)}')

    if filters.max_cost:
        params.append(filters.max_cost)
        conditions.append(f'spend <= ${len(params)}')

    # Add offset and limit
    params.extend([offset, limit])

    query = f"""
    SELECT
        session_id,
        COALESCE("user", 'unknown') as user_id,
        COALESCE(metadata->>'agent_name', 'unknown') as agent_name,
        COALESCE(metadata->>'conversation_name', 'default') as conversation_name,
        COUNT(*) as total_messages,
        MIN("startTime") as session_start,
        MAX("endTime") as session_end,
        EXTRACT(EPOCH FROM (MAX("endTime") - MIN("startTime"))) as total_duration_seconds,
        SUM(total_tokens) as total_tokens,
        SUM(spend) as total_cost,
        AVG(EXTRACT(EPOCH FROM ("endTime" - "startTime"))) as avg_response_time,
        COUNT(CASE WHEN response::text LIKE '%tool_call%' OR response::text LIKE '%function_call%' THEN 1 END) as function_calls_count,
        ROUND(100.0 * COUNT(CASE WHEN cache_hit = 'True' THEN 1 END) / COUNT(*), 2) as cache_hit_rate,
        array_agg(DISTINCT model) as models_used
    FROM "LiteLLM_SpendLogs"
    WHERE {' AND '.join(conditions)}
    GROUP BY session_id, "user", metadata->>'agent_name', metadata->>'conversation_name'
    ORDER BY session_start DESC
    OFFSET ${len(params) - 1}
    LIMIT ${len(params)}
    """

    try:
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error searching sessions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# =============================================================================
# ANALYTICS AND DASHBOARD ENDPOINTS
# =============================================================================

@app.get("/api/v1/analytics/overview")
async def get_analytics_overview(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    conn=Depends(get_db)
):
    """Get high-level analytics overview"""
    cutoff_date = f"NOW() - INTERVAL '{days} days'"

    try:
        # Get basic stats
        basic_query = f"""
        SELECT
            COUNT(*) as total_requests,
            COUNT(DISTINCT session_id) as unique_sessions,
            COUNT(DISTINCT "user") as unique_users,
            SUM(total_tokens) as total_tokens,
            SUM(spend) as total_cost
        FROM "LiteLLM_SpendLogs"
        WHERE "startTime" >= {cutoff_date}
        """
        basic_row = await conn.fetchrow(basic_query)

        # Get performance stats
        perf_query = f"""
        SELECT
            AVG(EXTRACT(EPOCH FROM ("endTime" - "startTime"))) as avg_response_time,
            COUNT(CASE WHEN cache_hit = 'True' THEN 1 END) as cache_hits
        FROM "LiteLLM_SpendLogs"
        WHERE "startTime" >= {cutoff_date}
        """
        perf_row = await conn.fetchrow(perf_query)

        # Get function call stats
        func_query = f"""
        SELECT
            COUNT(CASE WHEN response::text LIKE '%tool_call%' OR response::text LIKE '%function_call%' THEN 1 END) as total_function_calls
        FROM "LiteLLM_SpendLogs"
        WHERE "startTime" >= {cutoff_date}
        """
        func_row = await conn.fetchrow(func_query)

        # Combine results
        result = dict(basic_row)
        result.update(dict(perf_row))
        result.update(dict(func_row))

        # Calculate cache hit rate
        if result['total_requests'] > 0:
            result['cache_hit_rate'] = round(100.0 * result['cache_hits'] / result['total_requests'], 2)
        else:
            result['cache_hit_rate'] = 0.0

        return result

    except Exception as e:
        logger.error(f"Error getting overview: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/analytics/agents", response_model=List[AgentPerformance])
async def get_agent_performance(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    conn=Depends(get_db)
):
    """Get agent performance analytics"""
    query = """
    SELECT
        COALESCE(metadata->>'agent_name', 'unknown') as agent_name,
        COUNT(DISTINCT session_id) as unique_sessions,
        COUNT(*) as total_interactions,
        AVG(EXTRACT(EPOCH FROM ("endTime" - "startTime"))) as avg_response_time,
        SUM(total_tokens) as total_tokens_used,
        SUM(spend) as total_cost,
        AVG(LENGTH(messages::text) + LENGTH(response::text)) as avg_conversation_length,
        COUNT(CASE WHEN response::text LIKE '%tool_call%' OR response::text LIKE '%function_call%' THEN 1 END) as function_calls,
        ROUND(100.0 * COUNT(CASE WHEN cache_hit = 'True' THEN 1 END) / COUNT(*), 2) as cache_hit_rate
    FROM "LiteLLM_SpendLogs"
    WHERE "startTime" >= NOW() - INTERVAL '%s days'
        AND session_id IS NOT NULL
    GROUP BY metadata->>'agent_name'
    ORDER BY total_interactions DESC
    """

    try:
        rows = await conn.fetch(query % days)
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting agent performance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/analytics/models")
async def get_model_usage(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    conn=Depends(get_db)
):
    """Get model usage analytics"""
    query = """
    SELECT
        model,
        COUNT(*) as total_requests,
        SUM(prompt_tokens) as total_prompt_tokens,
        SUM(completion_tokens) as total_completion_tokens,
        SUM(total_tokens) as total_tokens,
        SUM(spend) as total_cost,
        AVG(EXTRACT(EPOCH FROM ("endTime" - "startTime"))) as avg_response_time,
        MIN(EXTRACT(EPOCH FROM ("endTime" - "startTime"))) as min_response_time,
        MAX(EXTRACT(EPOCH FROM ("endTime" - "startTime"))) as max_response_time,
        COUNT(CASE WHEN cache_hit = 'True' THEN 1 END) as cache_hits,
        ROUND(100.0 * COUNT(CASE WHEN cache_hit = 'True' THEN 1 END) / COUNT(*), 2) as cache_hit_rate,
        custom_llm_provider as provider
    FROM "LiteLLM_SpendLogs"
    WHERE "startTime" >= NOW() - INTERVAL '%s days'
        AND model != ''
    GROUP BY model, custom_llm_provider
    ORDER BY total_requests DESC
    """

    try:
        rows = await conn.fetch(query % days)
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting model usage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/analytics/usage-trends")
async def get_usage_trends(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    granularity: str = Query(default="day", regex="^(hour|day)$", description="Data granularity"),
    conn=Depends(get_db)
):
    """Get usage trends over time"""
    if granularity == "hour":
        date_trunc = "hour"
        format_str = "YYYY-MM-DD HH24:00:00"
    else:
        date_trunc = "day"
        format_str = "YYYY-MM-DD"

    query = f"""
    SELECT
        TO_CHAR(DATE_TRUNC('{date_trunc}', "startTime"), '{format_str}') as time_period,
        COUNT(*) as total_requests,
        COUNT(DISTINCT session_id) as unique_sessions,
        SUM(total_tokens) as total_tokens,
        SUM(spend) as total_cost,
        AVG(EXTRACT(EPOCH FROM ("endTime" - "startTime"))) as avg_response_time,
        COUNT(CASE WHEN response::text LIKE '%tool_call%' OR response::text LIKE '%function_call%' THEN 1 END) as function_calls
    FROM "LiteLLM_SpendLogs"
    WHERE "startTime" >= NOW() - INTERVAL '%s days'
    GROUP BY DATE_TRUNC('{date_trunc}', "startTime")
    ORDER BY DATE_TRUNC('{date_trunc}', "startTime")
    """

    try:
        rows = await conn.fetch(query % days)
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting usage trends: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/analytics/cost-breakdown")
async def get_cost_breakdown(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    group_by: str = Query(default="model", regex="^(model|agent|user)$", description="Group costs by"),
    conn=Depends(get_db)
):
    """Get cost breakdown by different dimensions"""
    group_field_map = {
        "model": "model",
        "agent": "COALESCE(metadata->>'agent_name', 'unknown')",
        "user": 'COALESCE("user", \'unknown\')'
    }

    group_field = group_field_map[group_by]

    query = f"""
    SELECT
        {group_field} as category,
        COUNT(*) as total_requests,
        SUM(total_tokens) as total_tokens,
        SUM(spend) as total_cost,
        AVG(spend) as avg_cost_per_request,
        ROUND(100.0 * SUM(spend) / (SELECT SUM(spend) FROM "LiteLLM_SpendLogs"
                                     WHERE "startTime" >= NOW() - INTERVAL '%s days'), 2) as cost_percentage
    FROM "LiteLLM_SpendLogs"
    WHERE "startTime" >= NOW() - INTERVAL '%s days'
        AND spend > 0
    GROUP BY {group_field}
    ORDER BY total_cost DESC
    """

    try:
        rows = await conn.fetch(query % (days, days))
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting cost breakdown: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# =============================================================================
# INDIVIDUAL REQUEST ENDPOINTS
# =============================================================================

@app.get("/api/v1/requests/{request_id}")
async def get_request_details(
    request_id: str,
    conn=Depends(get_db)
):
    """Get detailed information about a specific request"""
    query = """
    SELECT
        request_id,
        session_id,
        "user" as user_id,
        model,
        call_type,
        "startTime" as request_start,
        "endTime" as request_end,
        "completionStartTime" as completion_start,
        EXTRACT(EPOCH FROM ("endTime" - "startTime")) as total_time,
        CASE
            WHEN "completionStartTime" IS NOT NULL THEN
                EXTRACT(EPOCH FROM ("completionStartTime" - "startTime"))
            ELSE NULL
        END as time_to_first_token,
        prompt_tokens,
        completion_tokens,
        total_tokens,
        spend as cost,
        cache_hit,
        cache_key,
        custom_llm_provider as provider,
        api_base,
        metadata,
        messages,
        response,
        request_tags
    FROM "LiteLLM_SpendLogs"
    WHERE request_id = $1
    """

    try:
        row = await conn.fetchrow(query, request_id)
        if not row:
            raise HTTPException(status_code=404, detail=f"Request {request_id} not found")

        result = dict(row)
        # Parse JSON fields if they exist
        for field in ['metadata', 'messages', 'response', 'request_tags']:
            if result[field] and isinstance(result[field], str):
                try:
                    result[field] = json.loads(result[field])
                except:
                    pass

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting request details: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/requests/{request_id}/messages")
async def get_request_messages(
    request_id: str,
    conn=Depends(get_db)
):
    """Get the full conversation messages for a request"""
    query = """
    SELECT messages, response
    FROM "LiteLLM_SpendLogs"
    WHERE request_id = $1
    """

    try:
        row = await conn.fetchrow(query, request_id)
        if not row:
            raise HTTPException(status_code=404, detail=f"Request {request_id} not found")

        return {
            "request_id": request_id,
            "messages": row['messages'],
            "response": row['response']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting request messages: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)