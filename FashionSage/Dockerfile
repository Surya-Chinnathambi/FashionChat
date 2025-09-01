# Use lightweight Python image
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for psycopg2, etc.)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY docker-requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r Docker-requirement.txt

# Copy backend source code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run the backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
