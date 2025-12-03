# 🚀 LiteLLM AI Gateway (LLM Proxy)

A complete, production-ready LiteLLM proxy setup that provides a unified API gateway for multiple Large Language Model (LLM) providers. This project includes rate limiting, load balancing, fallback mechanisms, logging, and comprehensive monitoring.

## 📖 Table of Contents

- [What is LiteLLM?](#what-is-litellm)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Keys Setup](#api-keys-setup)
- [Sample Applications](#sample-applications)
- [Monitoring & Logging](#monitoring--logging)
- [API Reference](#api-reference)

## 🤖 What is LiteLLM?

[LiteLLM](https://github.com/BerriAI/litellm) is an open-source library that provides a unified interface to 100+ LLM APIs with OpenAI-compatible format.

### Key Benefits:
- **Unified Interface**: One API for multiple LLM providers
- **OpenAI Compatibility**: Drop-in replacement for OpenAI API
- **Cost Control**: Budget limits, rate limiting, and usage tracking
- **High Availability**: Automatic failover and load balancing
- **Comprehensive Logging**: Track usage, costs, and performance

## 📋 Prerequisites

- **Docker & Docker Compose**: For deployment
- **Python 3.8+**: For sample applications
- **API Keys**: From LLM providers (OpenAI, Anthropic, etc.)
- **4GB+ RAM**: Recommended

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd llmproxy

# Copy environment file
cp .env.example .env
```

### 2. Configure API Keys

Edit the `.env` file with your actual API keys:

```bash
# Required: Add your LLM provider API keys
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Security: Change the master key for production
LITELLM_MASTER_KEY=sk-your-secure-master-key-here
```

### 3. Start the Proxy

```bash
# Start the LiteLLM proxy with database and caching (recommended)
docker-compose up -d

# Check if it's running
curl http://localhost:4000/health
```

### 4. Test the Setup

```bash
# Install Python dependencies
cd sample_app
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run a simple test
python simple_example.py
```

### Main Configuration File

The proxy is configured via `config/config.yaml`. Key sections:

#### Model Configuration
```yaml
model_list:
  - model_name: gpt-4o
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_API_KEY
      max_tokens: 4096
```

#### Rate Limiting
```yaml
litellm_settings:
  rpm: 6000  # Requests per minute
  tpm: 1000000  # Tokens per minute
  max_budget: 100  # USD per user per month
```

#### Fallbacks & Load Balancing
```yaml
router_settings:
  fallbacks:
    - gpt-4o: ["claude-3-5-sonnet", "gpt-4o-mini"]
  model_group_alias:
    smart-model: ["gpt-4o", "claude-3-5-sonnet"]
```

### Environment Variables

See `.env.example` for all available configuration options.

## 🔐 API Keys Setup

### OpenAI
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new secret key
3. Add to `.env`: `OPENAI_API_KEY=sk-...`

### Anthropic
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create an API key
3. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`

### Langfuse (Optional - for observability)
1. Go to [Langfuse Cloud](https://cloud.langfuse.com/) or self-host
2. Create a project and get your keys
3. Add to `.env`:
   ```bash
   LANGFUSE_PUBLIC_KEY=pk-your-public-key
   LANGFUSE_SECRET_KEY=sk-your-secret-key
   LANGFUSE_HOST=https://cloud.langfuse.com  # Optional, defaults to cloud
   ```


## 🏥 Health Checks

```bash
# Basic health check
curl http://localhost:4000/health

# List available models
curl http://localhost:4000/v1/models

# Check logs
docker-compose logs litellm-proxy
```

## 📊 Monitoring & Logging

### Built-in Admin UI
Access the web interface at http://localhost:4000 to view:
- Real-time usage statistics
- Model availability and latency
- Rate limit status
- Budget consumption

**Login Credentials:**
- Username: `admin`
- Password: `admin` (default, change in .env file for production)

### Logging Configuration
Configure various logging backends:

```yaml
litellm_params:
  success_callback: ["supabase", "langsmith", "langfuse"]
  failure_callback: ["supabase", "langfuse"]
```

#### Langfuse Integration
Langfuse provides comprehensive observability and tracing for your LLM applications:

1. **Setup**: Add Langfuse credentials to your `.env` file
2. **Automatic Logging**: All requests/responses are automatically tracked
3. **Custom Metadata**: Add custom tags and metadata to requests:
   ```python
   response = client.chat.completions.create(
       model="gpt-4o",
       messages=[...],
       extra_body={
           "metadata": {
               "generation_name": "customer-support",
               "trace_id": "trace-123",
               "user_id": "user-456"
           }
       }
   )
   ```
4. **Dashboard**: View detailed analytics at your Langfuse dashboard

### Database Logging
PostgreSQL database is included for advanced analytics and audit trails.

## 🗄️ PostgreSQL Database Contents

The PostgreSQL database stores comprehensive audit trails and analytics for your LiteLLM proxy:

### Key Tables

1. **`LiteLLM_SpendLogs`** - Complete API request audit trail (177 total requests tracked)
2. **`LiteLLM_VerificationToken`** - API Key management with usage tracking
3. **`LiteLLM_UserTable`** - User management and profiles
4. **`LiteLLM_TeamTable`** - Team/organization data
5. **`LiteLLM_BudgetTable`** - Spending controls and limits
6. **`LiteLLM_DailyUserSpend`** - Daily usage analytics
7. **`LiteLLM_ErrorLogs`** - Failed request tracking
8. **`LiteLLM_AuditLog`** - System audit and change tracking

### Database Access & Useful SQL Commands

#### Connect to Database

docker exec litellm-db psql -U litellm -d litellm -c "\dt"

```bash
# Access PostgreSQL database
docker exec -it litellm-db psql -U litellm -d litellm
```

#### Essential Queries

**1. View Recent API Requests**
```sql
SELECT "startTime", "endTime", model, "user", spend, total_tokens, prompt_tokens, completion_tokens
FROM "LiteLLM_SpendLogs"
ORDER BY "startTime" DESC LIMIT 10;
```

**2. Usage Summary by Model**
```sql
SELECT
    model,
    COUNT(*) as total_requests,
    SUM(spend) as total_cost,
    AVG(total_tokens) as avg_tokens,
    SUM(prompt_tokens) as total_prompt_tokens,
    SUM(completion_tokens) as total_completion_tokens
FROM "LiteLLM_SpendLogs"
GROUP BY model
ORDER BY total_cost DESC;
```

**3. User Spending & API Keys**
```sql
SELECT
    user_id,
    key_alias,
    spend,
    max_budget,
    models,
    created_at
FROM "LiteLLM_VerificationToken"
WHERE user_id IS NOT NULL
ORDER BY spend DESC;
```

**4. Daily Usage Patterns**
```sql
SELECT
    DATE("startTime") as request_date,
    COUNT(*) as requests,
    SUM(spend) as daily_cost,
    COUNT(DISTINCT "user") as unique_users,
    AVG(total_tokens) as avg_tokens_per_request
FROM "LiteLLM_SpendLogs"
GROUP BY DATE("startTime")
ORDER BY request_date DESC
LIMIT 7;
```

**5. Performance Analytics**
```sql
SELECT
    model,
    AVG(EXTRACT(EPOCH FROM ("endTime" - "startTime"))) as avg_response_time_seconds,
    MIN(EXTRACT(EPOCH FROM ("endTime" - "startTime"))) as min_response_time,
    MAX(EXTRACT(EPOCH FROM ("endTime" - "startTime"))) as max_response_time,
    COUNT(*) as total_requests
FROM "LiteLLM_SpendLogs"
WHERE "endTime" IS NOT NULL AND "startTime" IS NOT NULL
GROUP BY model
ORDER BY avg_response_time_seconds ASC;
```

**6. User Activity Analysis**
```sql
SELECT
    "user",
    COUNT(*) as total_requests,
    SUM(spend) as total_spent,
    AVG(total_tokens) as avg_tokens,
    MIN("startTime") as first_request,
    MAX("startTime") as last_request
FROM "LiteLLM_SpendLogs"
WHERE "user" IS NOT NULL AND "user" != ''
GROUP BY "user"
ORDER BY total_requests DESC;
```

**7. Failed Requests (Cost = 0)**
```sql
SELECT
    model,
    "user",
    "startTime",
    metadata,
    total_tokens
FROM "LiteLLM_SpendLogs"
WHERE spend = 0
ORDER BY "startTime" DESC
LIMIT 10;
```

**8. Cost Analysis by Time Period**
```sql
-- Last 24 hours
SELECT
    EXTRACT(HOUR FROM "startTime") as hour_of_day,
    COUNT(*) as requests,
    SUM(spend) as hourly_cost,
    AVG(total_tokens) as avg_tokens
FROM "LiteLLM_SpendLogs"
WHERE "startTime" >= NOW() - INTERVAL '24 hours'
GROUP BY EXTRACT(HOUR FROM "startTime")
ORDER BY hour_of_day;
```

**9. Token Usage Statistics**
```sql
SELECT
    model,
    SUM(prompt_tokens) as total_input_tokens,
    SUM(completion_tokens) as total_output_tokens,
    SUM(total_tokens) as total_tokens,
    ROUND(AVG(completion_tokens::float / prompt_tokens::float), 2) as avg_output_input_ratio
FROM "LiteLLM_SpendLogs"
WHERE prompt_tokens > 0
GROUP BY model
ORDER BY total_tokens DESC;
```

**10. Database Schema Exploration**
```sql
-- List all tables
\dt

-- Describe SpendLogs table structure
\d "LiteLLM_SpendLogs"

-- Count total records in key tables
SELECT
    'SpendLogs' as table_name,
    COUNT(*) as record_count
FROM "LiteLLM_SpendLogs"
UNION ALL
SELECT
    'VerificationToken',
    COUNT(*)
FROM "LiteLLM_VerificationToken"
UNION ALL
SELECT
    'UserTable',
    COUNT(*)
FROM "LiteLLM_UserTable";
```

### What You Can Track
- 📊 **Usage Analytics**: Request volumes, token consumption, costs by user/model
- 🔐 **Access Control**: API key management, permissions, budget limits
- 📈 **Performance Metrics**: Response times, error rates, cache hit ratios
- 💰 **Cost Management**: Spending by user, team, model, and time period
- 🛡️ **Audit Trail**: Complete request/response history for compliance
- 📋 **Operational Data**: Health checks, system status, configuration changes

## 🗨️ Session-Based Logging & Traceability

Track conversations and user sessions for comprehensive analytics and session management. The LiteLLM proxy supports rich session-based parameters that get automatically logged to PostgreSQL.

### Supported Session Parameters

When calling the `/chat/completions` API, you can pass the following session-based parameters:

#### Core Session Parameters:
- **`user`** - User identifier (logged to `"user"` field)
- **`metadata`** - JSON object containing session information:
  - `session_id` - Session identifier for grouping conversations
  - `agent_name` - Name of the AI agent/assistant
  - `conversation_name` - Name of the conversation thread
  - Custom metadata fields (department, priority, source, etc.)
- **`extra_headers`** - Additional headers for tracking
- **`request_tags`** - Tags for categorizing requests

### Example cURL Requests

#### 1. Basic Session with User and Session ID
```bash
curl -X POST "http://localhost:4000/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello, how are you?"}],
    "user": "john_doe_123",
    "metadata": {
      "session_id": "sess_abc123def456",
      "agent_name": "CustomerSupportBot",
      "conversation_name": "Support_Ticket_789"
    }
  }'
```

#### 2. Advanced Session with Multiple Metadata Fields
```bash
curl -X POST "http://localhost:4000/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "system", "content": "You are a helpful customer service agent."},
      {"role": "user", "content": "I need help with my order"}
    ],
    "user": "customer_456",
    "metadata": {
      "session_id": "cs_session_20241203_001",
      "agent_name": "OrderAssistant",
      "conversation_name": "Order_Help_Chat",
      "department": "customer_service",
      "priority": "high",
      "source": "web_chat",
      "customer_tier": "premium"
    },
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

#### 3. Streaming Session with Request Tags
```bash
curl -X POST "http://localhost:4000/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Explain machine learning in simple terms"}],
    "user": "student_789",
    "stream": true,
    "metadata": {
      "session_id": "edu_session_ml_101",
      "agent_name": "EducationBot",
      "conversation_name": "ML_Tutorial_Session",
      "course_id": "cs101",
      "lesson": "intro_to_ml"
    },
    "extra_headers": {
      "X-Session-Type": "educational",
      "X-Content-Category": "tutorial"
    }
  }'
```

#### 4. Function Calling Session
```bash
curl -X POST "http://localhost:4000/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "What is the weather like in New York?"}],
    "user": "weather_user_001",
    "metadata": {
      "session_id": "weather_session_nyc_001",
      "agent_name": "WeatherBot",
      "conversation_name": "NYC_Weather_Query",
      "location": "New_York_City"
    },
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "get_weather",
          "description": "Get current weather",
          "parameters": {
            "type": "object",
            "properties": {
              "location": {"type": "string"}
            }
          }
        }
      }
    ]
  }'
