#!/usr/bin/env python3
"""
AFL Manager Server Runner
"""

import os
import uvicorn

if __name__ == "__main__":
    # Auto-detect production vs development
    is_production = os.getenv("PORT") or os.getenv("RAILWAY_ENVIRONMENT")
    port = int(os.getenv("PORT", 8000))
    
    if is_production:
        print("🚀 Starting AFL Manager in production mode")
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=port,
            reload=False,  # No reload in production
            log_level="info"
        )
    else:
        print("🔧 Starting AFL Manager in development mode")
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0", 
            port=port,
            reload=True,
            log_level="info"
        )