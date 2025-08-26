#!/bin/bash
# Fashion E-commerce Chatbot - Quick Start Script

set -e

echo "🚀 Fashion E-commerce Chatbot - Quick Start"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.template .env
    echo "⚠️  Please edit .env file and add your OpenRouter API key!"
    echo "   You can get one at: https://openrouter.ai/"
    echo ""
    echo "📝 Opening .env file for editing..."
    ${EDITOR:-nano} .env
fi

# Validate OpenRouter API key
if grep -q "your_openrouter_api_key_here" .env; then
    echo "❌ Please update your OpenRouter API key in .env file"
    echo "   Edit the file and replace 'your_openrouter_api_key_here' with your actual API key"
    exit 1
fi

echo "🔧 Starting services..."

# Build and start containers
docker-compose up -d --build

echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are healthy
echo "🔍 Checking service health..."

# Check backend
if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "✅ Backend service is healthy"
else
    echo "❌ Backend service is not responding"
    echo "📋 Backend logs:"
    docker-compose logs backend
    exit 1
fi

echo ""
echo "🎉 Application is ready!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔗 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🩺 Health Check: http://localhost:8000/api/health"
echo ""
echo "💬 Try the chatbot with queries like:"
echo "   - 'Show me red dresses'"
echo "   - 'I need winter jackets'"
echo "   - 'Where is my order?'"
echo ""
echo "🛑 To stop: docker-compose down"
echo "📋 View logs: docker-compose logs -f"