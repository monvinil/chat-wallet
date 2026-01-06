#!/bin/sh
set -e

echo "=== Chat Wallet Startup ==="
echo "PORT (from Railway): ${PORT:-8501}"

# Don't use STREAMLIT_SERVER_PORT env var at all - pass directly as flag
# This avoids Railway's misconfigured env var entirely
ACTUAL_PORT=${PORT:-8501}

echo "Starting Streamlit on 0.0.0.0:${ACTUAL_PORT}"
echo "Python: $(python --version 2>&1)"

# Critical: Don't let Railway's broken STREAMLIT_SERVER_PORT interfere
# We use --server.port flag which takes precedence
exec env -u STREAMLIT_SERVER_PORT streamlit run app.py \
  --server.address=0.0.0.0 \
  --server.port=${ACTUAL_PORT} \
  --server.headless=true \
  --server.enableCORS=true \
  --server.enableXsrfProtection=false \
  --browser.gatherUsageStats=false
