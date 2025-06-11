"""Configuration management for the debug agent."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration settings for the debug agent."""
    
    def __init__(self):
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        
        # Gradio settings
        self.gradio_host: str = os.getenv("GRADIO_HOST", "127.0.0.1")
        self.gradio_port: int = int(os.getenv("GRADIO_PORT", "7860"))
        self.gradio_share: bool = os.getenv("GRADIO_SHARE", "false").lower() == "true"
        
        # Debug settings
        self.debug_timeout: int = int(os.getenv("DEBUG_TIMEOUT", "30"))  # seconds
        self.max_crash_analysis_depth: int = int(os.getenv("MAX_CRASH_ANALYSIS_DEPTH", "10"))
        
        # Platform specific settings
        self.windows_debugger_path: Optional[str] = os.getenv("WINDOWS_DEBUGGER_PATH")
        
    def validate(self) -> bool:
        """Validate that required configuration is present."""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        return True


# Global config instance
config = Config() 