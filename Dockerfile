# Chat Wallet - Custom Streamlit with branded splash screen
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port 8501
EXPOSE 8501

# Health check to verify app is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8501}/_stcore/health || exit 1

# Use startup script for better debugging and error handling
CMD ["/bin/sh", "/app/start.sh"]
