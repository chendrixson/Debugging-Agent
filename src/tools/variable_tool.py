"""Tool for inspecting variables in the debugged process."""

from typing import Dict, Any, Optional

# Handle imports for both package and direct execution
try:
    from src.tools.base_tool import BaseTool, ToolResult
    from src.debugger.base import DebuggerState
except ImportError:
    from tools.base_tool import BaseTool, ToolResult
    from debugger.base import DebuggerState


class GetVariablesTool(BaseTool):
    """Tool to get local variables in the current stack frame."""
    
    @property
    def name(self) -> str:
        return "get_variables"
    
    @property
    def description(self) -> str:
        return "Get local variables in the current stack frame of the debugged process"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "frame_index": {
                    "type": "integer",
                    "description": "Stack frame index to get variables from (0 is current frame)",
                    "default": 0
                },
                "expression": {
                    "type": "string",
                    "description": "Optional expression to evaluate in the frame context"
                }
            },
            "required": []
        }
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute variable inspection."""
        try:
            # Check if debugger is in a state where we can get variables
            state = self.debugger.get_state()
            if state not in [DebuggerState.PAUSED, DebuggerState.CRASHED]:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Cannot get variables - process is in state: {state.value}",
                    metadata={"action": "get_variables", "state": state.value}
                )
            
            frame_index = kwargs.get("frame_index", 0)
            expression = kwargs.get("expression")
            
            # Get variables
            variables = self.debugger.get_local_variables(frame_index)
            
            # If an expression was provided, evaluate it
            if expression:
                try:
                    result = self.debugger.evaluate_expression(expression, frame_index)
                    variables["_expression_result"] = result
                except Exception as e:
                    variables["_expression_error"] = str(e)
            
            return ToolResult(
                success=True,
                data={
                    "variables": variables,
                    "frame_index": frame_index,
                    "has_expression": expression is not None
                },
                metadata={
                    "action": "get_variables",
                    "timestamp": self._get_timestamp(),
                    "state": state.value
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error getting variables: {str(e)}",
                metadata={"action": "get_variables"}
            )
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string."""
        import datetime
        return datetime.datetime.now().isoformat() 