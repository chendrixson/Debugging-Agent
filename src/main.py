"""Main entry point for the Debug Agent application."""

import sys
import os
import argparse
from pathlib import Path

# Add src to path for imports and parent directory for package imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(parent_dir))

# Now we can import directly without relative imports
try:
    from src.ui.gradio_interface import DebugAgentInterface
    from src.utils.config import config
    from src.utils.exceptions import DebugAgentError
except ImportError:
    # Fallback for when running from different locations
    from ui.gradio_interface import DebugAgentInterface
    from utils.config import config
    from utils.exceptions import DebugAgentError


def check_prerequisites():
    """Check if required prerequisites are available."""
    errors = []
    
    # Check OpenAI API key
    if not config.openai_api_key:
        errors.append("OPENAI_API_KEY environment variable is required")
    
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

# Gradio UI Configuration
GRADIO_HOST=127.0.0.1
GRADIO_PORT=7860
GRADIO_SHARE=false

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
    parser = argparse.ArgumentParser(
        description="Debug Agent - AI-powered debugging assistant"
    )
    
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Create .env template file"
    )
    
    parser.add_argument(
        "--host",
        default=None,
        help="Host to bind to (overrides GRADIO_HOST)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind to (overrides GRADIO_PORT)"
    )
    
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create public Gradio link"
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
        
        print("🐛 Starting Debug Agent...")
        print(f"Platform: {sys.platform}")
        print(f"OpenAI Model: {config.openai_model}")
        
        # Override config with command line args
        if args.host:
            config.gradio_host = args.host
        if args.port:
            config.gradio_port = args.port
        if args.share:
            config.gradio_share = True
        
        # Create and launch the interface
        interface = DebugAgentInterface()
        
        print(f"🚀 Launching web interface at http://{config.gradio_host}:{config.gradio_port}")
        print("Press Ctrl+C to stop the server")
        
        interface.launch()
        
    except KeyboardInterrupt:
        print("\n👋 Debug Agent stopped by user")
    except DebugAgentError as e:
        print(f"❌ Debug Agent Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 