#!/bin/sh
set -e

echo "=== Chat Wallet Startup ==="
echo "PORT: ${PORT:-8501}"
echo "STREAMLIT_SERVER_PORT: ${STREAMLIT_SERVER_PORT:-not set}"
echo "Python version: $(python --version)"
echo "Streamlit version: $(streamlit --version)"

# Export the port
export STREAMLIT_SERVER_PORT=${PORT:-8501}

echo "Starting Streamlit on 0.0.0.0:${STREAMLIT_SERVER_PORT}"

# Start Streamlit with explicit config
exec streamlit run app.py \
  --server.address=0.0.0.0 \
  --server.port=${STREAMLIT_SERVER_PORT} \
  --server.headless=true \
  --server.enableCORS=true \
  --server.enableXsrfProtection=false \
  --browser.gatherUsageStats=false
