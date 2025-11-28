# LiteLLM Proxy Makefile
# Convenience commands for managing the LiteLLM proxy

.PHONY: help start stop restart logs health test clean setup install

# Default target
help:
	@echo "🚀 LiteLLM Proxy Management"
	@echo "=========================="
	@echo ""
	@echo "Available commands:"
	@echo "  setup      - Initial setup (copy .env and create directories)"
	@echo "  install    - Install Python dependencies for sample apps"
	@echo "  start      - Start the LiteLLM proxy with database"
	@echo "  stop       - Stop the LiteLLM proxy"
	@echo "  restart    - Restart the LiteLLM proxy"
	@echo "  logs       - Show proxy logs"
	@echo "  health     - Run health check"
	@echo "  test       - Run sample applications"
	@echo "  clean      - Stop and remove all containers and volumes"
	@echo "  help       - Show this help message"

# Initial setup
setup:
	@echo "📋 Setting up LiteLLM proxy..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file from .env.example"; \
		echo "⚠️  Please edit .env and add your API keys"; \
	else \
		echo "ℹ️  .env file already exists"; \
	fi
	@mkdir -p logs
	@echo "✅ Setup complete!"

# Install Python dependencies
install:
	@echo "📦 Installing Python dependencies..."
	@cd sample_app && pip install -r requirements.txt
	@echo "✅ Dependencies installed!"

# Start the proxy
start:
	@echo "🚀 Starting LiteLLM proxy with database..."
	@docker-compose up -d
	@echo "⏳ Waiting for proxy to start..."
	@sleep 15
	@echo "🏥 Checking health..."
	@curl -s http://localhost:4000/health > /dev/null && echo "✅ Proxy is healthy!" || echo "❌ Proxy health check failed"

# Stop the proxy
stop:
	@echo "🛑 Stopping LiteLLM proxy..."
	@docker-compose down

# Restart the proxy
restart: stop start

# Show logs
logs:
	@echo "📋 Showing LiteLLM proxy logs..."
	@docker-compose logs -f litellm-proxy

# Run health check
health:
	@echo "🏥 Running health check..."
	@curl -s http://localhost:4000/health > /dev/null && echo "✅ Proxy is healthy!" || echo "❌ Proxy health check failed"
	@echo "📋 Available models:"
	@curl -s http://localhost:4000/v1/models | grep -o '"id":"[^"]*"' | head -5 || echo "❌ Could not list models"

# Test with sample applications
test:
	@echo "🧪 Running sample applications..."
	@echo "Running simple example..."
	@cd sample_app && python simple_example.py
	@echo ""
	@echo "✅ Sample applications completed!"

# Clean everything
clean:
	@echo "🧹 Cleaning up..."
	@docker-compose down -v
	@docker system prune -f
	@echo "✅ Cleanup complete!"

# Database queries
db:
	@echo "🗄️  Connecting to PostgreSQL database..."
	@docker exec -it litellm-db psql -U litellm -d litellm

# Backup configuration
backup:
	@echo "💾 Creating configuration backup..."
	@tar -czf litellm-backup-$(shell date +%Y%m%d-%H%M%S).tar.gz config/ .env
	@echo "✅ Backup created!"

# Update proxy image
update:
	@echo "⬆️  Updating LiteLLM proxy image..."
	@docker-compose pull
	@docker-compose up -d
	@echo "✅ Update complete!"