```

#### 5. Multi-turn Conversation Session
```bash
curl -X POST "http://localhost:4000/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "claude-3-5-haiku",
    "messages": [
      {"role": "user", "content": "Hi, I am working on a Python project"},
      {"role": "assistant", "content": "Great! I would be happy to help you with your Python project. What specific aspect are you working on?"},
      {"role": "user", "content": "I need help with async/await patterns"}
    ],
    "user": "developer_555",
    "metadata": {
      "session_id": "dev_session_python_async_001",
      "agent_name": "CodingAssistant",
      "conversation_name": "Python_Async_Help",
      "programming_language": "python",
      "topic": "async_programming",
      "experience_level": "intermediate"
    }
  }'
```

### Using Python Client

```python
import openai
import uuid

# Generate a session ID
session_id = str(uuid.uuid4())  # or use your own session logic

client = openai.OpenAI(
    api_key="your-litellm-api-key",
    base_url="http://localhost:4000/v1"
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
    user="user_123",
    extra_body={
        "metadata": {
            "session_id": session_id,
            "agent_name": "MyAssistant",
            "conversation_name": "General_Chat",
            "department": "support",
            "priority": "medium"
        }
    }
)
```

### PostgreSQL Session Logging

Your session data gets automatically logged in the `LiteLLM_SpendLogs` table with these key fields:

#### Database Fields That Capture Session Data:
- **`session_id`** - Direct session identifier (if provided at top level)
- **`user`** - User identifier from the `user` parameter
- **`metadata`** - JSON field containing all metadata (agent_name, conversation_name, etc.)
- **`request_id`** - Unique request identifier
- **`messages`** - Full conversation messages
- **`response`** - LLM response content
- **`model`** - Model used
- **`startTime`** / **`endTime`** - Request timing
- **`total_tokens`** / **`prompt_tokens`** / **`completion_tokens`** - Token usage
- **`spend`** - Cost tracking
- **`cache_hit`** - Whether response was cached
- **`request_tags`** - Request tagging

### Query Session Data

**1. View all requests for a specific session:**
```sql
SELECT
    request_id,
    "startTime",
    "user",
    model,
    total_tokens,
    spend,
    metadata->>'agent_name' as agent,
    metadata->>'conversation_name' as conversation,
    metadata
