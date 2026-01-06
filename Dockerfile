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

# Patch Streamlit's loading animation with custom branded version
RUN python -c "
import streamlit
import os

# Find Streamlit's static directory
st_dir = os.path.dirname(streamlit.__file__)
static_dir = os.path.join(st_dir, 'static')
index_path = os.path.join(static_dir, 'index.html')

# Read the original index.html
with open(index_path, 'r') as f:
    content = f.read()

# Custom loading animation CSS
custom_css = '''
<style>
  /* Custom Chat Wallet loading screen */
  .stApp [data-testid=\"stAppViewContainer\"]::before {
    content: \"\";
    display: none;
  }

  /* Override Streamlit's default loader */
  .stApp > div:first-child > div:first-child {
    background: #0F0F14 !important;
  }

  /* Spinner wrapper */
  [data-testid=\"stSpinner\"] {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  /* Custom animated logo placeholder */
  .element-container:has([data-testid=\"stSpinner\"]) {
    min-height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
</style>

<style id=\"chat-wallet-loader\">
  /* Initial page load - before React mounts */
  body {
    background: #0F0F14 !important;
  }

  #root:empty::before {
    content: \"◈\";
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 64px;
    color: #3B82F6;
    animation: wallet-pulse 1.5s ease-in-out infinite;
    z-index: 9999;
  }

  #root:empty::after {
    content: \"Chat Wallet\";
    position: fixed;
    top: calc(50% + 60px);
    left: 50%;
    transform: translateX(-50%);
    font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
    font-size: 18px;
    font-weight: 500;
    color: #9CA3AF;
    letter-spacing: 0.05em;
    z-index: 9999;
  }

  @keyframes wallet-pulse {
    0%, 100% {
      opacity: 1;
      transform: translate(-50%, -50%) scale(1);
      filter: drop-shadow(0 0 20px rgba(59, 130, 246, 0.5));
    }
    50% {
      opacity: 0.7;
      transform: translate(-50%, -50%) scale(1.1);
      filter: drop-shadow(0 0 40px rgba(59, 130, 246, 0.8));
    }
  }

  /* Gradient ring animation */
  #root:empty {
    background:
      radial-gradient(circle at 50% 50%, rgba(59, 130, 246, 0.1) 0%, transparent 50%),
      #0F0F14;
  }
</style>
'''

# Inject custom CSS before </head>
if 'chat-wallet-loader' not in content:
    content = content.replace('</head>', custom_css + '</head>')

    with open(index_path, 'w') as f:
        f.write(content)
    print('✓ Streamlit loading screen customized')
else:
    print('✓ Custom loading screen already applied')
"

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run the app
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
