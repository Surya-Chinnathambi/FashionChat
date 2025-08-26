# Fashion E-commerce Platform with AI Chatbot

A comprehensive fashion e-commerce platform with AI-powered chatbot assistance using OpenRouter API for intent detection, Simple Search for product discovery, PostgreSQL for structured data, and a React TypeScript frontend.

## 🌟 Features

- **AI-Powered Chatbot**: OpenRouter API integration for natural language processing and intent detection
- **Smart Product Search**: Text-based similarity search for product discovery
- **User Authentication**: JWT-based authentication with bcrypt password hashing
- **Order Management**: Complete order tracking and management system
- **Real-time Chat Interface**: Interactive chat widget with session management
- **Responsive Design**: Modern UI built with React TypeScript and Tailwind CSS
- **Docker Support**: Complete containerization for easy deployment

## 🏗️ Architecture

```
User Query → OpenRouter LLM → Intent Detection → Route to:
├── Product Search (Simple Text Search)
├── Order Inquiry (PostgreSQL)
└── General Response (LLM)
```

### Tech Stack

**Backend:**
- FastAPI (Python) - REST API
- PostgreSQL - Structured data storage
- OpenRouter API - LLM for intent detection and responses
- Simple Search Service - Text-based product search
- JWT Authentication - Secure user sessions

**Frontend:**
- React 18 with TypeScript
- Vite - Fast development and build tool
- Tailwind CSS - Utility-first styling
- Responsive chat interface

**Infrastructure:**
- Docker & Docker Compose
- PostgreSQL Database
- Health checks and monitoring

## 🚀 Quick Start with Docker

### Prerequisites

- Docker and Docker Compose installed
- OpenRouter API key ([Get one here](https://openrouter.ai/))

### 1. Clone and Setup

```bash
git clone <your-repo>
cd fashion-ecommerce-chatbot
```

### 2. Configure Environment

Create a `.env` file in the root directory:

```bash
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Database Configuration (these are defaults, change if needed)
POSTGRES_USER=fashion_user
POSTGRES_PASSWORD=fashion_pass
POSTGRES_DB=fashion_db

# Security
JWT_SECRET_KEY=your_super_secret_jwt_key_change_in_production
```

### 3. Start the Application

```bash
# Start all services
docker-compose up -d

# Or start with logs
docker-compose up
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## 🔧 Manual Setup (Development)

### Backend Setup

1. **Install Python Dependencies**:
```bash
pip install -r docker-requirements.txt
```

2. **Setup Database**:
```bash
# Start PostgreSQL (or use Docker)
docker run -d --name postgres \
  -e POSTGRES_USER=fashion_user \
  -e POSTGRES_PASSWORD=fashion_pass \
  -e POSTGRES_DB=fashion_db \
  -p 5432:5432 postgres:15-alpine
```

3. **Configure Environment**:
```bash
export DATABASE_URL="postgresql://fashion_user:fashion_pass@localhost:5432/fashion_db"
export OPENROUTER_API_KEY="your_openrouter_api_key_here"
export JWT_SECRET_KEY="your_secret_key"
```

4. **Run Backend**:
```bash
python main.py
```

### Frontend Setup

1. **Install Dependencies**:
```bash
cd frontend
npm install
```

2. **Configure Environment**:
```bash
echo "VITE_API_URL=http://localhost:8000" > .env
```

3. **Run Frontend**:
```bash
npm run dev
```

## 📚 API Documentation

### Authentication Endpoints

- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user info

### Chat Endpoints

- `POST /chat/message` - Send message to chatbot
- `GET /chat/history/{session_id}` - Get chat history
- `GET /chat/sessions` - Get user's chat sessions

### Product Endpoints

- `GET /products/` - List all products
- `GET /products/search` - Search products
- `GET /products/{product_id}` - Get product details

### System Endpoints

- `GET /api/health` - Health check
- `GET /api/info` - Application information

## 💬 Chatbot Capabilities

### Intent Detection
The chatbot uses OpenRouter LLM to classify user intents:

1. **Product Search**: "Show me red dresses", "I need winter jackets"
2. **Order Inquiry**: "Where is my order?", "Track order #123"
3. **General Questions**: "What's your return policy?", "How do I contact support?"

### Search Features
- Text-based similarity matching
- Category and attribute filtering
- Brand and color-specific searches
- Price range filtering

### Example Queries
```
User: "I'm looking for a red dress for a party"
Bot: [Searches products] → [Returns relevant red dresses with details]

User: "Where is my order #12345?"
Bot: [Checks order status] → [Returns tracking information]

User: "What's your return policy?"
Bot: [General response] → [Provides policy information]
```

## 🔍 Project Structure

```
fashion-ecommerce-chatbot/
├── backend/
│   ├── main.py                 # FastAPI application entry
│   ├── models.py              # SQLAlchemy models
│   ├── schemas.py             # Pydantic schemas
│   ├── database.py            # Database configuration
│   ├── config.py             # Application configuration
│   ├── routers/              # API route handlers
│   │   ├── auth.py           # Authentication routes
│   │   ├── chat.py           # Chat routes
│   │   └── products.py       # Product routes
│   └── services/             # Business logic
│       ├── auth_service.py   # Authentication service
│       ├── chat_service.py   # Chat orchestration
│       ├── openrouter_client.py # LLM client
│       └── simple_search.py  # Product search service
├── frontend/                 # React TypeScript app
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── hooks/           # Custom hooks
│   │   ├── services/        # API integration
│   │   └── types/           # TypeScript definitions
│   └── public/              # Static assets
├── docker-compose.yml        # Docker orchestration
├── Dockerfile               # Backend container
└── README.md               # This file
```

## 🛠️ Development

### Adding New Features

1. **New API Endpoints**: Add to `routers/` directory
2. **Database Changes**: Update `models.py` and run migrations
3. **Chat Intents**: Extend `openrouter_client.py` intent classification
4. **Frontend Components**: Add to `frontend/src/components/`

### Testing

```bash
# Backend tests
pytest

# Frontend tests
cd frontend && npm run test

# Integration tests
docker-compose -f docker-compose.test.yml up
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## 🚀 Deployment

### Production Environment Variables

```bash
# Required
OPENROUTER_API_KEY=your_production_api_key
DATABASE_URL=your_production_database_url
JWT_SECRET_KEY=your_production_secret_key

# Optional
CORS_ORIGINS=["https://yourdomain.com"]
APP_HOST=0.0.0.0
APP_PORT=8000
```

### Docker Production Deployment

```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# Or use Docker Swarm
docker stack deploy -c docker-compose.prod.yml fashion-ecommerce
```

## 📊 Monitoring

### Health Checks

The application includes comprehensive health checks:

- Database connectivity
- Search service status
- API service health
- External service connectivity

### Logs

```bash
# View application logs
docker-compose logs -f backend

# View database logs
docker-compose logs -f postgres
```

## 🔐 Security

- JWT token authentication
- Bcrypt password hashing
- CORS protection
- SQL injection prevention
- Rate limiting (in production)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: GitHub Issues
- **Documentation**: `/docs` endpoint when running
- **API Docs**: `/docs` (Swagger UI) or `/redoc` (ReDoc)

## 🎯 Roadmap

- [ ] Vector embeddings with ChromaDB
- [ ] Advanced recommendation engine
- [ ] Multi-language support
- [ ] Voice chat interface
- [ ] Mobile app integration
- [ ] Analytics dashboard
- [ ] A/B testing framework

---

**Built with ❤️ for modern e-commerce experiences**