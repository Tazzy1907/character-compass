#!/usr/bin/env python3
"""
Startup script for Character Compass API server.
Runs the FastAPI application with uvicorn.
"""

import uvicorn
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    """Start the FastAPI server."""
    print("\n🚀 Starting Character Compass API Server...\n")
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",       # Listen on all network interfaces
        port=8000,             # Default port
        reload=True,           # Auto-reload on code changes (useful for development)
        log_level="info"       # Log level
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 API Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

