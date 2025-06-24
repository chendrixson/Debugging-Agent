"""Tool registry for managing debugging tools."""

from typing import Dict, List, Any, Optional

# Handle imports for both package and direct execution
try:
    from src.tools.base_tool import BaseTool
    from src.tools.attach_tool import LaunchApplicationTool, AttachToProcessTool
    from src.tools.stack_tool import AnalyzeCrashTool, GetStackTraceTool, GetCurrentFrameTool, WaitForEventTool
    from src.tools.execution_control_tool import ExecutionControlTool
    from src.tools.step_tool import StepTool
    from src.tools.breakpoint_tool import SetBreakpointTool, RemoveBreakpointTool
    from src.tools.variable_tool import GetVariablesTool
except ImportError:
    from tools.base_tool import BaseTool
    from tools.attach_tool import LaunchApplicationTool, AttachToProcessTool
    from tools.stack_tool import AnalyzeCrashTool, GetStackTraceTool, GetCurrentFrameTool, WaitForEventTool
    from tools.execution_control_tool import ExecutionControlTool
    from tools.step_tool import StepTool
    from tools.breakpoint_tool import SetBreakpointTool, RemoveBreakpointTool
    from tools.variable_tool import GetVariablesTool


class ToolRegistry:
    """Registry for debugging tools."""
    
    def __init__(self, debugger):
        self.debugger = debugger
        self.tools: Dict[str, BaseTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default debugging tools."""
        default_tools = [
            LaunchApplicationTool(self.debugger),
            AttachToProcessTool(self.debugger),
            AnalyzeCrashTool(self.debugger),
            GetStackTraceTool(self.debugger),
            GetCurrentFrameTool(self.debugger),
            WaitForEventTool(self.debugger),
            ExecutionControlTool(self.debugger),
            StepTool(self.debugger),
            SetBreakpointTool(self.debugger),
            RemoveBreakpointTool(self.debugger),
            GetVariablesTool(self.debugger)
        ]
        
        for tool in default_tools:
            self.register_tool(tool)
    
    def register_tool(self, tool: BaseTool):
        """Register a new tool."""
        self.tools[tool.name] = tool
    
    def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool by name."""
        if tool_name in self.tools:
            del self.tools[tool_name]
            return True
        return False
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self.tools.keys())
    
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool by name with given parameters."""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        return tool.execute(**kwargs)
    
    def get_openai_functions(self) -> List[Dict[str, Any]]:
        """Get all tools formatted as OpenAI function definitions."""
        return [tool.to_openai_function() for tool in self.tools.values()]
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all tools."""
        return {name: tool.description for name, tool in self.tools.items()} 