FROM "LiteLLM_SpendLogs"
WHERE metadata->>'session_id' = 'your_session_id'
ORDER BY "startTime";
```

**2. Session summary with aggregated metrics:**
```sql
SELECT
    metadata->>'session_id' as session_id,
    metadata->>'agent_name' as agent_name,
    metadata->>'conversation_name' as conversation_name,
    "user",
    COUNT(*) as total_requests,
    SUM(total_tokens) as total_tokens,
    SUM(spend) as total_cost,
    MIN("startTime") as session_start,
    MAX("startTime") as session_end,
    ROUND(AVG(EXTRACT(EPOCH FROM ("endTime" - "startTime"))), 2) as avg_response_time_seconds
FROM "LiteLLM_SpendLogs"
WHERE metadata->>'session_id' = 'your_session_id'
GROUP BY metadata->>'session_id', metadata->>'agent_name', metadata->>'conversation_name', "user";
```

**3. View conversation flow for a session:**
```sql
SELECT
    "startTime",
    messages,
    response
FROM "LiteLLM_SpendLogs"
WHERE metadata->>'session_id' = 'your_session_id'
ORDER BY "startTime" ASC;
```

**4. Agent performance by session:**
```sql
SELECT
    metadata->>'agent_name' as agent_name,
    COUNT(DISTINCT metadata->>'session_id') as unique_sessions,
    COUNT(*) as total_requests,
    SUM(total_tokens) as total_tokens,
    SUM(spend) as total_cost,
    AVG(EXTRACT(EPOCH FROM ("endTime" - "startTime"))) as avg_response_time_seconds
