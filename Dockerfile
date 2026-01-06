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

# Expose port 8501
EXPOSE 8501

# Run the app with shell to expand PORT variable
# Set STREAMLIT_SERVER_PORT to the actual PORT value to override any env var
# Add debugging and ensure proper startup
CMD ["/bin/sh", "-c", "echo 'Starting Streamlit on port '${PORT:-8501} && export STREAMLIT_SERVER_PORT=${PORT:-8501} && streamlit run app.py --server.address=0.0.0.0 --server.headless=true --server.enableCORS=true --server.enableXsrfProtection=false"]
