# Docker Setup Guide for Fashion E-commerce Chatbot

## Complete Docker Deployment Solution

This project is fully containerized and ready for Docker deployment with PostgreSQL database and OpenRouter API integration.

## Prerequisites

- Docker (20.10+)
- Docker Compose (2.0+)
- OpenRouter API key from [https://openrouter.ai/](https://openrouter.ai/)

## Quick Start (Recommended)

### 1. Run the Setup Script

```bash
chmod +x start.sh
./start.sh
```

This script will:
- Check Docker installation
- Create `.env` from template
- Prompt for OpenRouter API key configuration
- Start all services with Docker Compose
- Verify health of all services

### 2. Manual Setup

If you prefer manual setup:

```bash
# Copy environment template
cp .env.template .env

# Edit .env file with your settings
nano .env

# Start services
docker-compose up -d --build

# Check logs
docker-compose logs -f
```

## Environment Configuration

Edit `.env` file with your settings:

```bash
# Required: Get from https://openrouter.ai/
OPENROUTER_API_KEY=your_actual_api_key_here

# Database settings (defaults work fine)
POSTGRES_USER=fashion_user
POSTGRES_PASSWORD=fashion_pass
POSTGRES_DB=fashion_db

# Security (change in production)
JWT_SECRET_KEY=your_super_secret_jwt_key

# Application settings
APP_HOST=0.0.0.0
APP_PORT=8000
```

## Service Architecture

The Docker setup includes:

1. **PostgreSQL Database**
   - Port: 5432
   - Data persistence with volumes
   - Health checks enabled

2. **Backend API (FastAPI)**
   - Port: 8000
   - OpenRouter LLM integration
   - Simple text-based product search
   - JWT authentication

3. **Frontend (React + Vite)**
   - Port: 3000
   - TypeScript with Tailwind CSS
   - Real-time chat interface

## Docker Commands

### Start Services
```bash
docker-compose up -d          # Start in background
docker-compose up            # Start with logs
```

### Stop Services
```bash
docker-compose down           # Stop all services
docker-compose down -v        # Stop and remove volumes
```

### View Logs
```bash
docker-compose logs -f        # All services
docker-compose logs backend   # Backend only
docker-compose logs postgres  # Database only
```

### Rebuild Services
```bash
docker-compose up -d --build  # Rebuild and start
docker-compose build backend  # Rebuild backend only
```

### Database Management
```bash
# Access PostgreSQL
docker-compose exec postgres psql -U fashion_user -d fashion_db

# Backup database
docker-compose exec postgres pg_dump -U fashion_user fashion_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U fashion_user -d fashion_db < backup.sql
```

## Production Deployment

### Use Production Compose File

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# With environment file
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d
```

### Production Environment Variables

```bash
# .env.production
OPENROUTER_API_KEY=your_production_api_key
DATABASE_URL=your_production_database_url
JWT_SECRET_KEY=your_production_secret_key
DEBUG=false
CORS_ORIGINS=["https://yourdomain.com"]
```

## Health Checks

The application includes comprehensive health monitoring:

### Check Application Health
```bash
curl http://localhost:8000/api/health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "search_products": 8,
  "openrouter_configured": true
}
```

### Check Application Info
```bash
curl http://localhost:8000/api/info
```

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Change ports in docker-compose.yml or .env
   APP_PORT=8001
   ```

2. **Database Connection Failed**
   ```bash
   # Check PostgreSQL container
   docker-compose logs postgres
   
   # Restart database
   docker-compose restart postgres
   ```

3. **OpenRouter API Issues**
   ```bash
   # Verify API key in logs
   docker-compose logs backend | grep "openrouter"
   
   # Test API key manually
   curl -H "Authorization: Bearer your_key" https://openrouter.ai/api/v1/models
   ```

4. **Frontend Not Loading**
   ```bash
   # Check if backend is running
   curl http://localhost:8000/api/health
   
   # Rebuild frontend
   docker-compose build frontend
   ```

### Debug Mode

Enable debug logging:

```bash
# In .env file
DEBUG=true

# Restart services
docker-compose up -d --build
```

### Reset Everything

Complete reset (⚠️ This will delete all data):

```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

## Development vs Production

### Development Features
- Hot reload disabled for stability
- Debug logging available
- Local file mounting for development
- Exposed database ports

### Production Features
- Optimized builds
- Security hardening
- Health checks
- Restart policies
- Volume persistence

## Security Considerations

1. **Change Default Passwords**
   - Update `POSTGRES_PASSWORD`
   - Use strong `JWT_SECRET_KEY`

2. **API Key Security**
   - Store API keys securely
   - Use environment variables
   - Never commit keys to version control

3. **Network Security**
   - Configure CORS origins
   - Use HTTPS in production
   - Limit exposed ports

## Scaling

### Horizontal Scaling
```bash
# Scale backend replicas
docker-compose up -d --scale backend=3

# Load balancer needed for multiple replicas
```

### Database Scaling
```bash
# Use external database in production
DATABASE_URL=postgresql://user:pass@external-db:5432/fashion_db
```

## Monitoring

### Container Resource Usage
```bash
docker stats
```

### Application Metrics
```bash
# Health endpoint provides basic metrics
curl http://localhost:8000/api/health

# View detailed logs
docker-compose logs -f backend
```

## Backup Strategy

### Automated Backup Script
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec postgres pg_dump -U fashion_user fashion_db > backups/backup_$DATE.sql
```

### Data Volumes
```bash
# List volumes
docker volume ls

# Backup volume
docker run --rm -v fashion_ecommerce_postgres_data:/data -v $(pwd):/backup ubuntu tar czf /backup/postgres_backup.tar.gz /data
```

## Support

- **API Documentation**: http://localhost:8000/docs
- **Health Status**: http://localhost:8000/api/health
- **Application Info**: http://localhost:8000/api/info

For issues with the OpenRouter API, visit [OpenRouter Documentation](https://openrouter.ai/docs).

---

**Ready to deploy! 🚀**

Your fashion e-commerce chatbot is now fully containerized and ready for deployment with Docker.