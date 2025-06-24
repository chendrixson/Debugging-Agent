#!/usr/bin/env python3
"""Flask-based Debug Agent runner script."""

import sys
import os
import argparse
from pathlib import Path
import logging

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run Flask backend
from backend.app import app, socketio, backend

def check_prerequisites():
    """Check if required prerequisites are available."""
    errors = []
    
    # Check OpenAI API key
    try:
        from src.utils.config import config
        if not config.openai_api_key:
            errors.append("OPENAI_API_KEY environment variable is required")
    except ImportError:
        errors.append("Could not import configuration")
    
    # Check platform support
    if sys.platform == "win32":
        try:
            import win32api
        except ImportError:
            errors.append("pywin32 package is required for Windows debugging")
    else:
        errors.append(f"Platform {sys.platform} is not supported yet (Windows only)")
    
    return errors

def create_env_template():
    """Create a .env template file."""
    env_template = """# Debug Agent Configuration

# OpenAI Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4-turbo-preview

# Flask Backend Configuration
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=true

# Debug Configuration
DEBUG_TIMEOUT=30
MAX_CRASH_ANALYSIS_DEPTH=10

# Windows Specific (Optional)
WINDOWS_DEBUGGER_PATH=
"""
    
    env_path = Path(".env")
    if not env_path.exists():
        with open(env_path, "w") as f:
            f.write(env_template)
        print(f"Created .env template file at {env_path.absolute()}")
        print("Please edit it with your OpenAI API key and other settings.")
        return True
    return False

def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
        stream=sys.stdout
    )
    parser = argparse.ArgumentParser(
        description="Flask-based Debug Agent - AI-powered debugging assistant"
    )
    
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Create .env template file"
    )
    
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to bind to (default: 5000)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    args = parser.parse_args()
    
    # Handle setup mode
    if args.setup:
        create_env_template()
        return
    
    try:
        # Check prerequisites
        errors = check_prerequisites()
        if errors:
            print("❌ Prerequisites check failed:")
            for error in errors:
                print(f"  • {error}")
            print("\nRun with --setup to create a .env template file.")
            sys.exit(1)
        
        print("🐛 Starting Flask-based Debug Agent...")
        print(f"Platform: {sys.platform}")
        print(f"Backend URL: http://{args.host}:{args.port}")
        print(f"Frontend URL: http://localhost:3000")
        print("Press Ctrl+C to stop the server")
        
        # Run the Flask app with SocketIO
        socketio.run(
            app, 
            host=args.host, 
            port=args.port, 
            debug=args.debug,
            allow_unsafe_werkzeug=True
        )
        
    except KeyboardInterrupt:
        print("\n👋 Debug Agent stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 