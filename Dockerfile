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

# Patch Streamlit's loading animation (optional, won't fail build)
RUN python patch_streamlit.py || echo "Patch skipped"

# Use Railway's PORT environment variable
ENV PORT=8501

# Expose port
EXPOSE $PORT

# Run the app - use shell form to expand $PORT
CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