FROM "LiteLLM_SpendLogs"
WHERE metadata->>'agent_name' IS NOT NULL
GROUP BY metadata->>'agent_name'
ORDER BY total_requests DESC;
```

**5. Find all sessions for a user:**
```sql
SELECT
    metadata->>'session_id' as session_id,
    metadata->>'agent_name' as agent_name,
    metadata->>'conversation_name' as conversation_name,
    COUNT(*) as requests_in_session,
    SUM(spend) as session_cost,
    MIN("startTime") as session_start,
    MAX("startTime") as session_end
FROM "LiteLLM_SpendLogs"
WHERE "user" = 'your_user_id'
    AND metadata->>'session_id' IS NOT NULL
GROUP BY metadata->>'session_id', metadata->>'agent_name', metadata->>'conversation_name'
ORDER BY session_start DESC;
```

**6. Session activity trends:**
```sql
SELECT
    DATE("startTime") as date,
    COUNT(DISTINCT metadata->>'session_id') as unique_sessions,
    COUNT(*) as total_requests,
    COUNT(DISTINCT "user") as unique_users,
    SUM(spend) as total_cost
FROM "LiteLLM_SpendLogs"
WHERE metadata->>'session_id' IS NOT NULL
    AND "startTime" >= NOW() - INTERVAL '7 days'
GROUP BY DATE("startTime")
ORDER BY date DESC;
```


## 📝 API Reference

### Chat Completions

```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

### List Models

```bash
curl -H "Authorization: Bearer your-key" \
     http://localhost:4000/v1/models
```

### Health Check

```bash
curl http://localhost:4000/health
```

---

## 📞 Support

- **LiteLLM Docs**: https://docs.litellm.ai/
- **GitHub Issues**: https://github.com/BerriAI/litellm/issues

**🚀 Happy coding with your LLM Gateway!**