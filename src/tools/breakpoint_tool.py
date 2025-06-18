"""Tools for managing breakpoints."""

from typing import Dict, Any, Optional

# Handle imports for both package and direct execution
try:
    from src.tools.base_tool import BaseTool, ToolResult
    from src.debugger.base import DebuggerState
    from src.utils.exceptions import BreakpointError
except ImportError:
    from tools.base_tool import BaseTool, ToolResult
    from debugger.base import DebuggerState
    from utils.exceptions import BreakpointError


class SetBreakpointTool(BaseTool):
    """Tool to set a breakpoint at a specific location or function."""
    
    @property
    def name(self) -> str:
        return "set_breakpoint"
    
    @property
    def description(self) -> str:
        return "Set a breakpoint at a specific file and line number, or at a specific function in the debugged process"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the source file where to set the breakpoint (required for line breakpoints)"
                },
                "line_number": {
                    "type": "integer",
                    "description": "Line number in the file where to set the breakpoint (required for line breakpoints)"
                },
                "function_name": {
                    "type": "string",
                    "description": "Name of the function where to set the breakpoint (required for function breakpoints)"
                },
                "condition": {
                    "type": "string",
                    "description": "Optional condition that must be true for the breakpoint to trigger"
                }
            },
            "required": [],
            "oneOf": [
                {
                    "required": ["file_path", "line_number"]
                },
                {
                    "required": ["function_name"]
                }
            ]
        }
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute breakpoint setting."""
        try:
            self.validate_parameters(**kwargs)
            
            # Check if debugger is in a state where we can set breakpoints
            if not self.debugger.is_attached():
                return ToolResult(
                    success=False,
                    data=None,
                    error="Cannot set breakpoint - debugger is not attached to a process",
                    metadata={"action": "set_breakpoint", "state": self.debugger.get_state().value}
                )
            
            condition = kwargs.get("condition")
            
            # Handle function breakpoint
            if "function_name" in kwargs:
                function_name = kwargs["function_name"]
                bp_id = self.debugger.set_function_breakpoint(
                    function_name=function_name,
                    condition=condition
                )
                return ToolResult(
                    success=True,
                    data={
                        "breakpoint_id": bp_id,
                        "function_name": function_name,
                        "condition": condition
                    },
                    metadata={
                        "action": "set_breakpoint",
                        "type": "function",
                        "timestamp": self._get_timestamp()
                    }
                )
            
            # Handle line breakpoint
            file_path = kwargs["file_path"]
            line_number = kwargs["line_number"]
            
            bp_id = self.debugger.set_breakpoint(
                file_path=file_path,
                line_number=line_number,
                condition=condition
            )
            
            return ToolResult(
                success=True,
                data={
                    "breakpoint_id": bp_id,
                    "file_path": file_path,
                    "line_number": line_number,
                    "condition": condition
                },
                metadata={
                    "action": "set_breakpoint",
                    "type": "line",
                    "timestamp": self._get_timestamp()
                }
            )
            
        except BreakpointError as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to set breakpoint: {str(e)}",
                metadata={"action": "set_breakpoint"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error setting breakpoint: {str(e)}",
                metadata={"action": "set_breakpoint"}
            )
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string."""
        import datetime
        return datetime.datetime.now().isoformat()


class RemoveBreakpointTool(BaseTool):
    """Tool to remove a breakpoint."""
    
    @property
    def name(self) -> str:
        return "remove_breakpoint"
    
    @property
    def description(self) -> str:
        return "Remove a previously set breakpoint by its ID"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "breakpoint_id": {
                    "type": "integer",
                    "description": "ID of the breakpoint to remove"
                }
            },
            "required": ["breakpoint_id"]
        }
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute breakpoint removal."""
        try:
            self.validate_parameters(**kwargs)
            
            # Check if debugger is in a state where we can remove breakpoints
            if not self.debugger.is_attached():
                return ToolResult(
                    success=False,
                    data=None,
                    error="Cannot remove breakpoint - debugger is not attached to a process",
                    metadata={"action": "remove_breakpoint", "state": self.debugger.get_state().value}
                )
            
            breakpoint_id = kwargs["breakpoint_id"]
            
            # Remove the breakpoint
            success = self.debugger.remove_breakpoint(breakpoint_id)
            
            if success:
                return ToolResult(
                    success=True,
                    data={
                        "breakpoint_id": breakpoint_id,
                        "status": "removed"
                    },
                    metadata={
                        "action": "remove_breakpoint",
                        "timestamp": self._get_timestamp()
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Breakpoint {breakpoint_id} not found",
                    metadata={"action": "remove_breakpoint"}
                )
            
        except BreakpointError as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to remove breakpoint: {str(e)}",
                metadata={"action": "remove_breakpoint"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error removing breakpoint: {str(e)}",
                metadata={"action": "remove_breakpoint"}
            )
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string."""
        import datetime
        return datetime.datetime.now().isoformat() 