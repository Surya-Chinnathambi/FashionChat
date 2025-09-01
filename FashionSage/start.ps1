# Fashion E-commerce Chatbot - Quick Start Script (PowerShell)

Write-Host "🚀 Fashion E-commerce Chatbot - Quick Start"
Write-Host "=========================================="

# Check if Docker is installed
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker is not installed. Please install Docker first."
    Write-Host "   Visit: https://docs.docker.com/get-docker/"
    exit 1
}

if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker Compose is not installed. Please install Docker Compose first."
    Write-Host "   Visit: https://docs.docker.com/compose/install/"
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating .env file from template..."
    Copy-Item ".env.template" ".env"
    Write-Host "⚠️  Please edit .env file and add your OpenRouter API key!"
    Write-Host "   You can get one at: https://openrouter.ai/"
    notepad ".env"
}

# Validate OpenRouter API key
$envFile = Get-Content ".env"
if ($envFile -match "your_openrouter_api_key_here") {
    Write-Host "❌ Please update your OpenRouter API key in .env file"
    exit 1
}

Write-Host "🔧 Starting services..."

# Build and start containers
docker-compose up -d --build

Write-Host "⏳ Waiting for services to start..."
Start-Sleep -Seconds 10

# Check if services are healthy
Write-Host "🔍 Checking service health..."

try {
    Invoke-WebRequest "http://localhost:8000/api/health" -UseBasicParsing | Out-Null
    Write-Host "✅ Backend service is healthy"
}
catch {
    Write-Host "❌ Backend service is not responding"
    Write-Host "📋 Backend logs:"
    docker-compose logs backend
    exit 1
}

Write-Host ""
Write-Host "🎉 Application is ready!"
Write-Host ""
Write-Host "📱 Frontend: http://localhost:3000"
Write-Host "🔗 Backend API: http://localhost:8000"
Write-Host "📚 API Docs: http://localhost:8000/docs"
Write-Host "🩺 Health Check: http://localhost:8000/api/health"
Write-Host ""
Write-Host "💬 Try the chatbot with queries like:"
Write-Host "   - 'Show me red dresses'"
Write-Host "   - 'I need winter jackets'"
Write-Host "   - 'Where is my order?'"
Write-Host ""
Write-Host "🛑 To stop: docker-compose down"
Write-Host "📋 View logs: docker-compose logs -f"
