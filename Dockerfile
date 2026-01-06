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
CMD ["/bin/sh", "-c", "streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true"]
