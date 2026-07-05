FROM python:3.11-slim

# System deps for psycopg2 and matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    g++ \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer-cached unless requirements change)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Ensure local storage directory exists (used as fallback when cloud storage not configured)
RUN mkdir -p storage

EXPOSE 8000

# Production: run with 2 Uvicorn workers. Adjust to match your hosting tier.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
