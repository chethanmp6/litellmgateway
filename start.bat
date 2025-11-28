@echo off
echo 🚀 Starting LiteLLM proxy with database...
docker-compose up -d
echo ⏳ Waiting for proxy to start...
timeout /t 15 /nobreak
echo.
echo 🏥 Running health check...
curl -s http://localhost:4000/health >nul && echo ✅ Proxy is healthy! || echo ❌ Proxy health check failed
echo 📋 Available models:
curl -s http://localhost:4000/v1/models | findstr "id" | findstr /v "object"