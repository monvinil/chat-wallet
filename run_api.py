#!/usr/bin/env python3
"""
Run the USDChat API server.

Usage:
    python run_api.py                    # Production mode
    python run_api.py --debug            # Debug mode with auto-reload
    python run_api.py --port 8080        # Custom port
"""

import argparse
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(description="Run USDChat API server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")

    args = parser.parse_args()

    # Set debug mode in environment
    if args.debug:
        os.environ["DEBUG"] = "true"

    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=args.host,
        port=args.port,
        reload=args.debug,
        workers=args.workers if not args.debug else 1,
        log_level="debug" if args.debug else "info",
    )


if __name__ == "__main__":
    main()
