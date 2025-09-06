"""
EverLiving Application Entry Point
Port: 8080

This is the main entry point that imports and runs the restructured application.
"""

import os
import sys

# Add src directory to Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

# Import the main application
from app_restructured import app

if __name__ == '__main__':
    # Get port from environment variable (Railway sets this)
    port = int(os.environ.get('PORT', 8081))
    
    # Detect if running in production (Railway) or development
    is_production = os.environ.get('RAILWAY_ENVIRONMENT') is not None
    
    if is_production:
        print("🚀 Starting EverLiving on Railway...")
        print(f"🌐 Running on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        print("🚀 Starting EverLiving Application...")
        print("📁 Project structure has been reorganized")
        print(f"🌐 Access your application at: http://localhost:{port}")
        app.run(host='0.0.0.0', port=port, debug=True)
