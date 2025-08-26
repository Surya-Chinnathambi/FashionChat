# Fashion E-commerce Platform with AI Chatbot

## Project Overview
A comprehensive fashion e-commerce platform with AI-powered chatbot using ChromaDB for vector similarity search, PostgreSQL for structured data, and OpenRouter API for natural language processing.

## Architecture
- **Backend**: FastAPI (Python)
- **Frontend**: React TypeScript with Vite
- **Databases**: 
  - PostgreSQL (users, orders, products)
  - ChromaDB (product vectors for semantic search)
- **AI**: OpenRouter API for intent detection and response generation
- **Authentication**: JWT with bcrypt

## User Preferences
- Use TypeScript for type safety
- Implement responsive design with Tailwind CSS
- Ensure all product data is converted to vectors for ChromaDB search
- Use Docker containers for databases

## Project Architecture
### Backend Structure
- `/backend/main.py` - FastAPI application entry point
- `/backend/models/` - SQLAlchemy models
- `/backend/routers/` - API route handlers
- `/backend/services/` - Business logic (ChromaDB, OpenRouter integration)
- `/backend/auth/` - Authentication utilities
- `/backend/database.py` - Database configuration

### Frontend Structure
- `/frontend/` - React TypeScript application
- `/frontend/src/components/` - Reusable components
- `/frontend/src/pages/` - Page components
- `/frontend/src/services/` - API integration

## Recent Changes
- Initial project setup (2025-08-26)
- Architecture planning with ChromaDB and OpenRouter integration

## Key Features
- AI-powered chatbot with intent detection
- Vector similarity search for products
- Real-time order tracking
- JWT authentication
- Responsive design
- Drag & drop chat interface