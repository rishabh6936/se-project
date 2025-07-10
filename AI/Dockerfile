FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for AI/ML libraries
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 worker && chown -R worker:worker /app
USER worker

# Health check for worker process
HEALTHCHECK --interval=60s --timeout=30s --start-period=10s --retries=3 \
    CMD python -c "import redis; r=redis.Redis(host='redis-queue', port=6379); r.ping()" || exit 1

# Run the worker
CMD ["python", "worker.py"]