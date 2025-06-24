"""Factory for creating platform-specific debuggers."""

import sys
from typing import Optional

# Handle imports for both package and direct execution
try:
    from src.debugger.base import BaseDebugger
    from src.debugger.platform.windows import WindowsDebugger
    from src.utils.exceptions import DebuggerError
except ImportError:
    from debugger.base import BaseDebugger
    from debugger.platform.windows import WindowsDebugger
    from utils.exceptions import DebuggerError


class DebuggerFactory:
    """Factory for creating platform-specific debuggers."""
    
    @staticmethod
    def create_debugger() -> BaseDebugger:
        """Create a debugger instance for the current platform."""
        if sys.platform == "win32":
            return WindowsDebugger()
        else:
            raise DebuggerError(f"Unsupported platform: {sys.platform}") 