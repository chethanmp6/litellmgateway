# LLM Traceability API

A comprehensive FastAPI service for querying and analyzing LiteLLM proxy logs with session-based traceability.

## Features

### 🔍 Session Traceability
- **Complete session tracking** - Get all messages for any session ID
- **Session analytics** - Token usage, costs, response times, function calls
- **Advanced search** - Filter by agent, user, model, date range, cost

### 📊 Analytics & Dashboard
- **Overview dashboard** - High-level metrics and KPIs
- **Agent performance** - Track individual agent metrics
- **Model usage** - Analyze model performance and costs
- **Usage trends** - Time-based analysis (hourly/daily)
- **Cost breakdown** - Detailed cost analysis by model/agent/user

### 📋 Request Details
- **Individual request inspection** - Full request/response details
- **Message extraction** - Get conversation content
- **Performance metrics** - Response times, token usage, caching

## API Endpoints

### Session Traceability
```
GET  /api/v1/sessions/{session_id}/messages     # Get all messages in session
GET  /api/v1/sessions/{session_id}/summary      # Get session summary
POST /api/v1/sessions/search                    # Search sessions with filters
```

### Analytics
```
GET  /api/v1/analytics/overview                 # High-level overview
GET  /api/v1/analytics/agents                   # Agent performance
GET  /api/v1/analytics/models                   # Model usage stats
GET  /api/v1/analytics/usage-trends             # Usage over time
GET  /api/v1/analytics/cost-breakdown           # Cost analysis
```

### Request Details
```
GET  /api/v1/requests/{request_id}              # Individual request details
GET  /api/v1/requests/{request_id}/messages     # Request conversation
```

### Utility
```
GET  /health                                    # Health check
GET  /                                          # API info
GET  /docs                                      # Interactive API docs
```

## Quick Start

### 1. Using Docker Compose (Recommended)

```bash
cd traceability-api
docker-compose up -d
```

The API will be available at http://localhost:8000

### 2. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://litellm:changeme@localhost:5432/litellm"

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Verify Installation

```bash
# Check health
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Database connection (required)
DATABASE_URL=postgresql://litellm:changeme@localhost:5432/litellm

# API settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# CORS (for frontend integration)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

## Usage Examples

### Get Session Summary
```bash
curl http://localhost:8000/api/v1/sessions/fe6d311c-ae68-4177-8e0d-5dc2a7f61c11/summary
```

### Search Sessions
```bash
curl -X POST http://localhost:8000/api/v1/sessions/search \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "customer_support_bot",
    "start_date": "2025-12-01T00:00:00",
    "min_cost": 0.001
  }'
```

### Get Analytics Overview
```bash
curl http://localhost:8000/api/v1/analytics/overview?days=7
```

### Agent Performance
```bash
curl http://localhost:8000/api/v1/analytics/agents?days=30
```

## Data Models

### Session Summary Response
```json
{
  "session_id": "fe6d311c-ae68-4177-8e0d-5dc2a7f61c11",
  "user_id": "default_user_id",
  "agent_name": "customer_support",
  "conversation_name": "support_ticket_123",
  "total_messages": 5,
  "session_start": "2025-12-02T10:36:26",
  "session_end": "2025-12-02T10:36:42",
  "total_duration_seconds": 16.0,
  "total_tokens": 813,
  "total_cost": 0.0018037,
  "avg_response_time": 2.7,
  "function_calls_count": 0,
  "cache_hit_rate": 0.0,
  "models_used": ["gemini-2.5-flash"]
}
```

### Search Filters
```json
{
  "agent_name": "customer_support_bot",
  "user_id": "user123",
  "model": "gpt-4o",
  "start_date": "2025-12-01T00:00:00Z",
  "end_date": "2025-12-02T23:59:59Z",
  "min_cost": 0.001,
  "max_cost": 1.0
}
```

## Integration with Frontend

This API is designed to be consumed by frontend dashboards. Key features:

- **CORS enabled** for web applications
- **Pydantic models** for type safety
- **Comprehensive error handling**
- **Pagination support** with limit/offset
- **Interactive docs** at `/docs`

### React/Vue.js Example
```javascript
// Get session summary
const response = await fetch(`/api/v1/sessions/${sessionId}/summary`);
const sessionData = await response.json();

// Search sessions
const searchResults = await fetch('/api/v1/sessions/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    agent_name: 'support_bot',
    start_date: '2025-12-01T00:00:00'
  })
});
```

## Database Requirements

This API connects to the same PostgreSQL database used by your LiteLLM proxy. Ensure:

1. **Database access** - API can connect to PostgreSQL
2. **Read permissions** - On `LiteLLM_SpendLogs` table
3. **Network connectivity** - Between API and database

## Performance Notes

- **Connection pooling** - Handles up to 10 concurrent connections
- **Query optimization** - All queries use proper indexes
- **Async operations** - Non-blocking database operations
- **Error handling** - Comprehensive exception management

## Production Deployment

For production use:

1. **Set proper CORS origins** in environment
2. **Use connection pooling** (already configured)
3. **Enable logging** with appropriate log level
4. **Monitor health endpoint** for uptime
5. **Scale horizontally** as needed

## API Documentation

Visit http://localhost:8000/docs for interactive API documentation with:
- **Request/response schemas**
- **Try-it-out functionality**
- **Parameter descriptions**
- **Error code definitions**