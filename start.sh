#!/bin/sh
set -e

echo "=== Chat Wallet Startup ==="
echo "PORT (from Railway): ${PORT:-8501}"
echo "STREAMLIT_SERVER_PORT (before fix): ${STREAMLIT_SERVER_PORT:-not set}"

# CRITICAL: Unset the problematic env var that Railway sets to literal "$PORT"
unset STREAMLIT_SERVER_PORT

# Now export the correct numeric value
export STREAMLIT_SERVER_PORT=${PORT:-8501}

echo "STREAMLIT_SERVER_PORT (after fix): ${STREAMLIT_SERVER_PORT}"
echo "Python version: $(python --version)"
echo "Streamlit version: $(streamlit --version)"
echo "Starting Streamlit on 0.0.0.0:${STREAMLIT_SERVER_PORT}"

# Start Streamlit with explicit config
exec streamlit run app.py \
  --server.address=0.0.0.0 \
  --server.port=${STREAMLIT_SERVER_PORT} \
  --server.headless=true \
  --server.enableCORS=true \
  --server.enableXsrfProtection=false \
  --browser.gatherUsageStats=false
