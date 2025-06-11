"""Base tool interface for OpenAI-compatible debugging tools."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel


class ToolResult(BaseModel):
    """Result of a tool execution."""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class BaseTool(ABC):
    """Abstract base class for debugging tools."""
    
    def __init__(self, debugger):
        self.debugger = debugger
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for OpenAI."""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """OpenAI function parameters schema."""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass
    
    def to_openai_function(self) -> Dict[str, Any]:
        """Convert tool to OpenAI function definition."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
    
    def validate_parameters(self, **kwargs) -> bool:
        """Validate tool parameters before execution."""
        # Basic validation - can be overridden in subclasses
        required_params = self.parameters.get("required", [])
        for param in required_params:
            if param not in kwargs:
                raise ValueError(f"Missing required parameter: {param}")
        return True 