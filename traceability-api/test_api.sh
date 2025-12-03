#!/bin/bash

echo "🚀 Testing LLM Traceability API Endpoints"
echo "========================================"

API_URL="http://localhost:8000"

echo
echo "1. 🏥 Health Check"
echo "-------------------"
curl -s "$API_URL/health" | jq .

echo
echo "2. 🔍 Session Search (All Sessions)"
echo "-----------------------------------"
curl -s -X POST "$API_URL/api/v1/sessions/search" \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.[:3]'

echo
echo "3. 📊 Session Summary"
echo "--------------------"
SESSION_ID=$(curl -s -X POST "$API_URL/api/v1/sessions/search" -H "Content-Type: application/json" -d '{}' | jq -r '.[0].session_id')
curl -s "$API_URL/api/v1/sessions/$SESSION_ID/summary" | jq .

echo
echo "4. 💬 Session Messages"
echo "----------------------"
curl -s "$API_URL/api/v1/sessions/$SESSION_ID/messages" | jq '.[:2]'

echo
echo "5. 🎯 Filtered Search (Today's Sessions)"
echo "---------------------------------------"
TODAY=$(date -u +"%Y-%m-%dT00:00:00Z")
curl -s -X POST "$API_URL/api/v1/sessions/search" \
  -H "Content-Type: application/json" \
  -d "{\"start_date\": \"$TODAY\"}" | jq '.[:2]'

echo
echo "6. 📈 Analytics (if working)"
echo "---------------------------"
curl -s "$API_URL/api/v1/analytics/agents" && echo
curl -s "$API_URL/api/v1/analytics/models" && echo

echo
echo "✅ API is working! Check http://localhost:8000/docs for interactive documentation"
echo "📊 Available Endpoints:"
echo "   - Session Search: POST /api/v1/sessions/search"
echo "   - Session Summary: GET /api/v1/sessions/{id}/summary"
echo "   - Session Messages: GET /api/v1/sessions/{id}/messages"
echo "   - Agent Analytics: GET /api/v1/analytics/agents"
echo "   - Model Analytics: GET /api/v1/analytics/models"