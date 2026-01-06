#!/usr/bin/env python3
"""Patch Streamlit's loading screen with custom branded animation"""

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
<style id="chat-wallet-loader">
  body { background: #0F0F14 !important; }

  #root:empty::before {
    content: "◈";
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
    content: "Chat Wallet";
    position: fixed;
    top: calc(50% + 60px);
    left: 50%;
    transform: translateX(-50%);
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 18px;
    font-weight: 500;
    color: #9CA3AF;
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
